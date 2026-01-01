"""
Test script for database initialization and import
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_database_init():
    """Test database initialization"""
    print("\n" + "="*60)
    print("TEST 1: Database Initialization")
    print("="*60)
    
    try:
        from database.init_db import init_database, get_database_info
        
        # Initialize database
        print("Initializing database...")
        engine = init_database()
        print("✓ Database initialized successfully")
        
        # Get database info
        info = get_database_info()
        print(f"\nDatabase Info:")
        print(f"  Path: {info['path']}")
        print(f"  Exists: {info['exists']}")
        print(f"  Size: {info['size_mb']} MB")
        
        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_models():
    """Test database models"""
    print("\n" + "="*60)
    print("TEST 2: Database Models")
    print("="*60)
    
    try:
        from database.models import (
            Link, CrawlResult, ContentExtraction, 
            MarkdownFile, QualityMetric, create_session
        )
        
        session = create_session()
        
        # Test creating a sample link
        print("Creating test link...")
        test_link = Link(
            title="Test Article",
            original_url="https://example.com/test",
            domain="example.com",
            pocket_status="unread",
            tag_count=0,
            highlight_count=0
        )
        session.add(test_link)
        session.flush()
        print(f"✓ Test link created with ID: {test_link.id}")
        
        # Test creating crawl result
        print("Creating test crawl result...")
        crawl_result = CrawlResult(
            link_id=test_link.id,
            final_url="https://example.com/test",
            status_code=200,
            redirect_count=0,
            response_time=1.5
        )
        session.add(crawl_result)
        session.flush()
        print(f"✓ Crawl result created with ID: {crawl_result.id}")
        
        # Test creating quality metric
        print("Creating test quality metric...")
        quality_metric = QualityMetric(
            link_id=test_link.id,
            is_accessible=True,
            has_redirects=False,
            quality_score=80
        )
        session.add(quality_metric)
        session.commit()
        print("✓ Quality metric created")
        
        # Test querying
        print("\nTesting queries...")
        link_count = session.query(Link).count()
        print(f"✓ Total links in database: {link_count}")
        
        # Clean up test data
        print("\nCleaning up test data...")
        session.delete(test_link)  # Cascade will delete related records
        session.commit()
        print("✓ Test data cleaned up")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_queries():
    """Test query functions"""
    print("\n" + "="*60)
    print("TEST 3: Query Functions")
    print("="*60)
    
    try:
        from database.queries import LinkQuery, StatisticsQuery
        
        link_query = LinkQuery()
        stats_query = StatisticsQuery()
        
        # Test basic queries
        print("Testing basic queries...")
        total = stats_query.get_total_count()
        print(f"✓ Total links: {total}")
        
        pocket_status = stats_query.get_pocket_status_breakdown()
        print(f"✓ Pocket status breakdown: {pocket_status}")
        
        print("✓ Query functions working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_small_import():
    """Test importing a small sample from CSV"""
    print("\n" + "="*60)
    print("TEST 4: Small CSV Import")
    print("="*60)
    
    csv_path = Path("data/pocket_merged_crawled.csv")
    
    if not csv_path.exists():
        print(f"✗ CSV file not found: {csv_path}")
        return False
    
    try:
        import pandas as pd
        from database.importer import import_csv_to_database
        
        # Create a small test CSV (first 10 rows)
        print("Creating test CSV sample (10 rows)...")
        df = pd.read_csv(csv_path, nrows=10)
        test_csv = Path("data/test_sample_import.csv")
        df.to_csv(test_csv, index=False)
        print(f"✓ Test CSV created: {test_csv}")
        
        # Import the test CSV
        print("\nImporting test CSV...")
        stats = import_csv_to_database(test_csv, batch_size=5)
        
        print("\nImport Statistics:")
        print(f"  Total rows processed: {stats['total']:,}")
        print(f"  Successfully imported: {stats['imported']:,}")
        print(f"  Skipped: {stats['skipped']:,}")
        print(f"  Errors: {stats['errors']:,}")
        print(f"  Crawl results: {stats['crawl_results']:,}")
        print(f"  Quality metrics: {stats['quality_metrics']:,}")
        
        # Verify import
        from database.queries import StatisticsQuery
        stats_query = StatisticsQuery()
        total = stats_query.get_total_count()
        print(f"\n✓ Total links in database after import: {total}")
        
        # Clean up test CSV
        test_csv.unlink()
        print(f"✓ Test CSV cleaned up")
        
        return stats['errors'] == 0
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("POCKET LINK DATABASE - INITIAL TESTS")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Database Initialization", test_database_init()))
    results.append(("Database Models", test_models()))
    results.append(("Query Functions", test_queries()))
    results.append(("Small CSV Import", test_small_import()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Database is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
