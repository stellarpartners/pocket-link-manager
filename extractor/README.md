# Extractor Module

Content extraction and URL processing utilities for converting web pages to markdown.

## Overview

This module provides functionality to extract clean content from web pages and convert them to markdown format suitable for Obsidian or other knowledge management systems.

## Components

### URL to Markdown (`url_to_markdown.py`)

**URLToMarkdownConverter** class:

- Converts web pages to clean markdown
- Supports multiple extraction methods (trafilatura, readability, auto)
- Extracts metadata (title, author, published date, excerpt)
- Handles redirects and follows final URLs
- Removes UTM parameters and cleans URLs

**Key Methods:**

- `convert(url, extract_method='auto', include_metadata=True)` - Main conversion method
- `extract_published_date_from_html(html_content)` - Extract publication dates from HTML

### URL Utilities (`url_utils.py`)

URL processing functions:

- **remove_utm_parameters(url)** - Remove UTM tracking parameters from URLs
- URL normalization and cleaning utilities

## Usage

```python
from extractor.url_to_markdown import URLToMarkdownConverter

converter = URLToMarkdownConverter()
result = converter.convert(
    "https://example.com/article",
    extract_method='auto',
    include_metadata=True
)

if result['success']:
    print(result['markdown'])
    print(f"Title: {result['title']}")
    print(f"Author: {result['author']}")
```

## Extraction Methods

- **auto** - Automatically selects best method (default)
- **trafilatura** - Uses trafilatura library (good for articles)
- **readability** - Uses readability-lxml (good for general content)

## Dependencies

- `trafilatura` - Content extraction
- `readability-lxml` - HTML readability
- `markdownify` - HTML to markdown conversion
- `requests` - HTTP requests
