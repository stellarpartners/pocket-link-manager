"""
Common database queries and utilities
"""

from sqlalchemy import func, and_, or_, desc, asc, Integer, case
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from .models import (
    Link, CrawlResult, ContentExtraction, MarkdownFile, QualityMetric,
    create_session
)


class LinkQuery:
    """Query builder for links"""
    
    def __init__(self, session=None):
        self.session = session or create_session()
    
    def get_by_id(self, link_id: int) -> Optional[Link]:
        """Get a link by ID with all relationships loaded"""
        return self.session.query(Link).options(
            joinedload(Link.crawl_results),
            joinedload(Link.content_extractions),
            joinedload(Link.markdown_files),
            joinedload(Link.quality_metric)
        ).filter_by(id=link_id).first()
    
    def get_by_url(self, url: str) -> Optional[Link]:
        """Get a link by original URL"""
        return self.session.query(Link).filter_by(original_url=url).first()
    
    def filter_by_status_code(self, status_code: int):
        """Filter links by crawl status code"""
        return self.session.query(Link).join(CrawlResult).filter(
            CrawlResult.status_code == status_code
        )
    
    def filter_by_domain(self, domain: str):
        """Filter links by domain"""
        return self.session.query(Link).filter(Link.domain == domain)
    
    def filter_by_pocket_status(self, status: str):
        """Filter by Pocket status (unread/archive)"""
        return self.session.query(Link).filter(Link.pocket_status == status)
    
    def filter_by_quality_score(self, min_score: int = 0, max_score: int = 100):
        """Filter links by quality score range"""
        return self.session.query(Link).join(QualityMetric).filter(
            and_(
                QualityMetric.quality_score >= min_score,
                QualityMetric.quality_score <= max_score
            )
        )
    
    def filter_accessible(self, accessible: bool = True):
        """Filter by accessibility (status 200)"""
        return self.session.query(Link).join(QualityMetric).filter(
            QualityMetric.is_accessible == accessible
        )
    
    def filter_has_content(self, has_content: bool = True):
        """Filter links that have extracted content"""
        return self.session.query(Link).join(QualityMetric).filter(
            QualityMetric.has_content == has_content
        )
    
    def filter_has_markdown(self, has_markdown: bool = True):
        """Filter links that have generated markdown"""
        return self.session.query(Link).join(QualityMetric).filter(
            QualityMetric.has_markdown == has_markdown
        )
    
    def search(self, query: str):
        """Search links by title or URL"""
        search_term = f"%{query}%"
        return self.session.query(Link).filter(
            or_(
                Link.title.like(search_term),
                Link.original_url.like(search_term),
                Link.domain.like(search_term)
            )
        )
    
    def filter_by_tags(self, tags: List[str], match_all: bool = False):
        """Filter links by tags"""
        # This is a simplified version - for production, consider a tags table
        query = self.session.query(Link)
        if match_all:
            for tag in tags:
                query = query.filter(Link.tags.contains(tag))
        else:
            tag_filter = or_(*[Link.tags.contains(tag) for tag in tags])
            query = query.filter(tag_filter)
        return query
    
    def filter_by_date_range(self, start_date: datetime = None, end_date: datetime = None):
        """Filter links by date saved"""
        query = self.session.query(Link)
        if start_date:
            query = query.filter(Link.date_saved >= start_date)
        if end_date:
            query = query.filter(Link.date_saved <= end_date)
        return query
    
    def get_recent(self, days: int = 30, limit: int = 100):
        """Get recently saved links"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.session.query(Link).filter(
            Link.date_saved >= cutoff_date
        ).order_by(desc(Link.date_saved)).limit(limit).all()
    
    def get_unread(self, limit: int = None):
        """Get unread links"""
        query = self.session.query(Link).filter(Link.pocket_status == 'unread')
        if limit:
            query = query.limit(limit)
        return query.order_by(desc(Link.date_saved)).all()
    
    def get_broken_links(self):
        """Get links with 4xx or 5xx status codes"""
        return self.session.query(Link).join(CrawlResult).filter(
            or_(
                CrawlResult.status_code.between(400, 499),
                CrawlResult.status_code.between(500, 599)
            )
        ).all()
    
    def get_uncrawled(self):
        """Get links that haven't been crawled yet"""
        return self.session.query(Link).outerjoin(CrawlResult).filter(
            CrawlResult.id == None
        ).all()
    
    def get_without_content(self):
        """Get links that don't have extracted content"""
        return self.session.query(Link).join(QualityMetric).filter(
            QualityMetric.has_content == False
        ).all()
    
    def get_without_markdown(self):
        """Get links that don't have generated markdown"""
        return self.session.query(Link).join(QualityMetric).filter(
            QualityMetric.has_markdown == False
        ).all()
    
    def get_links_by_domain(self, domain: str):
        """Get all links for a specific domain"""
        return self.session.query(Link).filter(Link.domain == domain)
    
    def get_uncrawled_by_domain(self, domain: str):
        """Get links for a domain that haven't been crawled yet"""
        return self.session.query(Link).outerjoin(CrawlResult).filter(
            and_(
                Link.domain == domain,
                CrawlResult.id == None
            )
        )
    
    def get_domains_with_links(self):
        """Get all domains that have links, with link counts"""
        results = self.session.query(
            Link.domain,
            func.count(Link.id).label('count')
        ).filter(
            Link.domain.isnot(None),
            Link.domain != ''
        ).group_by(Link.domain).order_by(desc('count')).all()
        
        return [{'domain': domain, 'count': count} for domain, count in results]


