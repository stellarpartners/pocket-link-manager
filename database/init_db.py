"""
Database initialization and setup
"""

from pathlib import Path
from .models import Base, create_engine_instance, get_db_path
import logging

logger = logging.getLogger(__name__)


def init_database(db_path=None, drop_existing=False):
    """
    Initialize the database by creating all tables.
    
    Args:
        db_path: Optional path to database file. If None, uses default.
        drop_existing: If True, drops all existing tables first.
    
    Returns:
        Engine instance
    """
    if db_path is None:
        db_path = get_db_path()
    
    engine = create_engine_instance(db_path)
    
    if drop_existing:
        logger.warning(f"Dropping all tables in {db_path}")
        Base.metadata.drop_all(engine)
    
    logger.info(f"Creating tables in {db_path}")
    Base.metadata.create_all(engine)
    
    logger.info("Database initialized successfully")
    return engine


def check_database_exists(db_path=None):
    """Check if database file exists"""
    if db_path is None:
        db_path = get_db_path()
    return Path(db_path).exists()


def get_database_info(db_path=None):
    """Get information about the database"""
    if db_path is None:
        db_path = get_db_path()
    
    db_file = Path(db_path)
    if not db_file.exists():
        return {
            'exists': False,
            'path': db_path,
            'size': 0
        }
    
    return {
        'exists': True,
        'path': str(db_path),
        'size': db_file.stat().st_size,
        'size_mb': round(db_file.stat().st_size / (1024 * 1024), 2)
    }


if __name__ == '__main__':
    # Command-line interface for database initialization
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    drop = '--drop' in sys.argv
    
    print("Initializing Pocket Links database...")
    engine = init_database(drop_existing=drop)
    
    info = get_database_info()
    print(f"\nDatabase initialized:")
    print(f"  Path: {info['path']}")
    print(f"  Size: {info['size_mb']} MB")
    print("\nDatabase ready!")
