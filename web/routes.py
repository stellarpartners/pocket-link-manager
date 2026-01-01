"""
Flask routes for web interface
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, send_file
from database.queries import LinkQuery, StatisticsQuery, paginate_query
from database.models import create_session, Link, CrawlResult, QualityMetric, ContentExtraction, MarkdownFile
from sqlalchemy import desc, asc, func, or_
from datetime import datetime
from pathlib import Path
import logging
from extractor.url_utils import remove_utm_parameters

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)


@main_bp.route('/')
def index():
    """Dashboard homepage"""
    session = create_session()
    try:
        stats_query = StatisticsQuery(session)
        dashboard_stats = stats_query.get_dashboard_stats()
        return render_template('index.html', stats=dashboard_stats)
    finally:
        session.close()


@main_bp.route('/links')
def links():
    """Links listing page"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status_code = request.args.get('status_code', type=int)
    domain = request.args.get('domain', type=str)
    pocket_status = request.args.get('pocket_status', type=str)
    quality_min = request.args.get('quality_min', type=int)
    quality_max = request.args.get('quality_max', type=int)
    search = request.args.get('search', type=str)
    tag = request.args.get('tag', type=str)
    sort_by = request.args.get('sort_by', 'date_saved', type=str)
    sort_order = request.args.get('sort_order', 'desc', type=str)
    
    session = create_session()
    try:
        query = session.query(Link)
        
        # Track if we need joins
        needs_crawl_join = False
        needs_quality_join = False
        
        # Apply filters
        if status_code:
            needs_crawl_join = True
            query = query.join(CrawlResult).filter(CrawlResult.status_code == status_code)
        
        if domain:
            # Filter by domain - Link.domain should be synced with final URL when updated
            # Also check final_url domain for links that haven't been synced yet
            needs_crawl_join = True
            query = query.outerjoin(CrawlResult)
            # Filter by Link.domain (should be synced) or check final_url contains the domain
            query = query.filter(
                or_(
                    Link.domain == domain,
                    func.lower(CrawlResult.final_url).like(f"%//{domain.lower()}%")
                )
            ).distinct()
        
        if pocket_status:
            query = query.filter(Link.pocket_status == pocket_status)
        
        if tag and tag.strip():
            # Filter by tag - tags are stored as JSON array, so we search for the tag in the JSON string
            # We need to match the tag as a JSON string element, accounting for quotes
            tag_value = tag.strip()
            # Match: "tag" or 'tag' within the JSON array
            tag_patterns = [
                f'"{tag_value}"',  # JSON double quotes
                f"'{tag_value}'",   # Single quotes (for Python list syntax)
            ]
            # Use OR to match either pattern
            tag_filters = [Link.tags.contains(pattern) for pattern in tag_patterns]
            query = query.filter(or_(*tag_filters))
        
        if quality_min is not None or quality_max is not None:
            needs_quality_join = True
            query = query.join(QualityMetric)
            if quality_min is not None:
                query = query.filter(QualityMetric.quality_score >= quality_min)
            if quality_max is not None:
                query = query.filter(QualityMetric.quality_score <= quality_max)
        
        if search and search.strip():
            # SQLite LIKE is case-insensitive by default, but we'll use lower() for explicit case-insensitive search
            # Prioritize final URL over original URL - work with final URLs
            search_lower = search.strip().lower()
            needs_crawl_join = True
            
            # Search in title, final URL (prioritized), domain, and original URL (fallback)
            # Use outer join to include links without crawl results
            if not needs_crawl_join:
                query = query.outerjoin(CrawlResult)
            else:
                # If we already have a join, make sure it's outer join for search
                query = query.outerjoin(CrawlResult)
            
            search_filters = [
                func.lower(Link.title).like(f"%{search_lower}%"),
                func.lower(CrawlResult.final_url).like(f"%{search_lower}%"),  # Prioritize final URL
                func.lower(Link.domain).like(f"%{search_lower}%"),
                func.lower(Link.original_url).like(f"%{search_lower}%")  # Fallback to original
            ]
            query = query.filter(or_(*search_filters)).distinct()
        
        # Apply sorting
        if sort_by == 'date_saved':
            order_func = desc if sort_order == 'desc' else asc
            query = query.order_by(order_func(Link.date_saved))
        elif sort_by == 'quality_score':
            query = query.join(QualityMetric)
            order_func = desc if sort_order == 'desc' else asc
            query = query.order_by(order_func(QualityMetric.quality_score))
        elif sort_by == 'domain':
            order_func = desc if sort_order == 'desc' else asc
            query = query.order_by(order_func(Link.domain))
        
        # Paginate
        paginated = paginate_query(query, page, per_page)
        
        # Get domains for filter dropdown
        stats_query = StatisticsQuery(session)
        domain_stats = stats_query.get_domain_stats(limit=100)
        
        # Build filters dict, excluding None and empty values
        filters = {}
        if status_code is not None:
            filters['status_code'] = status_code
        if domain and domain.strip():
            filters['domain'] = domain
        if pocket_status and pocket_status.strip():
            filters['pocket_status'] = pocket_status
        if quality_min is not None:
            filters['quality_min'] = quality_min
        if quality_max is not None:
            filters['quality_max'] = quality_max
        if search and search.strip():
            filters['search'] = search.strip()
        if tag and tag.strip():
            filters['tag'] = tag.strip()
        if sort_by and sort_by.strip():
            filters['sort_by'] = sort_by
        if sort_order and sort_order.strip():
            filters['sort_order'] = sort_order
        
        return render_template('links.html', 
                             links=paginated['items'],
                             pagination=paginated,
                             filters=filters,
                             domain_stats=domain_stats,
                             current_tag=tag)
    finally:
        session.close()


