#!/usr/bin/env python3
"""
Migration script to add browser crawl fields to CrawlResult table
"""

import sys
import sqlite3
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import get_db_path

def migrate():
    """Add crawl_method, browser_wait_time, and batch_crawl_date columns to crawl_results table"""
    db_path = get_db_path()
    
    if not Path(db_path).exists():
        print(f"Database not found at {db_path}")
        print("Creating new database with all tables...")
        from database.init_db import init_database
        init_database()
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(crawl_results)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'crawl_method' not in columns:
            print("Adding crawl_method column...")
            cursor.execute("ALTER TABLE crawl_results ADD COLUMN crawl_method VARCHAR(20)")
            print("[OK] Added crawl_method column")
        else:
            print("[OK] crawl_method column already exists")
        
        if 'browser_wait_time' not in columns:
            print("Adding browser_wait_time column...")
            cursor.execute("ALTER TABLE crawl_results ADD COLUMN browser_wait_time INTEGER")
            print("[OK] Added browser_wait_time column")
        else:
            print("[OK] browser_wait_time column already exists")
        
        if 'batch_crawl_date' not in columns:
            print("Adding batch_crawl_date column...")
            cursor.execute("ALTER TABLE crawl_results ADD COLUMN batch_crawl_date DATETIME")
            print("[OK] Added batch_crawl_date column")
        else:
            print("[OK] batch_crawl_date column already exists")
        
        conn.commit()
        print("\nMigration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
