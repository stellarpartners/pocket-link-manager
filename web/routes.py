"""
Flask routes for web interface
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, send_file
from database.queries import LinkQuery, StatisticsQuery, paginate_query, normalize_domain
from database.models import create_session, Link, CrawlResult, QualityMetric, ContentExtraction, MarkdownFile
from sqlalchemy import desc, asc, func, or_
from datetime import datetime
from pathlib import Path
import logging
import threading
from extractor.url_utils import remove_utm_parameters
from urllib.parse import urlparse
from web.app import cache_result, clear_cache

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)


@cache_result(expiration_seconds=300)
def _get_cached_dashboard_stats():
    """Cached wrapper for dashboard stats"""
    session = create_session()
    try:
        stats_query = StatisticsQuery(session)
        return stats_query.get_dashboard_stats()
    finally:
        session.close()

@main_bp.route('/')
def index():
    """Redirect to Data Quality page"""
    return redirect(url_for('main.data_quality'))


@main_bp.route('/data-quality')
def data_quality():
    """Combined Dashboard and Quality view"""
    # Use cached dashboard stats
    dashboard_stats = _get_cached_dashboard_stats()
    return render_template('data_quality.html', stats=dashboard_stats)


@main_bp.route('/links')
def links():
    """Links listing page"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
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
        # Get all tags for autocomplete in bulk tag modal
        stats_query = StatisticsQuery(session)
        all_tags = [t['tag'] for t in stats_query.get_all_tags()]
        query = session.query(Link)
        
        # Track if joins have been performed (not just needed)
        has_crawl_join = False
        has_quality_join = False
        
        # Apply filters
        if status_code:
            query = query.join(CrawlResult).filter(CrawlResult.status_code == status_code)
            has_crawl_join = True
        
        if domain:
            # Filter by domain - handle normalized domains (www. removed)
            # Check both the normalized domain and www. prefixed version
            if not has_crawl_join:
                query = query.outerjoin(CrawlResult)
                has_crawl_join = True
            
            # Build domain filter conditions for both normalized and www. prefixed versions
            normalized_domain = normalize_domain(domain)
            domain_conditions = [
                Link.domain == normalized_domain,
                Link.domain == domain  # Original domain in case it wasn't normalized
            ]
            
            # Add www. prefixed version if domain doesn't already start with www.
            if not normalized_domain.lower().startswith('www.'):
                domain_conditions.append(Link.domain == f"www.{normalized_domain}")
            
            # Also check final_url contains the domain
            domain_conditions.append(
                func.lower(CrawlResult.final_url).like(f"%//{normalized_domain.lower()}%")
            )
            domain_conditions.append(
                func.lower(CrawlResult.final_url).like(f"%//www.{normalized_domain.lower()}%")
            )
            
            query = query.filter(or_(*domain_conditions)).distinct()
        
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
            if not has_quality_join:
                query = query.join(QualityMetric)
                has_quality_join = True
            if quality_min is not None:
                query = query.filter(QualityMetric.quality_score >= quality_min)
            if quality_max is not None:
                query = query.filter(QualityMetric.quality_score <= quality_max)
        
        if search and search.strip():
            # SQLite LIKE is case-insensitive by default, but we'll use lower() for explicit case-insensitive search
            # Prioritize final URL over original URL - work with final URLs
            search_lower = search.strip().lower()
            
            # Search in title, final URL (prioritized), domain, and original URL (fallback)
            # Use outer join to include links without crawl results
            if not has_crawl_join:
                query = query.outerjoin(CrawlResult)
                has_crawl_join = True
            
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
            if not has_quality_join:
                query = query.join(QualityMetric)
                has_quality_join = True
            order_func = desc if sort_order == 'desc' else asc
            query = query.order_by(order_func(QualityMetric.quality_score))
        elif sort_by == 'domain':
            order_func = desc if sort_order == 'desc' else asc
            query = query.order_by(order_func(Link.domain))
        
        # Paginate
        paginated = paginate_query(query, page, per_page)
        
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
                             current_tag=tag,
                             all_tags=all_tags)
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
        
        # Get recently used tags (3 most recent)
        recent_tags = stats_query.get_recently_used_tags(limit=3)
        
        # Get referrer for back button, prioritize 'back' query param
        referrer = request.args.get('back') or request.referrer
        # Only use referrer if it's from our own site and not the link detail itself
        if not referrer or url_for('main.link_detail', link_id=link_id) in referrer:
            referrer = url_for('main.links')
        
        # Normalize domain for display and filtering
        normalized_domain = normalize_domain(link.domain) if link.domain else None
        
        return render_template('link_detail.html',
                             link=link,
                             crawl_result=crawl_result,
                             content_extraction=content_extraction,
                             quality_metric=quality_metric,
                             all_tags=all_tags,
                             recent_tags=recent_tags,
                             back_url=referrer,
                             normalized_domain=normalized_domain)
    finally:
        session.close()