@main_bp.route('/links/<int:link_id>')
def link_detail(link_id):
    """Individual link detail page"""
    session = create_session()
    try:
        link_query = LinkQuery(session)
        link = link_query.get_by_id(link_id)
        
        if not link:
            return "Link not found", 404
        
        crawl_result = link.latest_crawl()
        content_extraction = link.latest_content()
        quality_metric = link.quality_metric
        
        # Get all tags for autocomplete
        stats_query = StatisticsQuery(session)
        all_tags = [t['tag'] for t in stats_query.get_all_tags()]
        
        return render_template('link_detail.html',
                             link=link,
                             crawl_result=crawl_result,
                             content_extraction=content_extraction,
                             quality_metric=quality_metric,
                             all_tags=all_tags)
    finally:
        session.close()


@main_bp.route('/quality')
def quality():
    """Quality analysis dashboard"""
    session = create_session()
    try:
        stats_query = StatisticsQuery(session)
        dashboard_stats = stats_query.get_dashboard_stats()
        return render_template('quality.html', stats=dashboard_stats)
    finally:
        session.close()


@main_bp.route('/export')
def export():
    """Obsidian export interface"""
    session = create_session()
    try:
        stats_query = StatisticsQuery(session)
        stats = stats_query.get_dashboard_stats()
        return render_template('export.html', stats=stats)
    finally:
        session.close()


# API Routes

@api_bp.route('/stats')
def api_stats():
    """Get dashboard statistics"""
    stats_query = StatisticsQuery()
    stats = stats_query.get_dashboard_stats()
    
    return jsonify(stats)


