"""
Verify database contents and show statistics
"""

from database.queries import LinkQuery, StatisticsQuery
from database.models import create_session, Link, CrawlResult, QualityMetric

def main():
    print("\n" + "="*60)
    print("DATABASE VERIFICATION")
    print("="*60)
    
    session = create_session()
    stats_query = StatisticsQuery()
    
    # Basic counts
    print("\n📊 Basic Statistics:")
    print("-" * 60)
    total_links = stats_query.get_total_count()
    print(f"Total Links: {total_links:,}")
    
    # Status breakdown
    pocket_status = stats_query.get_pocket_status_breakdown()
    if pocket_status:
        print("\nPocket Status Breakdown:")
        for status, count in pocket_status.items():
            print(f"  {status}: {count:,}")
    
    # Status code breakdown
    status_codes = stats_query.get_status_code_breakdown()
    if status_codes:
        print("\nHTTP Status Code Breakdown:")
        for code, count in sorted(status_codes.items()):
            print(f"  {code}: {count:,}")
    
    # Quality distribution
    quality_dist = stats_query.get_quality_distribution()
    if quality_dist:
        print("\nQuality Score Distribution:")
        for category, count in quality_dist.items():
            print(f"  {category}: {count:,}")
    
    # Sample links
    print("\n📋 Sample Links (first 5):")
    print("-" * 60)
    links = session.query(Link).limit(5).all()
    for link in links:
        crawl = link.latest_crawl()
        quality = link.quality_metric
        
        print(f"\nID: {link.id}")
        print(f"  Title: {link.title[:60]}...")
        print(f"  URL: {link.original_url[:70]}...")
        print(f"  Domain: {link.domain}")
        print(f"  Status: {link.pocket_status}")
        if crawl:
            print(f"  Crawl Status: {crawl.status_code}")
            print(f"  Final URL: {crawl.final_url[:70] if crawl.final_url else 'N/A'}...")
        if quality:
            print(f"  Quality Score: {quality.quality_score}/100")
            print(f"  Accessible: {quality.is_accessible}")
    
    # Domain stats
    domain_stats = stats_query.get_domain_stats(limit=5)
    if domain_stats:
        print("\n🌐 Top Domains:")
        print("-" * 60)
        print(f"{'Domain':<30} {'Total':<10} {'Success Rate':<15} {'Avg Score':<10}")
        print("-" * 60)
        for stat in domain_stats:
            print(f"{stat['domain'][:29]:<30} {stat['total']:<10} {stat['success_rate']:<15} {stat['avg_quality_score']:<10}")
    
    session.close()
    
    print("\n" + "="*60)
    print("✓ Database verification complete!")
    print("="*60)

if __name__ == '__main__':
    main()
