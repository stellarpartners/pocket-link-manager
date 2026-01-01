#!/usr/bin/env python3
"""
URL Crawler for Pocket Articles
Visits each URL from the merged CSV, follows redirects, and tracks final URLs and status codes.
Handles errors gracefully and provides comprehensive logging.
"""

import pandas as pd
import requests
import time
import logging
from datetime import datetime
from urllib.parse import urlparse, urljoin
from pathlib import Path
import json
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from extractor.url_utils import remove_utm_parameters

class URLCrawler:
    def __init__(self, csv_path="data/pocket_merged.csv", max_workers=5, delay_range=(1, 3)):
        self.csv_path = csv_path
        self.max_workers = max_workers
        self.delay_range = delay_range
        
        # Setup logging
        self.setup_logging()
        
        # Create session with retry strategy
        self.session = self.create_session()
        
        # Stats tracking
        self.stats = {
            'total_urls': 0,
            'processed': 0,
            'successful': 0,
            'redirected': 0,
            'errors_4xx': 0,
            'errors_5xx': 0,
            'timeouts': 0,
            'connection_errors': 0,
            'other_errors': 0
        }
        
    def setup_logging(self):
        """Configure logging for the crawler"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler for all logs
        file_handler = logging.FileHandler(
            log_dir / f"crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # Error file handler
        error_handler = logging.FileHandler(
            log_dir / f"crawler_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding='utf-8'
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # Setup logger
        self.logger = logging.getLogger('URLCrawler')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def create_session(self):
        """Create requests session with retry strategy and headers"""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set realistic headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session
    
    def crawl_url(self, url, index, title=""):
        """Crawl a single URL and return results"""
        result = {
            'index': index,
            'original_url': url,
            'final_url': url,
            'status_code': None,
            'redirect_count': 0,
            'response_time': None,
            'error_type': None,
            'error_message': None,
            'title': title[:50] + "..." if len(title) > 50 else title
        }
        
        start_time = time.time()
        
        try:
            # Add random delay to be respectful
            delay = random.uniform(*self.delay_range)
            time.sleep(delay)
            
            self.logger.info(f"Processing [{index}]: {url}")
            
            # Make request with timeout
            response = self.session.get(
                url, 
                timeout=(10, 30),  # (connect, read) timeout
                allow_redirects=True
            )
            
            result['final_url'] = remove_utm_parameters(response.url)
            result['status_code'] = response.status_code
            result['response_time'] = round(time.time() - start_time, 2)
            
            # Count redirects
            if hasattr(response, 'history'):
                result['redirect_count'] = len(response.history)
                if result['redirect_count'] > 0:
                    self.stats['redirected'] += 1
                    self.logger.info(f"  → Redirected {result['redirect_count']} times to: {result['final_url']}")
            
            # Check status code
            if 200 <= response.status_code < 300:
                self.stats['successful'] += 1
                self.logger.info(f"  ✅ Success: {response.status_code}")
            elif 400 <= response.status_code < 500:
                self.stats['errors_4xx'] += 1
                result['error_type'] = '4xx_client_error'
                self.logger.warning(f"  ⚠️ Client Error: {response.status_code}")
            elif 500 <= response.status_code < 600:
                self.stats['errors_5xx'] += 1
                result['error_type'] = '5xx_server_error'
                self.logger.warning(f"  ❌ Server Error: {response.status_code}")
            
        except requests.exceptions.Timeout:
            self.stats['timeouts'] += 1
            result['error_type'] = 'timeout'
            result['error_message'] = 'Request timeout'
            result['response_time'] = round(time.time() - start_time, 2)
            self.logger.error(f"  ⏰ Timeout after {result['response_time']}s: {url}")
            
        except requests.exceptions.ConnectionError as e:
            self.stats['connection_errors'] += 1
            result['error_type'] = 'connection_error'
            result['error_message'] = str(e)[:200]
            result['response_time'] = round(time.time() - start_time, 2)
            self.logger.error(f"  🔌 Connection Error: {url} - {str(e)[:100]}")
            
        except requests.exceptions.RequestException as e:
            self.stats['other_errors'] += 1
            result['error_type'] = 'request_error'
            result['error_message'] = str(e)[:200]
            result['response_time'] = round(time.time() - start_time, 2)
            self.logger.error(f"  ❓ Request Error: {url} - {str(e)[:100]}")
            
        except Exception as e:
            self.stats['other_errors'] += 1
            result['error_type'] = 'unknown_error'
            result['error_message'] = str(e)[:200]
            result['response_time'] = round(time.time() - start_time, 2)
            self.logger.error(f"  💥 Unknown Error: {url} - {str(e)[:100]}")
        
        self.stats['processed'] += 1
        return result
    
    def load_urls(self):
        """Load URLs from the merged CSV file"""
        try:
            df = pd.read_csv(self.csv_path)
            self.logger.info(f"Loaded {len(df)} URLs from {self.csv_path}")
            
            # Check if we've already processed some URLs
            if 'crawl_final_url' in df.columns:
                already_processed = df['crawl_final_url'].notna().sum()
                self.logger.info(f"Found {already_processed} already processed URLs")
                
                # Ask user if they want to skip processed URLs
                if already_processed > 0:
                    print(f"\n🔍 Found {already_processed} already processed URLs.")
                    choice = input("Skip already processed URLs? (y/n): ").lower().strip()
                    if choice == 'y':
                        df = df[df['crawl_final_url'].isna()]
                        self.logger.info(f"Skipping processed URLs. {len(df)} URLs remaining.")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading CSV: {e}")
            raise
    
    def save_results(self, df, results):
        """Save crawling results back to the CSV"""
        try:
            # Create new columns if they don't exist
            new_columns = [
                'crawl_final_url', 'crawl_status_code', 'crawl_redirect_count',
                'crawl_response_time', 'crawl_error_type', 'crawl_error_message',
                'crawl_date'
            ]
            
            for col in new_columns:
                if col not in df.columns:
                    df[col] = None
            
            # Update rows with results
            for result in results:
                idx = result['index']
                df.at[idx, 'crawl_final_url'] = result['final_url']
                df.at[idx, 'crawl_status_code'] = result['status_code']
                df.at[idx, 'crawl_redirect_count'] = result['redirect_count']
                df.at[idx, 'crawl_response_time'] = result['response_time']
                df.at[idx, 'crawl_error_type'] = result['error_type']
                df.at[idx, 'crawl_error_message'] = result['error_message']
                df.at[idx, 'crawl_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Save updated CSV
            output_path = self.csv_path.replace('.csv', '_crawled.csv')
            df.to_csv(output_path, index=False, encoding='utf-8')
            self.logger.info(f"Results saved to {output_path}")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            raise
    
    def save_progress(self, results, batch_num):
        """Save intermediate results for recovery"""
        try:
            progress_file = f"logs/crawl_progress_batch_{batch_num}.json"
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Progress saved to {progress_file}")
        except Exception as e:
            self.logger.warning(f"Could not save progress: {e}")
    
    def print_statistics(self):
        """Print crawling statistics"""
        print("\n" + "="*60)
        print("📊 CRAWLING STATISTICS")
        print("="*60)
        print(f"Total URLs: {self.stats['total_urls']:,}")
        print(f"Processed: {self.stats['processed']:,}")
        print(f"Successful (2xx): {self.stats['successful']:,}")
        print(f"Redirected: {self.stats['redirected']:,}")
        print(f"Client Errors (4xx): {self.stats['errors_4xx']:,}")
        print(f"Server Errors (5xx): {self.stats['errors_5xx']:,}")
        print(f"Timeouts: {self.stats['timeouts']:,}")
        print(f"Connection Errors: {self.stats['connection_errors']:,}")
        print(f"Other Errors: {self.stats['other_errors']:,}")
        
        if self.stats['processed'] > 0:
            success_rate = (self.stats['successful'] / self.stats['processed']) * 100
            print(f"Success Rate: {success_rate:.1f}%")
    
    def crawl_all_urls(self, batch_size=100):
        """Main method to crawl all URLs"""
        # Load URLs
        df = self.load_urls()
        
        if df.empty:
            self.logger.info("No URLs to process!")
            return
        
        self.stats['total_urls'] = len(df)
        
        print(f"\n🚀 Starting crawl of {self.stats['total_urls']:,} URLs")
        print(f"Max workers: {self.max_workers}")
        print(f"Delay range: {self.delay_range} seconds")
        print(f"Batch size: {batch_size}")
        print("-"*60)
        
        all_results = []
        
        # Process in batches to save progress
        for batch_start in range(0, len(df), batch_size):
            batch_end = min(batch_start + batch_size, len(df))
            batch_df = df.iloc[batch_start:batch_end]
            batch_num = (batch_start // batch_size) + 1
            
            print(f"\n📦 Processing batch {batch_num} (rows {batch_start+1}-{batch_end})")
            
            # Prepare batch data
            batch_data = []
            for idx, row in batch_df.iterrows():
                batch_data.append((row['url'], idx, row.get('title', '')))
            
            # Process batch with ThreadPoolExecutor
            batch_results = []
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_data = {
                    executor.submit(self.crawl_url, url, idx, title): (url, idx, title)
                    for url, idx, title in batch_data
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_data):
                    try:
                        result = future.result()
                        batch_results.append(result)
                        
                        # Progress indicator
                        if len(batch_results) % 10 == 0:
                            print(f"  Progress: {len(batch_results)}/{len(batch_data)} URLs processed")
                            
                    except Exception as e:
                        url, idx, title = future_to_data[future]
                        self.logger.error(f"Error processing {url}: {e}")
            
            all_results.extend(batch_results)
            
            # Save batch progress
            self.save_progress(batch_results, batch_num)
            
            # Print batch statistics
            print(f"  Batch {batch_num} complete: {len(batch_results)} URLs processed")
        
        # Save final results
        print("\n💾 Saving final results...")
        output_path = self.save_results(df, all_results)
        
        # Print final statistics
        self.print_statistics()
        
        print(f"\n✅ Crawling complete!")
        print(f"📄 Results saved to: {output_path}")
        print(f"📋 Logs saved to: logs/")

def main():
    print("🕸️  POCKET URL CRAWLER")
    print("="*60)
    print("This script will visit all URLs from your Pocket data,")
    print("follow redirects, and track final URLs and status codes.")
    print("="*60)
    
    # Configuration
    config = {
        'csv_path': 'data/pocket_merged.csv',
        'max_workers': 5,  # Adjust based on your internet connection
        'delay_range': (1, 3),  # Random delay between requests
        'batch_size': 100  # Save progress every N URLs
    }
    
    print(f"Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    # Ask for confirmation
    print(f"\n⚠️  This will process thousands of URLs and may take several hours.")
    proceed = input("Continue? (y/n): ").lower().strip()
    
    if proceed != 'y':
        print("Aborted.")
        return
    
    # Create and run crawler
    crawler = URLCrawler(
        csv_path=config['csv_path'],
        max_workers=config['max_workers'],
        delay_range=config['delay_range']
    )
    
    try:
        crawler.crawl_all_urls(batch_size=config['batch_size'])
    except KeyboardInterrupt:
        print("\n\n⏹️  Crawling interrupted by user")
        crawler.print_statistics()
        print("Progress has been saved. You can resume later.")
    except Exception as e:
        print(f"\n❌ Error during crawling: {e}")
        crawler.print_statistics()
        raise

if __name__ == "__main__":
    main()