@api_bp.route('/links')
def api_links():
    """API endpoint for links with filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status_code = request.args.get('status_code', type=int)
    domain = request.args.get('domain', type=str)
    
    link_query = LinkQuery()
    query = link_query.session.query(Link)
    
    if status_code:
        query = query.join(CrawlResult).filter(CrawlResult.status_code == status_code)
    if domain:
        query = query.filter(Link.domain == domain)
    
    paginated = paginate_query(query, page, per_page)
    
    # Serialize links
    links_data = []
    for link in paginated['items']:
        crawl = link.latest_crawl()
        quality = link.quality_metric
        
        links_data.append({
            'id': link.id,
            'title': link.title,
            'url': link.original_url,
            'domain': link.domain,
            'pocket_status': link.pocket_status,
            'date_saved': link.date_saved.isoformat() if link.date_saved else None,
            'status_code': crawl.status_code if crawl else None,
            'quality_score': quality.quality_score if quality else None,
            'is_accessible': quality.is_accessible if quality else False
        })
    
    return jsonify({
        'links': links_data,
        'pagination': {
            'page': paginated['page'],
            'per_page': paginated['per_page'],
            'total': paginated['total'],
            'pages': paginated['pages']
        }
    })


@api_bp.route('/links/<int:link_id>')
def api_link_detail(link_id):
    """API endpoint for individual link"""
    session = create_session()
    try:
        link_query = LinkQuery(session)
        link = link_query.get_by_id(link_id)
        
        if not link:
            return jsonify({'error': 'Not found'}), 404
        
        crawl = link.latest_crawl()
        content = link.latest_content()
        quality = link.quality_metric
        
        return jsonify({
            'id': link.id,
            'title': link.title,
            'url': link.original_url,
            'domain': link.domain,
            'pocket_status': link.pocket_status,
            'date_saved': link.date_saved.isoformat() if link.date_saved else None,
            'tags': link.get_tags_list(),
            'highlights': link.get_highlights_list(),
            'crawl': {
                'final_url': crawl.final_url if crawl else None,
                'status_code': crawl.status_code if crawl else None,
                'redirect_count': crawl.redirect_count if crawl else None,
                'response_time': crawl.response_time if crawl else None,
                'error_type': crawl.error_type if crawl else None,
                'crawl_date': crawl.crawl_date.isoformat() if crawl and crawl.crawl_date else None
            } if crawl else None,
            'content': {
                'title': content.title if content else None,
                'excerpt': content.excerpt if content else None,
                'author': content.author if content else None,
                'success': content.success if content else None,
                'extraction_date': content.extraction_date.isoformat() if content and content.extraction_date else None
            } if content else None,
            'quality': {
                'score': quality.quality_score if quality else None,
                'is_accessible': quality.is_accessible if quality else False,
                'has_content': quality.has_content if quality else False,
            'has_markdown': quality.has_markdown if quality else False
        } if quality else None
    })
    finally:
        session.close()


@main_bp.route('/links/<int:link_id>/archive', methods=['POST'])
def archive_link(link_id):
    """Archive or unarchive a link"""
    session = create_session()
    try:
        link = session.query(Link).filter_by(id=link_id).first()
        
        if not link:
            flash('Link not found', 'error')
            return redirect(url_for('main.links'))
        
        # Toggle archive status
        if link.pocket_status == 'archive':
            link.pocket_status = 'unread'
            message = 'Link unarchived successfully'
        else:
            link.pocket_status = 'archive'
            message = 'Link archived successfully'
        
        session.commit()
        flash(message, 'success')
        
        # Redirect back to where we came from
        referrer = request.referrer or url_for('main.links')
        return redirect(referrer)
        
    except Exception as e:
        session.rollback()
        flash(f'Error archiving link: {str(e)}', 'error')
        return redirect(url_for('main.links'))
    finally:
        session.close()


@main_bp.route('/links/<int:link_id>/delete', methods=['POST'])
def delete_link(link_id):
    """Delete a link"""
    # ... existing implementation ...
    session = create_session()
    try:
        link = session.query(Link).filter_by(id=link_id).first()
        
        if not link:
            flash('Link not found', 'error')
            return redirect(url_for('main.links'))
        
        title = link.title[:50] if link.title else 'Link'
        session.delete(link)  # Cascade will delete related records
        session.commit()
        
        flash(f'Link "{title}..." deleted successfully', 'success')
        return redirect(url_for('main.links'))
        
    except Exception as e:
        session.rollback()
        flash(f'Error deleting link: {str(e)}', 'error')
        return redirect(url_for('main.links'))
    finally:
        session.close()


@main_bp.route('/links/<int:link_id>/add-tag', methods=['POST'])
def add_tag(link_id):
    """Add a tag to a link"""
    session = create_session()
    try:
        link = session.query(Link).filter_by(id=link_id).first()
        if not link:
            flash('Link not found', 'error')
            return redirect(url_for('main.links'))
        
        tag_name = request.form.get('tag_name', '').strip()
        if not tag_name:
            flash('Tag name cannot be empty', 'warning')
            return redirect(url_for('main.link_detail', link_id=link_id))
        
        current_tags = link.get_tags_list()
        if tag_name not in current_tags:
            current_tags.append(tag_name)
            link.set_tags_list(current_tags)
            session.commit()
            flash(f'Tag "{tag_name}" added', 'success')
        else:
            flash(f'Tag "{tag_name}" already exists', 'info')
            
        return redirect(url_for('main.link_detail', link_id=link_id))
    except Exception as e:
        session.rollback()
        flash(f'Error adding tag: {str(e)}', 'error')
        return redirect(url_for('main.link_detail', link_id=link_id))
    finally:
        session.close()


@main_bp.route('/links/<int:link_id>/remove-tag', methods=['POST'])
def remove_tag(link_id):
    """Remove a tag from a link"""
    session = create_session()
    try:
        link = session.query(Link).filter_by(id=link_id).first()
        if not link:
            flash('Link not found', 'error')
            return redirect(url_for('main.links'))
        
        tag_name = request.form.get('tag_name', '').strip()
        if not tag_name:
            flash('No tag specified', 'warning')
            return redirect(url_for('main.link_detail', link_id=link_id))
        
        current_tags = link.get_tags_list()
        if tag_name in current_tags:
            current_tags.remove(tag_name)
            link.set_tags_list(current_tags)
            session.commit()
            flash(f'Tag "{tag_name}" removed', 'success')
            
        return redirect(url_for('main.link_detail', link_id=link_id))
    except Exception as e:
        session.rollback()
        flash(f'Error removing tag: {str(e)}', 'error')
        return redirect(url_for('main.link_detail', link_id=link_id))
    finally:
        session.close()


@main_bp.route('/links/<int:link_id>/update-final-url', methods=['POST'])
def update_final_url(link_id):
    """Update the final URL for a link's crawl result and update domain if changed"""
    session = create_session()
    try:
        link = session.query(Link).filter_by(id=link_id).first()
        
        if not link:
            flash('Link not found', 'error')
            return redirect(url_for('main.links'))
        
        final_url = request.form.get('final_url', '').strip()
        
        if not final_url:
            flash('Final URL cannot be empty', 'error')
            return redirect(url_for('main.link_detail', link_id=link_id))
        
        # Validate URL format
        if not (final_url.startswith('http://') or final_url.startswith('https://')):
            flash('URL must start with http:// or https://', 'error')
            return redirect(url_for('main.link_detail', link_id=link_id))
        
        # Remove UTM parameters from final URL
        final_url = remove_utm_parameters(final_url)
        
        # Extract domain from final URL
        from urllib.parse import urlparse
        parsed_url = urlparse(final_url)
        new_domain = parsed_url.netloc
        
        # Update domain if it's different from the original
        if new_domain and new_domain != link.domain:
            old_domain = link.domain
            link.domain = new_domain
            domain_updated = True
        else:
            domain_updated = False
        
        # Get or create crawl result
        crawl_result = link.latest_crawl()
        
        if not crawl_result:
            # Create a new crawl result if none exists
            crawl_result = CrawlResult(
                link_id=link.id,
                final_url=final_url,
                status_code=200,  # Assume success if manually set
                crawl_date=datetime.utcnow()
            )
            session.add(crawl_result)
        else:
            # Update existing crawl result
            crawl_result.final_url = final_url
            crawl_result.crawl_date = datetime.utcnow()
        
        session.commit()
        
        # Success message
        if domain_updated:
            flash(f'Final URL and domain updated successfully (domain changed from {old_domain} to {new_domain})', 'success')
        else:
            flash('Final URL updated successfully', 'success')
        
        return redirect(url_for('main.link_detail', link_id=link_id))
        
    except Exception as e:
        session.rollback()
        flash(f'Error updating final URL: {str(e)}', 'error')
        return redirect(url_for('main.link_detail', link_id=link_id))
    finally:
        session.close()