@main_bp.route('/quality')
def quality():
    """Redirect to Data Quality page"""
    return redirect(url_for('main.data_quality'))


@main_bp.route('/domains')
def domains():
    """Domains listing page"""
    page = request.args.get('page', 1, type=int)
    per_page = 25
    sort_by = request.args.get('sort_by', 'count', type=str)
    sort_order = request.args.get('sort_order', 'desc', type=str)
    search = request.args.get('search', type=str)
    
    session = create_session()
    try:
        stats_query = StatisticsQuery(session)
        # Get domain stats with quality metrics (no limit to show all domains)
        domains_list = stats_query.get_domain_stats(limit=10000)
        
        # Apply search filter if provided
        if search and search.strip():
            search_lower = search.strip().lower()
            domains_list = [
                d for d in domains_list 
                if search_lower in d['domain'].lower()
            ]
        
        # Apply sorting
        if sort_by == 'domain':
            # Sort by domain name alphabetically
            domains_list.sort(key=lambda x: x['domain'].lower(), reverse=(sort_order == 'desc'))
        elif sort_by == 'count' or sort_by == 'total':
            # Sort by link count
            domains_list.sort(key=lambda x: x['total'], reverse=(sort_order == 'desc'))
        elif sort_by == 'success_rate':
            # Sort by success rate
            domains_list.sort(key=lambda x: x.get('success_rate', 0), reverse=(sort_order == 'desc'))
        elif sort_by == 'quality':
            # Sort by average quality score
            domains_list.sort(key=lambda x: x.get('avg_quality_score', 0), reverse=(sort_order == 'desc'))
        
        # Calculate pagination
        total = len(domains_list)
        pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_domains = domains_list[start_idx:end_idx]
        
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages
        }
        
        # Build filters dict for pagination links
        filters = {}
        if search and search.strip():
            filters['search'] = search.strip()
        if sort_by and sort_by.strip():
            filters['sort_by'] = sort_by
        if sort_order and sort_order.strip():
            filters['sort_order'] = sort_order
        
        return render_template('domains.html', 
                             domains=paginated_domains,
                             pagination=pagination,
                             sort_by=sort_by,
                             sort_order=sort_order,
                             search=search or '',
                             filters=filters)
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
    # Use cached dashboard stats
    stats = _get_cached_dashboard_stats()
    return jsonify(stats)


