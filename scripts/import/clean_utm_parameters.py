#!/usr/bin/env python3
"""
Clean UTM Parameters from Database
Removes all utm_* parameters from final_url fields in the CrawlResult table.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from database.models import create_session, CrawlResult
from extractor.url_utils import remove_utm_parameters
from sqlalchemy import func
import re


def find_utm_parameters(url):
    """Check if URL contains UTM parameters"""
    if not url:
        return False
    # Check for utm_ parameters in the URL
    return bool(re.search(r'[?&]utm_', url, re.IGNORECASE))


def clean_all_utm_parameters(dry_run=True, batch_size=100, skip_confirm=False):
    """
    Clean all UTM parameters from final_url fields in CrawlResult table.
    
    Args:
        dry_run: If True, only show what would be changed without updating
        batch_size: Number of records to process at a time
        skip_confirm: If True, skip confirmation prompt (for non-interactive use)
    """
    session = create_session()
    
    try:
        # Get all crawl results with final_url
        all_results = session.query(CrawlResult).filter(
            CrawlResult.final_url.isnot(None)
        ).all()
        
        total_count = len(all_results)
        print(f"\n[INFO] Found {total_count:,} crawl results with final_url")
        
        # Find URLs with UTM parameters
        urls_with_utm = [
            r for r in all_results 
            if r.final_url and find_utm_parameters(r.final_url)
        ]
        
        utm_count = len(urls_with_utm)
        print(f"[INFO] Found {utm_count:,} URLs with UTM parameters ({utm_count/total_count*100:.1f}%)")
        
        if utm_count == 0:
            print("\n[SUCCESS] No URLs with UTM parameters found. Database is clean!")
            return
        
        # Show some examples
        print("\n[EXAMPLES] URLs with UTM parameters:")
        for i, result in enumerate(urls_with_utm[:5], 1):
            cleaned = remove_utm_parameters(result.final_url)
            print(f"\n  {i}. Link ID: {result.link_id}")
            print(f"     Original: {result.final_url[:100]}...")
            print(f"     Cleaned:  {cleaned[:100]}...")
        
        if len(urls_with_utm) > 5:
            print(f"\n     ... and {len(urls_with_utm) - 5} more")
        
        if dry_run:
            print("\n[DRY-RUN] DRY RUN MODE - No changes will be made")
            print(f"   Would clean {utm_count:,} URLs")
            return
        
        # Confirm before proceeding
        if not skip_confirm:
            print(f"\n[WARNING] This will update {utm_count:,} URLs in the database")
            try:
                response = input("Continue? (yes/no): ").strip().lower()
                if response != 'yes':
                    print("[ABORT] Aborted by user")
                    return
            except (EOFError, KeyboardInterrupt):
                print("\n[ABORT] Aborted (no input available)")
                return
        else:
            print(f"\n[INFO] Will update {utm_count:,} URLs in the database (--yes flag set)")
        
        # Process in batches
        print(f"\n[PROCESSING] Processing {utm_count:,} URLs in batches of {batch_size}...")
        updated_count = 0
        unchanged_count = 0
        
        for i in range(0, len(urls_with_utm), batch_size):
            batch = urls_with_utm[i:i + batch_size]
            
            for result in batch:
                original_url = result.final_url
                cleaned_url = remove_utm_parameters(original_url)
                
                if cleaned_url != original_url:
                    result.final_url = cleaned_url
                    updated_count += 1
                else:
                    unchanged_count += 1
            
            # Commit batch
            session.commit()
            
            # Progress indicator
            processed = min(i + batch_size, len(urls_with_utm))
            print(f"  [PROGRESS] Processed {processed:,}/{utm_count:,} URLs ({processed/utm_count*100:.1f}%)")
        
        print(f"\n[SUCCESS] Cleanup complete!")
        print(f"   Updated: {updated_count:,} URLs")
        print(f"   Unchanged: {unchanged_count:,} URLs")
        print(f"   Total processed: {utm_count:,} URLs")
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


def main():
    """Main entry point"""
    print("=" * 70)
    print("UTM PARAMETER CLEANUP SCRIPT")
    print("=" * 70)
    print("\nThis script will remove all utm_* parameters from final_url fields")
    print("in the CrawlResult table.")
    
    # Check for command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Clean UTM parameters from database URLs')
    parser.add_argument('--execute', action='store_true', 
                       help='Actually update the database (default is dry-run)')
    parser.add_argument('--yes', action='store_true',
                       help='Skip confirmation prompt (use with --execute)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of records to process per batch (default: 100)')
    
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    if dry_run:
        print("\n[DRY-RUN] Running in DRY-RUN mode (no changes will be made)")
        print("   Use --execute flag to actually update the database")
    else:
        print("\n[EXECUTE] EXECUTE MODE - Database will be updated!")
        if args.yes:
            print("   [INFO] --yes flag set, will skip confirmation")
    
    print()
    
    clean_all_utm_parameters(dry_run=dry_run, batch_size=args.batch_size, skip_confirm=args.yes)


if __name__ == "__main__":
    main()