@main_bp.route('/links/<int:link_id>/update-metadata', methods=['POST'])
def update_metadata(link_id):
    """Update link metadata (title, author, excerpt)"""
    session = create_session()
    try:
        link = session.query(Link).filter_by(id=link_id).first()
        
        if not link:
            flash('Link not found', 'error')
            return redirect(url_for('main.links'))
        
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        
        if title:
            link.title = title
            
        # Update or create content extraction for author and excerpt
        content_extraction = link.latest_content()
        
        if author or excerpt:
            if not content_extraction:
                content_extraction = ContentExtraction(
                    link_id=link.id,
                    extraction_method='manual',
                    extraction_date=datetime.utcnow(),
                    success=True
                )
                session.add(content_extraction)
            
            if author:
                content_extraction.author = author
            if excerpt:
                content_extraction.excerpt = excerpt
            
            content_extraction.extraction_method = 'manual'
            content_extraction.extraction_date = datetime.utcnow()
            
        session.commit()
        flash('Link metadata updated successfully', 'success')
        
        return redirect(url_for('main.link_detail', link_id=link_id))
        
    except Exception as e:
        session.rollback()
        flash(f'Error updating metadata: {str(e)}', 'error')
        return redirect(url_for('main.link_detail', link_id=link_id))
    finally:
        session.close()


