"""
URL to Markdown Converter

Converts web pages to clean markdown format using content extraction
and HTML-to-markdown conversion.
"""

import requests
from urllib.parse import urlparse
from datetime import datetime
import logging
from typing import Dict, Optional, Tuple
import trafilatura
from readability import Document
from markdownify import markdownify as md
from lxml import html
import re
from extractor.url_utils import remove_utm_parameters

logger = logging.getLogger(__name__)


def extract_published_date_from_html(html_content: str) -> Optional[datetime]:
    """
    Extract published date from HTML meta tags.
    Checks common meta tag patterns for article publication dates.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        datetime object if found, None otherwise
    """
    try:
        from dateutil import parser as date_parser
        import json
        
        # Parse HTML
        doc = html.fromstring(html_content)
        
        # Common meta tag patterns for published dates
        meta_patterns = [
            ('property', 'article:published_time'),
            ('property', 'og:published_time'),
            ('property', 'article:published'),
            ('name', 'article:published_time'),
            ('name', 'date'),
            ('name', 'pubdate'),
            ('name', 'publishdate'),
            ('name', 'publication-date'),
            ('itemprop', 'datePublished'),
            ('itemprop', 'datepublished'),
        ]
        
        # Check meta tags
        for attr_name, attr_value in meta_patterns:
            meta_tags = doc.xpath(f'//meta[@{attr_name}="{attr_value}"]')
            for meta in meta_tags:
                content = meta.get('content', '').strip()
                if content:
                    try:
                        # Parse the date string
                        parsed_date = date_parser.parse(content)
                        return parsed_date
                    except (ValueError, TypeError):
                        continue
        
        # Check for JSON-LD structured data
        json_ld_scripts = doc.xpath('//script[@type="application/ld+json"]')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.text_content())
                # Handle both single objects and arrays
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            date_str = item.get('datePublished') or item.get('datepublished') or item.get('date')
                            if date_str:
                                parsed_date = date_parser.parse(date_str)
                                return parsed_date
                elif isinstance(data, dict):
                    date_str = data.get('datePublished') or data.get('datepublished') or data.get('date')
                    if date_str:
                        parsed_date = date_parser.parse(date_str)
                        return parsed_date
            except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
                continue
        
        # Check for time elements with datetime attribute
        time_elements = doc.xpath('//time[@datetime]')
        for time_elem in time_elements:
            datetime_attr = time_elem.get('datetime', '').strip()
            if datetime_attr:
                try:
                    parsed_date = date_parser.parse(datetime_attr)
                    return parsed_date
                except (ValueError, TypeError):
                    continue
        
    except Exception as e:
        logger.debug(f"Error extracting published date from HTML: {e}")
    
    return None


def escape_yaml_value(value: str) -> str:
    """
    Properly escape a YAML value, quoting if necessary.
    
    Args:
        value: String value to escape
        
    Returns:
        Properly escaped YAML value
    """
    if not value:
        return '""'
    
    value_str = str(value).strip()
    
    # If empty after strip, return empty quoted string
    if not value_str:
        return '""'
    
    # Check if value needs quoting
    needs_quotes = False
    
    # Check for special YAML characters
    if any(char in value_str for char in [':', '#', '|', '>', '&', '*', '!', '%', '@', '`', '[', ']', '{', '}', '\\']):
        needs_quotes = True
    
    # Check if it starts with special characters
    if value_str.startswith(('-', '?', ':', ',', '[', ']', '{', '}', '&', '*', '!', '%', '@', '`', '|', '>', "'", '"')):
        needs_quotes = True
    
    # Check if it looks like a number or boolean (YAML might interpret it)
    if value_str.lower() in ('true', 'false', 'null', 'yes', 'no', 'on', 'off'):
        needs_quotes = True
    
    # Check if it contains newlines
    if '\n' in value_str:
        needs_quotes = True
    
    # If quotes are needed, escape internal quotes and wrap
    if needs_quotes:
        # Escape backslashes first, then quotes
        escaped = value_str.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    
    return value_str


