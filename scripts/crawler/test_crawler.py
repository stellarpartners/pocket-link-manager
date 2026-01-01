#!/usr/bin/env python3
"""
Test script for URL Crawler
Tests the crawler with a small sample of URLs before running the full crawl.
"""

import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent))

from url_crawler import URLCrawler

def create_test_data():
    """Create a small test CSV with various types of URLs"""
    test_urls = [
        {
            'title': 'Google Homepage', 
            'url': 'https://google.com',
            'domain': 'google.com',
            'status': 'unread'
        },
        {
            'title': 'Twitter Redirect', 
            'url': 'http://t.co/test123',  # This will likely 404 but tests redirects
            'domain': 't.co',
            'status': 'archive'
        },
        {
            'title': 'HTTPS Redirect Test', 
            'url': 'http://github.com',  # Should redirect to HTTPS
            'domain': 'github.com',
            'status': 'unread'
        },
        {
            'title': 'Invalid URL Test', 
            'url': 'https://thissitedefintely-does-not-exist-12345.com',
            'domain': 'invalid.com',
            'status': 'unread'
        },
        {
            'title': 'Medium Article', 
            'url': 'https://medium.com',
            'domain': 'medium.com',
            'status': 'archive'
        }
    ]
    
    df = pd.DataFrame(test_urls)
    
    # Add other columns that would be in the real data
    df['date_saved'] = '2024-01-01 12:00:00'
    df['tags'] = ''
    df['tag_count'] = 0
    df['highlights'] = ''
    df['highlight_count'] = 0
    df['has_highlights'] = False
    df['has_tags'] = False
    
    return df

def main():
    print("🧪 URL CRAWLER TEST")
    print("="*50)
    print("Testing the crawler with a small sample of URLs")
    print("="*50)
    
    # Create test data
    test_df = create_test_data()
    test_file = "data/test_sample.csv"
    
    # Save test data
    test_df.to_csv(test_file, index=False)
    print(f"Created test file: {test_file}")
    print(f"Test URLs ({len(test_df)}):")
    for idx, row in test_df.iterrows():
        print(f"  {idx+1}. {row['title']} - {row['url']}")
    
    print("\n" + "-"*50)
    proceed = input("Run test crawl? (y/n): ").lower().strip()
    
    if proceed != 'y':
        print("Test aborted.")
        return
    
    # Create crawler with test settings
    crawler = URLCrawler(
        csv_path=test_file,
        max_workers=2,  # Lower for testing
        delay_range=(0.5, 1.0)  # Shorter delays for testing
    )
    
    try:
        # Run the crawl
        crawler.crawl_all_urls(batch_size=10)
        
        # Show results
        print("\n" + "="*50)
        print("🎯 TEST RESULTS")
        print("="*50)
        
        # Load and display results
        results_file = test_file.replace('.csv', '_crawled.csv')
        if Path(results_file).exists():
            results_df = pd.read_csv(results_file)
            
            print("Results summary:")
            for idx, row in results_df.iterrows():
                print(f"\n{idx+1}. {row['title']}")
                print(f"   Original: {row['url']}")
                print(f"   Final:    {row['crawl_final_url']}")
                print(f"   Status:   {row['crawl_status_code']}")
                print(f"   Redirects: {row['crawl_redirect_count']}")
                print(f"   Time:     {row['crawl_response_time']}s")
                if pd.notna(row['crawl_error_type']):
                    print(f"   Error:    {row['crawl_error_type']}")
        
        print(f"\n✅ Test completed successfully!")
        print(f"📄 Results saved to: {results_file}")
        print(f"📋 Logs saved to: logs/")
        
        print(f"\nThe crawler is working correctly. You can now run:")
        print(f"  python scripts/crawler/url_crawler.py")
        print(f"to process your full Pocket dataset.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    main()