@api_bp.route('/links')
def api_links():
    """API endpoint for links with filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    status_code = request.args.get('status_code', type=int)
    domain = request.args.get('domain', type=str)
    
    link_query = LinkQuery()
    query = link_query.session.query(Link)
    
    if status_code:
        query = query.join(CrawlResult).filter(CrawlResult.status_code == status_code)
    if domain:
        # Filter by domain - handle normalized domains (www. removed)
        normalized_domain = normalize_domain(domain)
        domain_conditions = [
            Link.domain == normalized_domain,
            Link.domain == domain  # Original domain in case it wasn't normalized
        ]
        # Add www. prefixed version if domain doesn't already start with www.
        if not normalized_domain.lower().startswith('www.'):
            domain_conditions.append(Link.domain == f"www.{normalized_domain}")
        query = query.filter(or_(*domain_conditions))
    
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
        
        # Clear relevant caches
        clear_cache('index')  # Clear dashboard cache
        clear_cache('api_stats')  # Clear stats cache
        
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
        
        # Determine where to redirect
        next_url = request.form.get('next') or request.referrer
        if not next_url or url_for('main.link_detail', link_id=link_id) in next_url:
            next_url = url_for('main.links')
            
        return redirect(next_url)
        
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
            
        return redirect(request.referrer or url_for('main.link_detail', link_id=link_id))
    except Exception as e:
        session.rollback()
        flash(f'Error adding tag: {str(e)}', 'error')
        return redirect(request.referrer or url_for('main.link_detail', link_id=link_id))
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
            
        return redirect(request.referrer or url_for('main.link_detail', link_id=link_id))
    except Exception as e:
        session.rollback()
        flash(f'Error removing tag: {str(e)}', 'error')
        return redirect(request.referrer or url_for('main.link_detail', link_id=link_id))
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
        
        return redirect(request.referrer or url_for('main.link_detail', link_id=link_id))
        
    except Exception as e:
        session.rollback()
        flash(f'Error updating final URL: {str(e)}', 'error')
        return redirect(request.referrer or url_for('main.link_detail', link_id=link_id))
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
        
        return redirect(request.referrer or url_for('main.link_detail', link_id=link_id))
        
    except Exception as e:
        session.rollback()
        flash(f'Error updating metadata: {str(e)}', 'error')
        return redirect(request.referrer or url_for('main.link_detail', link_id=link_id))
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
        
        final_url = remove_utm_parameters(result['final_url'])
        crawl_result.final_url = final_url
        crawl_result.status_code = result['metadata'].get('status_code', 200)
        crawl_result.crawl_date = datetime.utcnow()
        
        # Update domain if changed
        from urllib.parse import urlparse
        parsed_url = urlparse(final_url)
        if parsed_url.netloc and parsed_url.netloc != link.domain:
            link.domain = parsed_url.netloc
        
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


@main_bp.route('/tags/rename', methods=['POST'])
def rename_tag():
    """Rename a tag across all links"""
    session = create_session()
    try:
        old_tag = request.form.get('old_tag', '').strip()
        new_tag = request.form.get('new_tag', '').strip()
        
        if not old_tag or not new_tag:
            flash('Both old and new tag names are required', 'error')
            return redirect(url_for('main.tags'))
        
        if old_tag == new_tag:
            flash('New tag name must be different from the old name', 'warning')
            return redirect(url_for('main.tags'))
        
        # Find all links that have the old tag
        tag_patterns = [
            f'"{old_tag}"',  # JSON double quotes
            f"'{old_tag}'",   # Single quotes (for Python list syntax)
        ]
        tag_filters = [Link.tags.contains(pattern) for pattern in tag_patterns]
        links_with_tag = session.query(Link).filter(or_(*tag_filters)).all()
        
        if not links_with_tag:
            flash(f'No links found with tag "{old_tag}"', 'warning')
            return redirect(url_for('main.tags'))
        
        # Update all links: replace old tag with new tag
        updated_count = 0
        for link in links_with_tag:
            current_tags = link.get_tags_list()
            if old_tag in current_tags:
                # Replace old tag with new tag
                current_tags = [new_tag if tag == old_tag else tag for tag in current_tags]
                link.set_tags_list(current_tags)
                updated_count += 1
        
        session.commit()
        
        # Clear caches
        clear_cache('index')
        clear_cache('api_stats')
        
        flash(f'Tag "{old_tag}" renamed to "{new_tag}" in {updated_count} link(s)', 'success')
        return redirect(url_for('main.tags'))
        
    except Exception as e:
        session.rollback()
        flash(f'Error renaming tag: {str(e)}', 'error')
        return redirect(url_for('main.tags'))
    finally:
        session.close()


@main_bp.route('/sync')
def sync():
    """Sync page showing all links synced to Obsidian with their tags"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    search = request.args.get('search', type=str)
    tag = request.args.get('tag', type=str)
    sort_by = request.args.get('sort_by', 'generation_date', type=str)
    sort_order = request.args.get('sort_order', 'desc', type=str)
    
    session = create_session()
    try:
        # Get all tags for autocomplete in bulk tag modal
        stats_query = StatisticsQuery(session)
        all_tags = [t['tag'] for t in stats_query.get_all_tags()]
        
        # Query links that have markdown files (synced to Obsidian)
        # Eagerly load markdown_files relationship
        from sqlalchemy.orm import joinedload
        query = session.query(Link).join(MarkdownFile).options(
            joinedload(Link.markdown_files)
        ).distinct()
        
        # Apply search filter
        if search and search.strip():
            search_lower = search.strip().lower()
            query = query.filter(
                or_(
                    func.lower(Link.title).like(f"%{search_lower}%"),
                    func.lower(Link.domain).like(f"%{search_lower}%"),
                    func.lower(Link.original_url).like(f"%{search_lower}%")
                )
            )
        
        # Apply tag filter
        if tag and tag.strip():
            tag_value = tag.strip()
            tag_patterns = [
                f'"{tag_value}"',
                f"'{tag_value}'",
            ]
            tag_filters = [Link.tags.contains(pattern) for pattern in tag_patterns]
            query = query.filter(or_(*tag_filters))
        
        # Apply sorting
        if sort_by == 'generation_date':
            # Sort by most recent markdown file generation date
            order_func = desc if sort_order == 'desc' else asc
            query = query.order_by(order_func(MarkdownFile.generation_date))
        elif sort_by == 'date_saved':
            order_func = desc if sort_order == 'desc' else asc
            query = query.order_by(order_func(Link.date_saved))
        elif sort_by == 'domain':
            order_func = desc if sort_order == 'desc' else asc
            query = query.order_by(order_func(Link.domain))
        
        # Paginate
        paginated = paginate_query(query, page, per_page)
        
        # Build filters dict
        filters = {}
        if search and search.strip():
            filters['search'] = search.strip()
        if tag and tag.strip():
            filters['tag'] = tag.strip()
        if sort_by and sort_by.strip():
            filters['sort_by'] = sort_by
        if sort_order and sort_order.strip():
            filters['sort_order'] = sort_order
        
        return render_template('sync.html',
                             links=paginated['items'],
                             pagination=paginated,
                             filters=filters,
                             current_tag=tag,
                             all_tags=all_tags)
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
        
        # Update domain if changed during conversion
        if result.get('final_url'):
            final_url = remove_utm_parameters(result['final_url'])
            from urllib.parse import urlparse
            parsed_url = urlparse(final_url)
            if parsed_url.netloc and parsed_url.netloc != link.domain:
                link.domain = parsed_url.netloc
        
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
        
        # Update domain from final URL if available
        from urllib.parse import urlparse
        final_parsed = urlparse(final_url)
        if final_parsed.netloc:
            domain = final_parsed.netloc
            
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
        
        # Clear caches
        clear_cache('index')
        clear_cache('api_stats')
        clear_cache('api_domains')
        
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
            # Clear caches
            clear_cache('index')
            clear_cache('api_stats')
            
        elif action == 'unarchive':
            for link in links:
                link.pocket_status = 'unread'
            session.commit()
            flash(f'{len(links)} links unarchived successfully', 'success')
            # Clear caches
            clear_cache('index')
            clear_cache('api_stats')
            
        elif action == 'delete':
            count = len(links)
            for link in links:
                session.delete(link)
            session.commit()
            flash(f'{count} links deleted successfully', 'success')
            # Clear caches
            clear_cache('index')
            clear_cache('api_stats')
            clear_cache('api_domains')
            
        elif action == 'add_tags':
            # Bulk add tags to selected links
            tags_input = request.form.get('tags', '').strip()
            referrer = request.referrer or url_for('main.links')
            
            # Determine redirect URL - check if coming from sync page
            if '/sync' in referrer:
                redirect_url = url_for('main.sync')
            else:
                redirect_url = url_for('main.links')
            
            if not tags_input:
                flash('No tags provided', 'error')
                return redirect(redirect_url)
            
            # Parse tags (comma-separated)
            new_tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            if not new_tags:
                flash('No valid tags provided', 'error')
                return redirect(redirect_url)
            
            updated_count = 0
            for link in links:
                current_tags = link.get_tags_list()
                # Add new tags that don't already exist
                for tag in new_tags:
                    if tag not in current_tags:
                        current_tags.append(tag)
                link.set_tags_list(current_tags)
                updated_count += 1
            
            session.commit()
            flash(f'Tags "{", ".join(new_tags)}" added to {updated_count} link(s)', 'success')
            # Clear caches
            clear_cache('index')
            clear_cache('api_stats')
            
            return redirect(redirect_url)
            
        elif action == 'refresh':
            # Refresh metadata for selected links
            refreshed_count = 0
            failed_count = 0
            
            for link in links:
                try:
                    # Prefer final URL if available, otherwise original
                    url = link.original_url
                    crawl_result = link.latest_crawl()
                    if crawl_result and crawl_result.final_url:
                        url = crawl_result.final_url
                    
                    from extractor.url_to_markdown import URLToMarkdownConverter
                    converter = URLToMarkdownConverter()
                    
                    # Fetch and extract metadata
                    result = converter.convert(url, extract_method='auto', include_metadata=False)
                    
                    if result['success']:
                        # Update Link title if found
                        if result.get('title'):
                            link.title = result['title']
                        
                        # Update CrawlResult
                        if not crawl_result:
                            crawl_result = CrawlResult(link_id=link.id)
                            session.add(crawl_result)
                        
                        final_url = remove_utm_parameters(result['final_url'])
                        crawl_result.final_url = final_url
                        crawl_result.status_code = result['metadata'].get('status_code', 200)
                        crawl_result.crawl_date = datetime.utcnow()
                        
                        # Update domain if changed
                        from urllib.parse import urlparse
                        parsed_url = urlparse(final_url)
                        if parsed_url.netloc and parsed_url.netloc != link.domain:
                            link.domain = parsed_url.netloc
                        
                        # Update ContentExtraction
                        extraction = link.latest_content()
                        if not extraction:
                            extraction = ContentExtraction(link_id=link.id)
                            session.add(extraction)
                        
                        extraction.title = result.get('title')
                        extraction.author = result.get('author')
                        extraction.excerpt = result.get('excerpt')
                        extraction.published_date = result.get('published_date')
                        extraction.extraction_method = result.get('extraction_method', 'auto')
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
                            True,  # has_content
                            quality.has_markdown
                        )
                        quality.last_updated = datetime.utcnow()
                        
                        refreshed_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error refreshing link {link.id}: {e}")
                    failed_count += 1
            
            session.commit()
            if failed_count > 0:
                flash(f'{refreshed_count} links refreshed successfully, {failed_count} failed', 'warning' if refreshed_count > 0 else 'error')
            else:
                flash(f'{refreshed_count} links refreshed successfully', 'success')
            
        else:
            flash('Invalid action', 'error')
        
        return redirect(request.referrer or url_for('main.links'))
        
    except Exception as e:
        session.rollback()
        flash(f'Error performing bulk action: {str(e)}', 'error')
        return redirect(request.referrer or url_for('main.links'))
    finally:
        session.close()


