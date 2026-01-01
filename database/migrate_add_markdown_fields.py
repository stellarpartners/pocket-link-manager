#!/usr/bin/env python3
"""
Migration script to add markdown fields to ContentExtraction table
"""

import sys
import sqlite3
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import get_db_path

def migrate():
    """Add markdown_content and markdown_file_path columns to content_extractions table"""
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
        cursor.execute("PRAGMA table_info(content_extractions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'markdown_content' not in columns:
            print("Adding markdown_content column...")
            cursor.execute("ALTER TABLE content_extractions ADD COLUMN markdown_content TEXT")
            print("[OK] Added markdown_content column")
        else:
            print("[OK] markdown_content column already exists")
        
        if 'markdown_file_path' not in columns:
            print("Adding markdown_file_path column...")
            cursor.execute("ALTER TABLE content_extractions ADD COLUMN markdown_file_path TEXT")
            print("[OK] Added markdown_file_path column")
        else:
            print("[OK] markdown_file_path column already exists")
        
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