class URLToMarkdownConverter:
    """
    Convert URLs to markdown format by extracting clean content
    and converting HTML to markdown.
    """
    
    def __init__(self, timeout: int = 30, user_agent: Optional[str] = None):
        """
        Initialize the converter.
        
        Args:
            timeout: Request timeout in seconds
            user_agent: Custom user agent string (defaults to trafilatura's)
        """
        self.timeout = timeout
        # Default user agent - a modern browser string
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.google.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
    
    def fetch_url(self, url: str) -> Tuple[Optional[str], Optional[str], Dict]:
        """
        Fetch HTML content from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (html_content, final_url, metadata)
        """
        metadata = {
            'original_url': url,
            'final_url': url,
            'status_code': None,
            'error': None
        }
        
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                stream=True
            )
            
            metadata['status_code'] = response.status_code
            cleaned_final_url = remove_utm_parameters(response.url)
            metadata['final_url'] = cleaned_final_url
            
            if response.status_code != 200:
                metadata['error'] = f"HTTP {response.status_code}"
                return None, cleaned_final_url, metadata
            
            # Check content type
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                metadata['error'] = f"Not HTML content: {content_type}"
                return None, cleaned_final_url, metadata
            
            html_content = response.text
            return html_content, cleaned_final_url, metadata
            
        except requests.exceptions.Timeout:
            metadata['error'] = "Request timeout"
            return None, url, metadata
        except requests.exceptions.ConnectionError as e:
            metadata['error'] = f"Connection error: {str(e)}"
            return None, url, metadata
        except requests.exceptions.RequestException as e:
            metadata['error'] = f"Request error: {str(e)}"
            return None, url, metadata
        except Exception as e:
            metadata['error'] = f"Unexpected error: {str(e)}"
            logger.exception(f"Error fetching {url}")
            return None, url, metadata
    
    def extract_content(self, html_content: str, url: str, method: str = 'auto') -> Dict:
        """
        Extract clean content from HTML.
        
        Args:
            html_content: Raw HTML content
            url: Source URL (for resolving relative links)
            method: Extraction method ('trafilatura', 'readability', or 'auto')
            
        Returns:
            Dictionary with extracted content and metadata
        """
        result = {
            'title': None,
            'content': None,
            'excerpt': None,
            'author': None,
            'published_date': None,
            'method': method,
            'success': False
        }
        
        # Try trafilatura first (usually better)
        if method in ('auto', 'trafilatura'):
            try:
                extracted = trafilatura.extract(
                    html_content,
                    include_comments=False,
                    include_tables=True,
                    include_images=True,
                    include_links=True,
                    output_format='xml',  # Get structured XML
                    url=url
                )
                
                if extracted:
                    # Parse metadata
                    metadata = trafilatura.extract_metadata(html_content, url=url)
                    if metadata:
                        result['title'] = metadata.title
                        result['author'] = metadata.author
                        result['published_date'] = metadata.date
                    
                    # If trafilatura didn't find published_date, try extracting from HTML meta tags
                    if not result['published_date']:
                        result['published_date'] = extract_published_date_from_html(html_content)
                    
                    # Convert XML to HTML for markdown conversion
                    doc = html.fromstring(extracted)
                    html_content_clean = html.tostring(doc, encoding='unicode', pretty_print=True)
                    result['content'] = html_content_clean
                    result['method'] = 'trafilatura'
                    result['success'] = True
                    
                    # Generate excerpt from first paragraph
                    if result['content']:
                        paragraphs = doc.xpath('//p')
                        if paragraphs:
                            first_para = paragraphs[0].text_content().strip()
                            result['excerpt'] = first_para[:300] + ('...' if len(first_para) > 300 else '')
                    
                    return result
            except Exception as e:
                logger.debug(f"Trafilatura extraction failed: {e}")
                if method == 'trafilatura':
                    return result
        
        # Fallback to readability
        if method in ('auto', 'readability'):
            try:
                doc = Document(html_content)
                title = doc.title()
                
                # Get clean HTML
                clean_html = doc.summary()
                
                if clean_html:
                    result['title'] = title
                    result['content'] = clean_html
                    result['method'] = 'readability'
                    result['success'] = True
                    
                    # Try to extract published date from HTML meta tags
                    if not result['published_date']:
                        result['published_date'] = extract_published_date_from_html(html_content)
                    
                    # Generate excerpt
                    doc_tree = html.fromstring(clean_html)
                    paragraphs = doc_tree.xpath('//p')
                    if paragraphs:
                        first_para = paragraphs[0].text_content().strip()
                        result['excerpt'] = first_para[:300] + ('...' if len(first_para) > 300 else '')
                    
                    return result
            except Exception as e:
                logger.debug(f"Readability extraction failed: {e}")
                if method == 'readability':
                    return result
        
        # If both fail, return raw HTML (last resort)
        result['content'] = html_content
        result['method'] = 'raw'
        result['success'] = False
        return result
    
    def html_to_markdown(self, html_content: str, **kwargs) -> str:
        """
        Convert HTML to markdown.
        
        Args:
            html_content: HTML content to convert
            **kwargs: Additional options for markdownify
            
        Returns:
            Markdown string
        """
        # Configure markdownify options
        md_options = {
            'heading_style': 'ATX',  # Use # for headings
            'bullets': '-',  # Use - for lists
            'strip': ['script', 'style'],  # Remove script and style tags
            **kwargs
        }
        
        markdown = md(html_content, **md_options)
        
        # Clean up extra whitespace
        lines = markdown.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if not prev_empty:
                    cleaned_lines.append('')
                    prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False
        
        return '\n'.join(cleaned_lines).strip()
    
    def convert(self, url: str, extract_method: str = 'auto', include_metadata: bool = True, 
                additional_metadata: Optional[Dict] = None) -> Dict:
        """
        Convert a URL to markdown format.
        
        Args:
            url: URL to convert
            extract_method: Content extraction method ('auto', 'trafilatura', 'readability')
            include_metadata: Whether to include frontmatter metadata
            additional_metadata: Optional dict with additional metadata:
                - tags: List of tags
                - date_saved: Date when link was saved (datetime or string)
                - crawl_date: Date when link was last crawled (datetime or string)
                - domain: Domain of the link
                - pocket_status: Pocket status ('unread' or 'archive')
                - description: Description/excerpt
            
        Returns:
            Dictionary with markdown content and metadata
        """
        result = {
            'url': url,
            'final_url': url,
            'markdown': None,
            'title': None,
            'excerpt': None,
            'author': None,
            'published_date': None,
            'extraction_method': None,
            'success': False,
            'error': None,
            'metadata': {}
        }
        
        additional_metadata = additional_metadata or {}
        
        # Fetch HTML
        html_content, final_url, fetch_metadata = self.fetch_url(url)
        result['final_url'] = final_url
        result['metadata'].update(fetch_metadata)
        
        if not html_content:
            result['error'] = fetch_metadata.get('error', 'Failed to fetch URL')
            return result
        
        # Extract clean content
        extracted = self.extract_content(html_content, final_url, method=extract_method)
        
        if not extracted['success'] or not extracted['content']:
            result['error'] = 'Failed to extract content'
            return result
        
        # Convert to markdown
        markdown_content = self.html_to_markdown(extracted['content'])
        
        if not markdown_content:
            result['error'] = 'Failed to convert to markdown'
            return result
        
        # Build final markdown with optional frontmatter
        if include_metadata:
            frontmatter_lines = ['---']
            
            # Title (prefer extracted, fallback to additional metadata)
            title = extracted['title'] or additional_metadata.get('title') or ''
            if title:
                title_escaped = escape_yaml_value(title)
                frontmatter_lines.append(f"title: {title_escaped}")
                result['title'] = title
            else:
                frontmatter_lines.append("title:")
            
            # Source URL (always quote URLs as they contain special characters)
            source_escaped = escape_yaml_value(final_url)
            frontmatter_lines.append(f"source: {source_escaped}")
            
            # Author
            author = extracted.get('author') or additional_metadata.get('author')
            if author:
                author_escaped = escape_yaml_value(author)
                frontmatter_lines.append(f"author: {author_escaped}")
                result['author'] = author
            else:
                frontmatter_lines.append("author:")
            
            # Published date (original article publication date) - YYYY-MM-DD format
            published_date = extracted.get('published_date') or additional_metadata.get('published_date')
            if published_date:
                if hasattr(published_date, 'date'):
                    published_str = published_date.date().isoformat()
                elif hasattr(published_date, 'isoformat'):
                    published_str = published_date.isoformat()[:10]
                else:
                    published_str = str(published_date)[:10]
                frontmatter_lines.append(f"published: {published_str}")
                result['published_date'] = published_date
            else:
                frontmatter_lines.append("published:")
            
            # Created date (when markdown file is created - today/now) - YYYY-MM-DD format
            created_date = datetime.utcnow()
            created_str = created_date.date().isoformat()
            frontmatter_lines.append(f"created: {created_str}")
            
            # Description (excerpt) - clean and escape
            description = extracted.get('excerpt') or additional_metadata.get('description') or additional_metadata.get('excerpt')
            if description:
                # Clean description: remove newlines, trim whitespace
                description_clean = ' '.join(description.split())
                description_escaped = escape_yaml_value(description_clean)
                frontmatter_lines.append(f"description: {description_escaped}")
                result['excerpt'] = description
            else:
                frontmatter_lines.append("description:")
            
            # Tags (from Pocket) - always use list format
            tags = additional_metadata.get('tags', [])
            frontmatter_lines.append("tags:")
            if tags:
                for tag in tags:
                    if tag:  # Skip empty tags
                        tag_str = str(tag).strip()
                        if tag_str:  # Double check after strip
                            tag_escaped = escape_yaml_value(tag_str)
                            frontmatter_lines.append(f"  - {tag_escaped}")
            else:
                # Add default 'clippings' tag if no tags
                frontmatter_lines.append("  - clippings")
            
            # Additional metadata (optional fields)
            if additional_metadata.get('crawl_date'):
                crawl_date = additional_metadata['crawl_date']
                if hasattr(crawl_date, 'date'):
                    crawl_str = crawl_date.date().isoformat()
                elif hasattr(crawl_date, 'isoformat'):
                    crawl_str = crawl_date.isoformat()[:10]
                else:
                    crawl_str = str(crawl_date)[:10]
                frontmatter_lines.append(f"last_crawled: {crawl_str}")
            
            if additional_metadata.get('domain'):
                domain_escaped = escape_yaml_value(additional_metadata['domain'])
                frontmatter_lines.append(f"domain: {domain_escaped}")
            
            if additional_metadata.get('pocket_status'):
                status_escaped = escape_yaml_value(additional_metadata['pocket_status'])
                frontmatter_lines.append(f"pocket_status: {status_escaped}")
            
            frontmatter_lines.append('---')
            frontmatter_lines.append('')
            
            markdown_content = '\n'.join(frontmatter_lines) + markdown_content
        
        result['markdown'] = markdown_content
        result['title'] = extracted['title']
        result['excerpt'] = extracted['excerpt']
        result['author'] = extracted['author']
        result['published_date'] = extracted['published_date']
        result['extraction_method'] = extracted['method']
        result['success'] = True
        
        return result
    
    def convert_to_file(self, url: str, output_path: str, extract_method: str = 'auto', 
                       include_metadata: bool = True, additional_metadata: Optional[Dict] = None) -> Dict:
        """
        Convert URL to markdown and save to file.
        
        Args:
            url: URL to convert
            output_path: Path to save markdown file
            extract_method: Content extraction method
            include_metadata: Whether to include frontmatter metadata
            additional_metadata: Optional dict with additional metadata (tags, dates, etc.)
            
        Returns:
            Dictionary with conversion result and file path
        """
        result = self.convert(url, extract_method, include_metadata, additional_metadata)
        
        if result['success']:
            try:
                from pathlib import Path
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(result['markdown'], encoding='utf-8')
                result['file_path'] = str(output_file)
            except Exception as e:
                result['error'] = f"Failed to save file: {str(e)}"
                result['success'] = False
        
        return result
