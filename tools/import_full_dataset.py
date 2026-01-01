"""
Import the full Pocket dataset into the database
"""

import logging
from pathlib import Path
from database.importer import import_csv_to_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    csv_file = Path("data/pocket_merged_crawled.csv")
    
    if not csv_file.exists():
        print(f"Error: CSV file not found: {csv_file}")
        return
    
    print("\n" + "="*60)
    print("IMPORTING FULL POCKET DATASET")
    print("="*60)
    print(f"Source: {csv_file}")
    print(f"Expected rows: ~22,745")
    print("\nThis may take a few minutes...")
    print("="*60 + "\n")
    
    try:
        stats = import_csv_to_database(
            csv_file,
            batch_size=1000,  # Process in batches of 1000
            skip_existing=True  # Skip if already imported
        )
        
        print("\n" + "="*60)
        print("IMPORT COMPLETE!")
        print("="*60)
        print(f"Total rows processed: {stats['total']:,}")
        print(f"Successfully imported: {stats['imported']:,}")
        print(f"Skipped (already exists): {stats['skipped']:,}")
        print(f"Errors: {stats['errors']:,}")
        print(f"Crawl results imported: {stats['crawl_results']:,}")
        print(f"Quality metrics created: {stats['quality_metrics']:,}")
        
        if stats['errors'] > 0:
            print(f"\n⚠️  Warning: {stats['errors']} errors occurred during import")
        else:
            print("\n✓ All records imported successfully!")
        
    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