def normalize_domain(domain: str) -> str:
    """Normalize domain by removing www. prefix"""
    if not domain:
        return domain
    domain_lower = domain.lower()
    if domain_lower.startswith('www.'):
        return domain[4:]  # Remove 'www.' prefix, preserving case of rest
    return domain


class StatisticsQuery:
    """Query builder for statistics and aggregations"""
    
    def __init__(self, session=None):
        self.session = session or create_session()
    
    def get_total_count(self) -> int:
        """Get total number of links"""
        return self.session.query(Link).count()
    
    def get_status_code_breakdown(self) -> Dict[str, int]:
        """Get count of links by status code, grouped as requested"""
        results = self.session.query(
            CrawlResult.status_code,
            func.count(CrawlResult.id).label('count')
        ).group_by(CrawlResult.status_code).all()
        
        breakdown = {
            '200': 0,
            '403': 0,
            '404': 0,
            '4XX': 0,
            '5XX': 0
        }
        
        for status_code, count in results:
            if not status_code:
                continue
                
            code_str = str(status_code)
            if code_str == '200':
                breakdown['200'] += count
            elif code_str == '403':
                breakdown['403'] += count
            elif code_str == '404':
                breakdown['404'] += count
            elif code_str.startswith('4'):
                breakdown['4XX'] += count
            elif code_str.startswith('5'):
                breakdown['5XX'] += count
        
        # Remove categories with 0 counts to keep it clean
        return {k: v for k, v in breakdown.items() if v > 0}
    
    def get_domain_stats(self, limit: int = 20) -> List[Dict]:
        """Get statistics by domain, normalized (www. removed) and sorted by success_rate * total"""
        # Link.domain should be synced with final URL when updated
        # This ensures we're working with final URLs
        results = self.session.query(
            Link.domain,
            func.count(Link.id).label('total'),
            func.sum(func.cast(QualityMetric.is_accessible, Integer)).label('accessible'),
            func.avg(QualityMetric.quality_score).label('avg_score')
        ).join(QualityMetric).filter(
            Link.domain.isnot(None),
            Link.domain != ''
        ).group_by(Link.domain).all()
        
        # Normalize domains and aggregate statistics
        domain_stats = {}
        domain_to_original = {}
        
        for domain, total, accessible, avg_score in results:
            normalized = normalize_domain(domain)
            if normalized not in domain_stats:
                domain_stats[normalized] = {
                    'total': 0,
                    'accessible': 0,
                    'quality_scores': []
                }
                domain_to_original[normalized] = []
            domain_stats[normalized]['total'] += total
            domain_stats[normalized]['accessible'] += accessible or 0
            if avg_score:
                domain_stats[normalized]['quality_scores'].append((avg_score, total))
            domain_to_original[normalized].append(domain)
        
        # Calculate weighted average quality scores and build result list
        domain_list = []
        for normalized_domain in domain_stats.keys():
            stats = domain_stats[normalized_domain]
            total = stats['total']
            accessible = stats['accessible']
            
            # Calculate weighted average quality score
            if stats['quality_scores']:
                weighted_sum = sum(score * count for score, count in stats['quality_scores'])
                total_weight = sum(count for _, count in stats['quality_scores'])
                avg_quality_score = weighted_sum / total_weight if total_weight > 0 else 0
            else:
                avg_quality_score = 0
            
            success_rate = round(accessible / total * 100, 1) if total > 0 else 0
            score = success_rate * total  # Calculate score: success_rate * total
            
            domain_list.append({
                'domain': normalized_domain,
                'total': total,
                'accessible': accessible,
                'success_rate': success_rate,
                'avg_quality_score': round(avg_quality_score, 1),
                'score': score,  # Add score for sorting
                'original_domains': domain_to_original[normalized_domain]  # For filtering
            })
        
        # Sort by score (success_rate * total) in descending order
        domain_list.sort(key=lambda x: x['score'], reverse=True)
        
        # Apply limit after sorting
        return domain_list[:limit]
    
    def get_domain_link_counts(self) -> List[Dict]:
        """Get all domains with their link counts, normalized (www. removed) and sorted alphabetically"""
        results = self.session.query(
            Link.domain,
            func.count(Link.id).label('count')
        ).filter(
            Link.domain.isnot(None),
            Link.domain != ''
        ).group_by(Link.domain).all()
        
        # Normalize domains and aggregate counts
        domain_counts = {}
        domain_to_original = {}  # Map normalized to original domain(s) for filtering
        
        for domain, count in results:
            normalized = normalize_domain(domain)
            if normalized not in domain_counts:
                domain_counts[normalized] = 0
                domain_to_original[normalized] = []
            domain_counts[normalized] += count
            domain_to_original[normalized].append(domain)
        
        # Convert to list and sort alphabetically by normalized domain
        domain_list = [
            {
                'domain': normalized_domain,
                'count': domain_counts[normalized_domain],
                'original_domains': domain_to_original[normalized_domain]  # For filtering
            }
            for normalized_domain in sorted(domain_counts.keys())
        ]
        
        return domain_list
    
    def get_quality_distribution(self) -> Dict[str, int]:
        """Get distribution of quality scores"""
        results = self.session.query(
            case(
                (QualityMetric.quality_score >= 80, 'excellent'),
                (QualityMetric.quality_score >= 60, 'good'),
                (QualityMetric.quality_score >= 40, 'fair'),
                else_='poor'
            ).label('category'),
            func.count(QualityMetric.link_id).label('count')
        ).group_by('category').all()
        
        return {category: count for category, count in results}
    
    def get_pocket_status_breakdown(self) -> Dict[str, int]:
        """Get breakdown by Pocket status"""
        results = self.session.query(
            Link.pocket_status,
            func.count(Link.id).label('count')
        ).group_by(Link.pocket_status).all()
        
        return {status: count for status, count in results if status}
    
    def get_content_extraction_stats(self) -> Dict[str, Any]:
        """Get statistics about content extraction"""
        total = self.session.query(Link).count()
        with_content = self.session.query(QualityMetric).filter(
            QualityMetric.has_content == True
        ).count()
        successful_extractions = self.session.query(ContentExtraction).filter(
            ContentExtraction.success == True
        ).count()
        failed_extractions = self.session.query(ContentExtraction).filter(
            ContentExtraction.success == False
        ).count()
        
        return {
            'total_links': total,
            'with_content': with_content,
            'content_rate': round(with_content / total * 100, 1) if total > 0 else 0,
            'successful_extractions': successful_extractions,
            'failed_extractions': failed_extractions,
            'success_rate': round(successful_extractions / (successful_extractions + failed_extractions) * 100, 1)
            if (successful_extractions + failed_extractions) > 0 else 0
        }
    
    def get_markdown_stats(self) -> Dict[str, Any]:
        """Get statistics about markdown generation"""
        total = self.session.query(Link).count()
        with_markdown = self.session.query(QualityMetric).filter(
            QualityMetric.has_markdown == True
        ).count()
        markdown_files = self.session.query(MarkdownFile).count()
        
        return {
            'total_links': total,
            'with_markdown': with_markdown,
            'markdown_rate': round(with_markdown / total * 100, 1) if total > 0 else 0,
            'total_files': markdown_files
        }
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics"""
        total = self.get_total_count()
        status_breakdown = self.get_status_code_breakdown()
        quality_dist = self.get_quality_distribution()
        pocket_status = self.get_pocket_status_breakdown()
        
        accessible_count = self.session.query(QualityMetric).filter(
            QualityMetric.is_accessible == True
        ).count()
        
        return {
            'total_links': total,
            'accessible_links': accessible_count,
            'accessibility_rate': round(accessible_count / total * 100, 1) if total > 0 else 0,
            'status_code_breakdown': status_breakdown,
            'quality_distribution': quality_dist,
            'pocket_status': pocket_status,
            'top_domains': self.get_domain_stats(limit=10),
            'content_stats': self.get_content_extraction_stats(),
            'markdown_stats': self.get_markdown_stats()
        }
    
    def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all tags with their link counts"""
        import json
        
        # Get all links with tags
        links_with_tags = self.session.query(Link).filter(
            Link.tag_count > 0
        ).all()
        
        # Count tags
        tag_counts = {}
        for link in links_with_tags:
            tags = link.get_tags_list()
            for tag in tags:
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Convert to list of dicts and sort by count
        tags_list = [
            {'tag': tag, 'count': count}
            for tag, count in tag_counts.items()
        ]
        tags_list.sort(key=lambda x: x['count'], reverse=True)
        
        return tags_list
    
    def get_recently_used_tags(self, limit: int = 3) -> List[str]:
        """Get recently used tags based on links that were recently updated"""
        import json
        
        # Get recently updated links with tags, ordered by most recent update
        recent_links = self.session.query(Link).filter(
            Link.tag_count > 0,
            Link.updated_at.isnot(None)
        ).order_by(desc(Link.updated_at)).limit(100).all()
        
        # Extract tags from recent links, maintaining order of appearance
        seen_tags = set()
        recent_tags = []
        
        for link in recent_links:
            tags = link.get_tags_list()
            for tag in tags:
                if tag and tag not in seen_tags:
                    seen_tags.add(tag)
                    recent_tags.append(tag)
                    if len(recent_tags) >= limit:
                        break
            if len(recent_tags) >= limit:
                break
        
        return recent_tags[:limit]


# Helper function for pagination
def paginate_query(query, page: int = 1, per_page: int = 50):
    """Paginate a query"""
    # Use distinct() if there are joins to avoid duplicate counts
    # Check if query has joins by examining the query structure
    try:
        # Try to get total count - use distinct if needed
        total = query.distinct().count()
    except Exception:
        # Fallback: if distinct fails, try without it
        total = query.count()
    
    items = query.distinct().offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if total > 0 else 0
    }