@main_bp.route('/links/<int:link_id>/refresh', methods=['POST'])
def refresh_metadata(link_id):
    """Re-crawl the URL and refresh metadata in the database"""
    session = create_session()
    try:
        link = session.query(Link).filter_by(id=link_id).first()
        if not link:
            return jsonify({'success': False, 'error': 'Link not found'}), 404
        
        # Prefer final URL if available, otherwise original
        url = link.original_url
        crawl_result = link.latest_crawl()
        if crawl_result and crawl_result.final_url:
            url = crawl_result.final_url
            
        from extractor.url_to_markdown import URLToMarkdownConverter
        converter = URLToMarkdownConverter()
        
        # Fetch and extract metadata (don't need full markdown sync here)
        result = converter.convert(url, extract_method='auto', include_metadata=False)
        
        if not result['success']:
            # Even if extraction fails, the crawl might have updated the final URL or status
            if result['metadata'].get('status_code'):
                if not crawl_result:
                    crawl_result = CrawlResult(link_id=link.id)
                    session.add(crawl_result)
                crawl_result.status_code = result['metadata']['status_code']
                crawl_result.final_url = remove_utm_parameters(result['final_url'])
                crawl_result.crawl_date = datetime.utcnow()
                session.commit()
            
            error_msg = result.get('error', 'Crawl failed')
            return jsonify({'success': False, 'error': f'Refresh failed: {error_msg}'}), 500
             
        # Update Link title if found
        if result['title']:
            link.title = result['title']
            
        # Update CrawlResult
        if not crawl_result:
            crawl_result = CrawlResult(link_id=link.id)
            session.add(crawl_result)
        
        crawl_result.final_url = remove_utm_parameters(result['final_url'])
        crawl_result.status_code = result['metadata'].get('status_code', 200)
        crawl_result.crawl_date = datetime.utcnow()
        
        # Update ContentExtraction
        extraction = link.latest_content()
        if not extraction:
            extraction = ContentExtraction(link_id=link.id)
            session.add(extraction)
            
        extraction.title = result['title']
        extraction.author = result['author']
        extraction.excerpt = result['excerpt']
        extraction.published_date = result['published_date']
        extraction.extraction_method = result['extraction_method']
        extraction.extraction_date = datetime.utcnow()
        extraction.success = True
        
        # Update QualityMetric
        from database.importer import calculate_quality_score
        quality = link.quality_metric
        if not quality:
            quality = QualityMetric(link_id=link.id)
            session.add(quality)
            
        quality.is_accessible = (crawl_result.status_code == 200)
        quality.has_content = True
        quality.quality_score = calculate_quality_score(
            crawl_result.status_code,
            crawl_result.redirect_count or 0,
            True, # has_content
            quality.has_markdown
        )
        quality.last_updated = datetime.utcnow()
        
        session.commit()
        return jsonify({
            'success': True, 
            'message': 'Metadata refreshed successfully from live URL',
            'title': result['title'],
            'author': result['author']
        })
    except Exception as e:
        session.rollback()
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500
    finally:
        session.close()


@main_bp.route('/tags')
def tags():
    """Tags listing page showing all tags with link counts"""
    session = create_session()
    try:
        stats_query = StatisticsQuery(session)
        all_tags = stats_query.get_all_tags()
        
        return render_template('tags.html', tags=all_tags)
    finally:
        session.close()


