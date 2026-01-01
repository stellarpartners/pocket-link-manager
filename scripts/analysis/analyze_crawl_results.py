#!/usr/bin/env python3
"""
Crawl Results Analysis Script
Analyzes the results from the URL crawler and provides insights.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter
# import matplotlib.pyplot as plt  # Not currently used
from datetime import datetime

class CrawlAnalyzer:
    def __init__(self, csv_path="data/pocket_merged_crawled.csv"):
        self.csv_path = csv_path
        self.df = None
        
    def load_data(self):
        """Load the crawled data"""
        try:
            self.df = pd.read_csv(self.csv_path)
            print(f"✅ Loaded {len(self.df)} records from {self.csv_path}")
            return True
        except FileNotFoundError:
            print(f"❌ File not found: {self.csv_path}")
            print("Run the crawler first: python scripts/crawler/url_crawler.py")
            return False
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def basic_statistics(self):
        """Print basic crawling statistics"""
        if self.df is None:
            return
        
        print("\n" + "="*60)
        print("📊 CRAWL RESULTS OVERVIEW")
        print("="*60)
        
        total = len(self.df)
        crawled = self.df['crawl_final_url'].notna().sum()
        
        print(f"Total URLs: {total:,}")
        print(f"Successfully crawled: {crawled:,} ({crawled/total*100:.1f}%)")
        print(f"Not yet crawled: {total-crawled:,}")
        
        if crawled == 0:
            print("\nNo URLs have been crawled yet.")
            return
        
        # Status code analysis
        crawled_df = self.df[self.df['crawl_final_url'].notna()]
        
        print(f"\n📈 STATUS CODE BREAKDOWN:")
        status_counts = crawled_df['crawl_status_code'].value_counts().sort_index()
        for status, count in status_counts.items():
            percentage = (count / crawled) * 100
            status_name = self.get_status_name(status)
            print(f"  {status} ({status_name}): {count:,} ({percentage:.1f}%)")
        
        # Error analysis
        print(f"\n🚨 ERROR ANALYSIS:")
        error_counts = crawled_df['crawl_error_type'].value_counts()
        if error_counts.empty or error_counts.isna().all():
            print("  No errors recorded!")
        else:
            for error, count in error_counts.items():
                if pd.notna(error):
                    percentage = (count / crawled) * 100
                    print(f"  {error}: {count:,} ({percentage:.1f}%)")
        
        # Redirect analysis
        print(f"\n🔄 REDIRECT ANALYSIS:")
        redirected = crawled_df[crawled_df['crawl_redirect_count'] > 0]
        print(f"  URLs with redirects: {len(redirected):,} ({len(redirected)/crawled*100:.1f}%)")
        
        if len(redirected) > 0:
            avg_redirects = redirected['crawl_redirect_count'].mean()
            max_redirects = redirected['crawl_redirect_count'].max()
            print(f"  Average redirects: {avg_redirects:.1f}")
            print(f"  Maximum redirects: {max_redirects}")
        
        # Response time analysis
        print(f"\n⏱️ RESPONSE TIME ANALYSIS:")
        response_times = crawled_df['crawl_response_time'].dropna()
        if len(response_times) > 0:
            print(f"  Average response time: {response_times.mean():.2f}s")
            print(f"  Median response time: {response_times.median():.2f}s")
            print(f"  Fastest response: {response_times.min():.2f}s")
            print(f"  Slowest response: {response_times.max():.2f}s")
    
    def get_status_name(self, status_code):
        """Get human-readable status code names"""
        status_names = {
            200: "OK",
            301: "Moved Permanently",
            302: "Found",
            403: "Forbidden",
            404: "Not Found",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout"
        }
        return status_names.get(status_code, "Unknown")
    
    def domain_analysis(self):
        """Analyze results by domain"""
        if self.df is None:
            return
        
        crawled_df = self.df[self.df['crawl_final_url'].notna()]
        if len(crawled_df) == 0:
            return
        
        print(f"\n🌐 DOMAIN ANALYSIS:")
        print("-" * 40)
        
        # Success rate by domain (top 10)
        domain_stats = crawled_df.groupby('domain').agg({
            'crawl_status_code': ['count', lambda x: (x == 200).sum()],
            'crawl_redirect_count': 'mean'
        }).round(2)
        
        domain_stats.columns = ['Total', 'Successful', 'Avg_Redirects']
        domain_stats['Success_Rate'] = (domain_stats['Successful'] / domain_stats['Total'] * 100).round(1)
        
        # Filter domains with at least 5 URLs
        domain_stats = domain_stats[domain_stats['Total'] >= 5]
        domain_stats = domain_stats.sort_values('Total', ascending=False).head(10)
        
        print("Top domains by volume (min 5 URLs):")
        print(f"{'Domain':<25} {'Total':<8} {'Success':<8} {'Rate %':<8} {'Avg Redirects'}")
        print("-" * 65)
        
        for domain, row in domain_stats.iterrows():
            print(f"{domain[:24]:<25} {row['Total']:<8} {row['Successful']:<8} {row['Success_Rate']:<8} {row['Avg_Redirects']}")
    
    def redirect_analysis(self):
        """Analyze redirect patterns"""
        if self.df is None:
            return
        
        crawled_df = self.df[self.df['crawl_final_url'].notna()]
        redirected_df = crawled_df[crawled_df['crawl_redirect_count'] > 0]
        
        if len(redirected_df) == 0:
            return
        
        print(f"\n🔄 REDIRECT PATTERN ANALYSIS:")
        print("-" * 40)
        
        # URLs that changed domains
        redirected_df['original_domain'] = redirected_df['url'].apply(lambda x: self.extract_domain(x))
        redirected_df['final_domain'] = redirected_df['crawl_final_url'].apply(lambda x: self.extract_domain(x))
        
        domain_changes = redirected_df[redirected_df['original_domain'] != redirected_df['final_domain']]
        
        print(f"URLs that changed domains: {len(domain_changes):,}")
        
        if len(domain_changes) > 0:
            print(f"\nMost common domain changes:")
            domain_change_patterns = domain_changes.groupby(['original_domain', 'final_domain']).size().sort_values(ascending=False).head(10)
            
            for (orig, final), count in domain_change_patterns.items():
                print(f"  {orig} → {final}: {count} URLs")
        
        # HTTP to HTTPS upgrades
        http_to_https = crawled_df[
            (crawled_df['url'].str.startswith('http://')) & 
            (crawled_df['crawl_final_url'].str.startswith('https://'))
        ]
        print(f"\nHTTP to HTTPS upgrades: {len(http_to_https):,}")
    
    def extract_domain(self, url):
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ''
    
    def error_analysis(self):
        """Detailed error analysis"""
        if self.df is None:
            return
        
        crawled_df = self.df[self.df['crawl_final_url'].notna()]
        error_df = crawled_df[crawled_df['crawl_error_type'].notna()]
        
        if len(error_df) == 0:
            return
        
        print(f"\n🚨 DETAILED ERROR ANALYSIS:")
        print("-" * 40)
        
        # Error types by domain
        error_by_domain = error_df.groupby(['domain', 'crawl_error_type']).size().reset_index(name='count')
        error_by_domain = error_by_domain.sort_values('count', ascending=False)
        
        print("Errors by domain (top 10):")
        for _, row in error_by_domain.head(10).iterrows():
            print(f"  {row['domain']}: {row['crawl_error_type']} ({row['count']} times)")
        
        # Common error messages
        print(f"\nMost common error messages:")
        if 'crawl_error_message' in error_df.columns:
            error_messages = error_df['crawl_error_message'].value_counts().head(5)
            for message, count in error_messages.items():
                if pd.notna(message):
                    print(f"  '{message[:60]}...': {count} times")
    
    def save_summary_report(self):
        """Save a comprehensive summary report"""
        if self.df is None:
            return
        
        crawled_df = self.df[self.df['crawl_final_url'].notna()]
        
        report_lines = []
        report_lines.append("POCKET URL CRAWL SUMMARY REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Source: {self.csv_path}")
        report_lines.append("")
        
        # Basic stats
        total = len(self.df)
        crawled = len(crawled_df)
        report_lines.append(f"OVERVIEW:")
        report_lines.append(f"- Total URLs: {total:,}")
        report_lines.append(f"- Successfully crawled: {crawled:,} ({crawled/total*100:.1f}%)")
        report_lines.append("")
        
        if crawled > 0:
            # Status codes
            report_lines.append("STATUS CODES:")
            status_counts = crawled_df['crawl_status_code'].value_counts().sort_index()
            for status, count in status_counts.items():
                percentage = (count / crawled) * 100
                status_name = self.get_status_name(status)
                report_lines.append(f"- {status} ({status_name}): {count:,} ({percentage:.1f}%)")
            report_lines.append("")
            
            # Redirects
            redirected = crawled_df[crawled_df['crawl_redirect_count'] > 0]
            report_lines.append("REDIRECTS:")
            report_lines.append(f"- URLs with redirects: {len(redirected):,} ({len(redirected)/crawled*100:.1f}%)")
            if len(redirected) > 0:
                report_lines.append(f"- Average redirects: {redirected['crawl_redirect_count'].mean():.1f}")
            report_lines.append("")
            
            # Response times
            response_times = crawled_df['crawl_response_time'].dropna()
            if len(response_times) > 0:
                report_lines.append("RESPONSE TIMES:")
                report_lines.append(f"- Average: {response_times.mean():.2f}s")
                report_lines.append(f"- Median: {response_times.median():.2f}s")
                report_lines.append(f"- Range: {response_times.min():.2f}s - {response_times.max():.2f}s")
        
        # Save report
        report_file = "data/crawl_summary_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"\n📄 Summary report saved to: {report_file}")
        
        return report_file
    
    def run_full_analysis(self):
        """Run complete analysis"""
        if not self.load_data():
            return
        
        self.basic_statistics()
        self.domain_analysis()
        self.redirect_analysis()
        self.error_analysis()
        self.save_summary_report()
        
        print(f"\n✅ Analysis complete!")

def main():
    print("🔍 CRAWL RESULTS ANALYZER")
    print("="*50)
    
    # Check if crawled file exists
    crawled_file = "data/pocket_merged_crawled.csv"
    if not Path(crawled_file).exists():
        print(f"❌ Crawled data file not found: {crawled_file}")
        print("\nRun the crawler first:")
        print("  python scripts/crawler/url_crawler.py")
        return
    
    analyzer = CrawlAnalyzer(crawled_file)
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()