@cache_result(expiration_seconds=600)
def _get_cached_domain_counts():
    """Cached wrapper for domain counts"""
    session = create_session()
    try:
        stats_query = StatisticsQuery(session)
        return stats_query.get_domain_link_counts()
    finally:
        session.close()

@api_bp.route('/domains', methods=['GET'])
def api_domains():
    """Get list of domains with link counts"""
    # Use cached domain counts
    domains = _get_cached_domain_counts()
    return jsonify({
        'domains': domains,
        'total': len(domains)
    })


@api_bp.route('/tags', methods=['GET'])
def api_tags():
    """Get all tags for autocomplete"""
    session = create_session()
    try:
        stats_query = StatisticsQuery(session)
        all_tags = [t['tag'] for t in stats_query.get_all_tags()]
        return jsonify({
            'tags': all_tags,
            'total': len(all_tags)
        })
    finally:
        session.close()


@api_bp.route('/links/get-all-ids', methods=['GET'])
def api_get_all_link_ids():
    """Get all link IDs matching current filters (for select all functionality)"""
    session = create_session()
    try:
        # Get filter parameters from query string (same as links() route)
        status_code = request.args.get('status_code', type=int)
        domain = request.args.get('domain', type=str)
        pocket_status = request.args.get('pocket_status', type=str)
        quality_min = request.args.get('quality_min', type=int)
        quality_max = request.args.get('quality_max', type=int)
        search = request.args.get('search', type=str)
        tag = request.args.get('tag', type=str)
        
        query = session.query(Link.id)
        
        # Track if joins have been performed
        has_crawl_join = False
        has_quality_join = False
        
        # Apply filters (same logic as links() route)
        if status_code:
            query = query.join(CrawlResult).filter(CrawlResult.status_code == status_code)
            has_crawl_join = True
        
        if domain:
            # Filter by domain - handle normalized domains (www. removed)
            if not has_crawl_join:
                query = query.outerjoin(CrawlResult)
                has_crawl_join = True
            
            # Build domain filter conditions for both normalized and www. prefixed versions
            normalized_domain = normalize_domain(domain)
            domain_conditions = [
                Link.domain == normalized_domain,
                Link.domain == domain  # Original domain in case it wasn't normalized
            ]
            
            # Add www. prefixed version if domain doesn't already start with www.
            if not normalized_domain.lower().startswith('www.'):
                domain_conditions.append(Link.domain == f"www.{normalized_domain}")
            
            # Also check final_url contains the domain
            domain_conditions.append(
                func.lower(CrawlResult.final_url).like(f"%//{normalized_domain.lower()}%")
            )
            domain_conditions.append(
                func.lower(CrawlResult.final_url).like(f"%//www.{normalized_domain.lower()}%")
            )
            
            query = query.filter(or_(*domain_conditions)).distinct()
        
        if pocket_status:
            query = query.filter(Link.pocket_status == pocket_status)
        
        if tag and tag.strip():
            tag_value = tag.strip()
            tag_patterns = [
                f'"{tag_value}"',
                f"'{tag_value}'",
            ]
            tag_filters = [Link.tags.contains(pattern) for pattern in tag_patterns]
            query = query.filter(or_(*tag_filters))
        
        if quality_min is not None or quality_max is not None:
            if not has_quality_join:
                query = query.join(QualityMetric)
                has_quality_join = True
            if quality_min is not None:
                query = query.filter(QualityMetric.quality_score >= quality_min)
            if quality_max is not None:
                query = query.filter(QualityMetric.quality_score <= quality_max)
        
        if search and search.strip():
            search_lower = search.strip().lower()
            if not has_crawl_join:
                query = query.outerjoin(CrawlResult)
                has_crawl_join = True
            
            search_filters = [
                func.lower(Link.title).like(f"%{search_lower}%"),
                func.lower(CrawlResult.final_url).like(f"%{search_lower}%"),
                func.lower(Link.domain).like(f"%{search_lower}%"),
                func.lower(Link.original_url).like(f"%{search_lower}%")
            ]
            query = query.filter(or_(*search_filters)).distinct()
        
        # Get all matching link IDs
        link_ids = [link_id for (link_id,) in query.all()]
        
        return jsonify({
            'success': True,
            'link_ids': link_ids,
            'total': len(link_ids)
        })
    except Exception as e:
        logger.error(f"Error getting all link IDs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


def refresh_link_metadata(link_id):
    """Helper function to refresh a single link's metadata"""
    session = create_session()
    try:
        link = session.query(Link).filter_by(id=link_id).first()
        if not link:
            logger.warning(f"Link {link_id} not found for refresh")
            return False
        
        # Prefer final URL if available, otherwise original
        url = link.original_url
        crawl_result = link.latest_crawl()
        if crawl_result and crawl_result.final_url:
            url = crawl_result.final_url
        
        from extractor.url_to_markdown import URLToMarkdownConverter
        converter = URLToMarkdownConverter()
        
        # Fetch and extract metadata
        result = converter.convert(url, extract_method='auto', include_metadata=False)
        
        if not result['success']:
            # Even if extraction fails, update crawl result if we have status code
            if result.get('metadata', {}).get('status_code'):
                if not crawl_result:
                    crawl_result = CrawlResult(link_id=link.id)
                    session.add(crawl_result)
                crawl_result.status_code = result['metadata']['status_code']
                crawl_result.final_url = remove_utm_parameters(result.get('final_url', url))
                crawl_result.crawl_date = datetime.utcnow()
                session.commit()
            return False
        
        # Update Link title if found
        if result.get('title'):
            link.title = result['title']
        
        # Update CrawlResult
        if not crawl_result:
            crawl_result = CrawlResult(link_id=link.id)
            session.add(crawl_result)
        
        final_url = remove_utm_parameters(result.get('final_url', url))
        crawl_result.final_url = final_url
        crawl_result.status_code = result.get('metadata', {}).get('status_code', 200)
        crawl_result.crawl_date = datetime.utcnow()
        
        # Update domain if changed
        parsed_url = urlparse(final_url)
        if parsed_url.netloc and parsed_url.netloc != link.domain:
            link.domain = parsed_url.netloc
        
        # Update ContentExtraction
        extraction = link.latest_content()
        if not extraction:
            extraction = ContentExtraction(link_id=link.id)
            session.add(extraction)
        
        extraction.title = result.get('title')
        extraction.author = result.get('author')
        extraction.excerpt = result.get('excerpt')
        extraction.published_date = result.get('published_date')
        extraction.extraction_method = result.get('extraction_method', 'auto')
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
            True,  # has_content
            quality.has_markdown
        )
        quality.last_updated = datetime.utcnow()
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error refreshing link {link_id}: {e}")
        return False
    finally:
        session.close()