@main_bp.route('/links/<int:link_id>/convert-to-markdown', methods=['POST'])
def convert_link_to_markdown(link_id):
    """Convert a link to markdown and save to Obsidian vault folder"""
    session = create_session()
    try:
        link = session.query(Link).filter_by(id=link_id).first()
        
        if not link:
            return jsonify({'error': 'Link not found'}), 404
        
        # Get URL to convert (prefer final_url from crawl_result, fallback to original_url)
        url_to_convert = link.original_url
        crawl_result = link.latest_crawl()
        if crawl_result and crawl_result.final_url:
            url_to_convert = crawl_result.final_url
        
        # Convert to markdown
        from extractor.url_to_markdown import URLToMarkdownConverter
        from pathlib import Path
        import re
        import json
        
        # Prepare additional metadata from link
        additional_metadata = {
            'title': link.title,  # Use Pocket title as fallback
            'tags': link.get_tags_list(),  # Get tags from link
            'date_saved': link.date_saved,  # Date when saved to Pocket
            'domain': link.domain,
            'pocket_status': link.pocket_status,
        }
        
        # Preserve existing published_date if available (in case new extraction doesn't find it)
        existing_content = link.latest_content()
        if existing_content and existing_content.published_date:
            additional_metadata['published_date'] = existing_content.published_date
        
        # Add crawl date if available
        if crawl_result and crawl_result.crawl_date:
            additional_metadata['crawl_date'] = crawl_result.crawl_date
        
        converter = URLToMarkdownConverter()
        result = converter.convert(
            url_to_convert, 
            extract_method='auto', 
            include_metadata=True,
            additional_metadata=additional_metadata
        )
        
        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Conversion failed')
            }), 500
        
        # Create markdownloads folder in Obsidian vault
        markdownloads_dir = Path(r"C:\Users\spytz\OneDrive\Spyros's Vault\Spyros's Vault\Pocket Vault")
        markdownloads_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if markdown file already exists for this link
        existing_md_file = session.query(MarkdownFile).filter_by(link_id=link.id).first()
        if existing_md_file and existing_md_file.file_path:
            # Use existing file path - update the file in place
            file_path = Path(existing_md_file.file_path)
            # Ensure the file path is absolute (handle both relative and absolute paths)
            if not file_path.is_absolute():
                file_path = markdownloads_dir / file_path.name
        else:
            # Generate new filename from title or URL
            if result['title']:
                # Clean title for filename
                safe_title = re.sub(r'[^\w\s-]', '', result['title'])[:100]
                safe_title = re.sub(r'[-\s]+', '-', safe_title)
                filename = f"{link_id}_{safe_title}.md"
            else:
                # Fallback to URL-based filename
                from urllib.parse import urlparse
                parsed = urlparse(url_to_convert)
                domain = parsed.netloc.replace('.', '_')
                filename = f"{link_id}_{domain}.md"
            
            file_path = markdownloads_dir / filename
            
            # Only ensure unique filename if file doesn't exist yet (for new files)
            counter = 1
            while file_path.exists():
                name_part = file_path.stem
                file_path = markdownloads_dir / f"{name_part}_{counter}.md"
                counter += 1
        
        # Save markdown file
        file_path.write_text(result['markdown'], encoding='utf-8')
        # Store absolute path for reference
        relative_path = str(file_path)
        
        # Update or create ContentExtraction
        content_extraction = link.latest_content()
        if not content_extraction:
            content_extraction = ContentExtraction(
                link_id=link.id,
                extraction_method=result['extraction_method'],
                title=result['title'],
                content=result.get('markdown', ''),  # Store markdown as content
                excerpt=result.get('excerpt'),
                author=result.get('author'),
                published_date=result.get('published_date'),
                success=True,
                markdown_content=result['markdown'],
                markdown_file_path=relative_path
            )
            session.add(content_extraction)
        else:
            # Update existing extraction
            content_extraction.extraction_method = result['extraction_method']
            content_extraction.title = result['title']
            content_extraction.content = result.get('markdown', '')
            content_extraction.excerpt = result.get('excerpt')
            content_extraction.author = result.get('author')
            # Only update published_date if new extraction found one, otherwise preserve existing
            if result.get('published_date'):
                content_extraction.published_date = result.get('published_date')
            # If no published_date in result, keep the existing one (don't overwrite with None)
            content_extraction.success = True
            content_extraction.markdown_content = result['markdown']
            content_extraction.markdown_file_path = relative_path
            content_extraction.extraction_date = datetime.utcnow()
        
        # Update or create MarkdownFile record
        existing_md_file = session.query(MarkdownFile).filter_by(link_id=link.id).first()
        if existing_md_file:
            existing_md_file.file_path = relative_path
            existing_md_file.generation_date = datetime.utcnow()
            existing_md_file.include_content = True
        else:
            md_file = MarkdownFile(
                link_id=link.id,
                file_path=relative_path,
                include_content=True
            )
            session.add(md_file)
        
        # Note: file_path is already set above - either reused from existing_md_file or newly generated
        
        # Update QualityMetric
        quality_metric = link.quality_metric
        if quality_metric:
            quality_metric.has_markdown = True
            quality_metric.has_content = True
            # Recalculate quality score
            from database.importer import calculate_quality_score
            quality_metric.quality_score = calculate_quality_score(
                crawl_result.status_code if crawl_result else None,
                crawl_result.redirect_count if crawl_result else 0,
                True,  # has_content
                True   # has_markdown
            )
        else:
            from database.importer import calculate_quality_score
            quality_metric = QualityMetric(
                link_id=link.id,
                is_accessible=crawl_result.status_code == 200 if crawl_result else False,
                has_redirects=crawl_result.redirect_count > 0 if crawl_result else False,
                has_content=True,
                has_markdown=True,
                quality_score=calculate_quality_score(
                    crawl_result.status_code if crawl_result else None,
                    crawl_result.redirect_count if crawl_result else 0,
                    True,
                    True
                )
            )
            session.add(quality_metric)
        
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Markdown converted and saved successfully',
            'file_path': relative_path,
            'title': result['title'],
            'extraction_method': result['extraction_method']
        })
        
    except Exception as e:
        session.rollback()
        import traceback
        return jsonify({
            'success': False,
            'error': f'Error converting to markdown: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500
    finally:
        session.close()


@api_bp.route('/convert-to-markdown', methods=['POST'])
def convert_to_markdown():
    """Convert a URL to markdown format"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate URL format
        if not (url.startswith('http://') or url.startswith('https://')):
            return jsonify({'error': 'URL must start with http:// or https://'}), 400
        
        extract_method = data.get('extract_method', 'auto')
        include_metadata = data.get('include_metadata', True)
        
        from extractor.url_to_markdown import URLToMarkdownConverter
        converter = URLToMarkdownConverter()
        result = converter.convert(url, extract_method, include_metadata)
        
        if result['success']:
            return jsonify({
                'success': True,
                'markdown': result['markdown'],
                'title': result['title'],
                'excerpt': result['excerpt'],
                'author': result['author'],
                'published_date': result['published_date'].isoformat() if result['published_date'] and hasattr(result['published_date'], 'isoformat') else str(result['published_date']) if result['published_date'] else None,
                'extraction_method': result['extraction_method'],
                'final_url': result['final_url']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Conversion failed')
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@main_bp.route('/markdown/<path:filename>')
def serve_markdown(filename):
    """Serve markdown files from Obsidian vault folder"""
    markdownloads_dir = Path(r"C:\Users\spytz\OneDrive\Spyros's Vault\Spyros's Vault\Pocket Vault")
    file_path = markdownloads_dir / filename
    
    # Security check: ensure file is within markdownloads directory
    try:
        file_path.resolve().relative_to(markdownloads_dir.resolve())
    except ValueError:
        return "File not found", 404
    
    if file_path.exists() and file_path.is_file():
        return send_file(str(file_path), mimetype='text/markdown', as_attachment=True)
    else:
        return "File not found", 404


@main_bp.route('/links/add', methods=['GET', 'POST'])
def add_link():
    """Add a new link from a URL"""
    if request.method == 'GET':
        # Return the add link form page
        return render_template('add_link.html')
    
    # POST - Add the link
    session = create_session()
    try:
        url = request.form.get('url', '').strip()
        tags_input = request.form.get('tags', '').strip()
        pocket_status = request.form.get('pocket_status', 'unread')
        
        if not url:
            flash('URL is required', 'error')
            return redirect(url_for('main.add_link'))
        
        # Validate URL format
        if not (url.startswith('http://') or url.startswith('https://')):
            flash('URL must start with http:// or https://', 'error')
            return redirect(url_for('main.add_link'))
        
        # Check if link already exists
        existing_link = session.query(Link).filter_by(original_url=url).first()
        if existing_link:
            flash(f'Link already exists: {existing_link.title or url}', 'warning')
            return redirect(url_for('main.link_detail', link_id=existing_link.id))
        
        # Extract domain
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Parse tags
        tags_list = []
        if tags_input:
            tags_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
        
        # Fetch metadata from URL
        from extractor.url_to_markdown import URLToMarkdownConverter
        converter = URLToMarkdownConverter()
        
        # Fetch URL and extract basic metadata (don't need full markdown conversion)
        result = converter.convert(url, extract_method='auto', include_metadata=False)
        
        # Extract metadata
        metadata = result.get('metadata', {})
        status_code = metadata.get('status_code')
        final_url = remove_utm_parameters(result.get('final_url', url))
        title = result.get('title') or domain or 'Untitled'
        
        # Create the link
        link = Link(
            title=title,
            original_url=url,
            domain=domain,
            pocket_status=pocket_status,
            date_saved=datetime.utcnow(),
            time_added=int(datetime.utcnow().timestamp())
        )
        
        if tags_list:
            link.set_tags_list(tags_list)
        
        session.add(link)
        session.flush()  # Get the link ID
        
        # Always create crawl result if we have status code or attempted fetch
        crawl_result = CrawlResult(
            link_id=link.id,
            final_url=final_url,
            status_code=status_code,
            crawl_date=datetime.utcnow()
        )
        if metadata.get('error'):
            crawl_result.error_type = 'fetch_error'
            crawl_result.error_message = metadata.get('error')
        session.add(crawl_result)
        
        # Create content extraction if we got content metadata
        if result.get('title') or result.get('excerpt') or result.get('author'):
            content_extraction = ContentExtraction(
                link_id=link.id,
                extraction_method=result.get('extraction_method', 'auto'),
                title=result.get('title'),
                excerpt=result.get('excerpt'),
                author=result.get('author'),
                published_date=result.get('published_date'),
                extraction_date=datetime.utcnow(),
                success=result.get('success', False)
            )
            session.add(content_extraction)
        
        # Create quality metric
        from database.importer import calculate_quality_score
        has_content = bool(result.get('title') or result.get('excerpt'))
        quality_metric = QualityMetric(
            link_id=link.id,
            is_accessible=(status_code == 200),
            has_content=has_content,
            has_markdown=False,
            quality_score=calculate_quality_score(
                status_code,
                0,  # redirect_count
                has_content,
                False  # has_markdown
            )
        )
        session.add(quality_metric)
        
        session.commit()
        
        flash(f'Link added successfully: {link.title}', 'success')
        return redirect(url_for('main.link_detail', link_id=link.id))
        
    except Exception as e:
        session.rollback()
        import traceback
        flash(f'Error adding link: {str(e)}', 'error')
        logger.error(f"Error adding link: {e}\n{traceback.format_exc()}")
        return redirect(url_for('main.add_link'))
    finally:
        session.close()


@main_bp.route('/links/bulk-action', methods=['POST'])
def bulk_action():
    """Handle bulk actions (archive, delete) on multiple links"""
    session = create_session()
    try:
        action = request.form.get('action')
        link_ids = request.form.getlist('link_ids')
        
        if not action or not link_ids:
            flash('No action or links selected', 'error')
            return redirect(url_for('main.links'))
        
        link_ids = [int(id) for id in link_ids]
        links = session.query(Link).filter(Link.id.in_(link_ids)).all()
        
        if action == 'archive':
            for link in links:
                link.pocket_status = 'archive'
            session.commit()
            flash(f'{len(links)} links archived successfully', 'success')
            
        elif action == 'unarchive':
            for link in links:
                link.pocket_status = 'unread'
            session.commit()
            flash(f'{len(links)} links unarchived successfully', 'success')
            
        elif action == 'delete':
            count = len(links)
            for link in links:
                session.delete(link)
            session.commit()
            flash(f'{count} links deleted successfully', 'success')
            
        else:
            flash('Invalid action', 'error')
        
        return redirect(url_for('main.links'))
        
    except Exception as e:
        session.rollback()
        flash(f'Error performing bulk action: {str(e)}', 'error')
        return redirect(url_for('main.links'))
    finally:
        session.close()