def process_bulk_refresh_background(link_ids):
    """Process bulk refresh in background thread"""
    refreshed_count = 0
    failed_count = 0
    
    for link_id in link_ids:
        try:
            if refresh_link_metadata(link_id):
                refreshed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            logger.error(f"Error in background refresh for link {link_id}: {e}")
            failed_count += 1
    
    logger.info(f"Bulk refresh completed: {refreshed_count} succeeded, {failed_count} failed")


@api_bp.route('/links/bulk-refresh', methods=['POST'])
def api_bulk_refresh():
    """Start bulk refresh process in background - continues even if user navigates away"""
    try:
        data = request.get_json()
        link_ids = data.get('link_ids', [])
        
        if not link_ids:
            return jsonify({'success': False, 'error': 'No link IDs provided'}), 400
        
        # Validate link IDs
        try:
            link_ids = [int(id) for id in link_ids]
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Invalid link IDs'}), 400
        
        # Start background thread to process refresh
        thread = threading.Thread(
            target=process_bulk_refresh_background,
            args=(link_ids,),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Bulk refresh started for {len(link_ids)} links. Processing will continue in the background.',
            'total': len(link_ids)
        })
        
    except Exception as e:
        logger.error(f"Error starting bulk refresh: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/domains/<domain>/bulk-refresh', methods=['POST'])
def api_domain_bulk_refresh(domain):
    """Start bulk refresh process for all links in a domain"""
    try:
        session = create_session()
        try:
            # Normalize domain and get all link IDs for this domain
            normalized_domain = normalize_domain(domain)
            domain_conditions = [
                Link.domain == normalized_domain,
                Link.domain == domain  # Original domain in case it wasn't normalized
            ]
            
            # Add www. prefixed version if domain doesn't already start with www.
            if not normalized_domain.lower().startswith('www.'):
                domain_conditions.append(Link.domain == f"www.{normalized_domain}")
            
            # Get all link IDs for this domain
            link_ids = [
                link.id for link in session.query(Link.id).filter(or_(*domain_conditions)).all()
            ]
            
            if not link_ids:
                return jsonify({'success': False, 'error': f'No links found for domain {domain}'}), 404
            
            # Start background thread to process refresh
            thread = threading.Thread(
                target=process_bulk_refresh_background,
                args=(link_ids,),
                daemon=True
            )
            thread.start()
            
            return jsonify({
                'success': True,
                'message': f'Bulk refresh started for {len(link_ids)} links in domain {normalized_domain}. Processing will continue in the background.',
                'total': len(link_ids),
                'domain': normalized_domain
            })
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error starting domain bulk refresh for {domain}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
