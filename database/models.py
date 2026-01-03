"""
SQLAlchemy models for Pocket Link Management System
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, REAL, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
import json
from pathlib import Path

Base = declarative_base()


class Link(Base):
    """Main table storing Pocket links"""
    __tablename__ = 'links'
    
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    original_url = Column(Text, unique=True, nullable=False, index=True)
    domain = Column(Text, index=True)
    pocket_status = Column(String(20))  # 'unread' or 'archive'
    date_saved = Column(DateTime)
    time_added = Column(Integer)  # Unix timestamp
    tags = Column(Text)  # JSON array as string
    tag_count = Column(Integer, default=0)
    highlights = Column(Text)  # JSON array as string
    highlight_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    crawl_results = relationship("CrawlResult", back_populates="link", cascade="all, delete-orphan")
    content_extractions = relationship("ContentExtraction", back_populates="link", cascade="all, delete-orphan")
    markdown_files = relationship("MarkdownFile", back_populates="link", cascade="all, delete-orphan")
    quality_metric = relationship("QualityMetric", back_populates="link", uselist=False, cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_domain_status', 'domain', 'pocket_status'),
        Index('idx_date_saved', 'date_saved'),
    )
    
    def get_tags_list(self):
        """Parse tags JSON string to list"""
        if not self.tags:
            return []
        try:
            return json.loads(self.tags) if isinstance(self.tags, str) else self.tags
        except:
            return []
    
    def set_tags_list(self, tags_list):
        """Convert list of tags to JSON string and update tag_count"""
        if not tags_list:
            self.tags = "[]"
            self.tag_count = 0
        else:
            # Clean and deduplicate tags
            cleaned_tags = sorted(list(set([str(t).strip() for t in tags_list if t])))
            self.tags = json.dumps(cleaned_tags)
            self.tag_count = len(cleaned_tags)
    
    def get_highlights_list(self):
        """Parse highlights JSON string to list"""
        if not self.highlights:
            return []
        try:
            return json.loads(self.highlights) if isinstance(self.highlights, str) else self.highlights
        except:
            return []
    
    def latest_crawl(self):
        """Get the most recent crawl result"""
        if self.crawl_results:
            return max(self.crawl_results, key=lambda x: x.crawl_date or datetime.min)
        return None
    
    def latest_content(self):
        """Get the most recent content extraction"""
        if self.content_extractions:
            return max(self.content_extractions, key=lambda x: x.extraction_date or datetime.min)
        return None
    
    def __repr__(self):
        return f"<Link(id={self.id}, title='{self.title[:50]}...', url='{self.original_url[:50]}...')>"


class CrawlResult(Base):
    """Crawl results for each link"""
    __tablename__ = 'crawl_results'
    
    id = Column(Integer, primary_key=True)
    link_id = Column(Integer, ForeignKey('links.id'), nullable=False, index=True)
    final_url = Column(Text)
    status_code = Column(Integer, index=True)
    redirect_count = Column(Integer, default=0)
    response_time = Column(REAL)
    error_type = Column(String(50))
    error_message = Column(Text)
    crawl_date = Column(DateTime, default=datetime.utcnow, index=True)
    crawl_attempt = Column(Integer, default=1)
    crawl_method = Column(String(20))  # 'http' or 'browser'
    browser_wait_time = Column(Integer)  # Wait time used for browser crawl (seconds)
    batch_crawl_date = Column(DateTime)  # When batch crawl was performed
    
    # Relationship
    link = relationship("Link", back_populates="crawl_results")
    
    __table_args__ = (
        Index('idx_link_crawl_date', 'link_id', 'crawl_date'),
    )
    
    def is_successful(self):
        """Check if crawl was successful (status 200)"""
        return self.status_code == 200
    
    def __repr__(self):
        return f"<CrawlResult(id={self.id}, link_id={self.link_id}, status={self.status_code})>"


class ContentExtraction(Base):
    """Extracted content from links"""
    __tablename__ = 'content_extractions'
    
    id = Column(Integer, primary_key=True)
    link_id = Column(Integer, ForeignKey('links.id'), nullable=False, index=True)
    extraction_method = Column(String(50))  # 'readability', 'trafilatura', etc.
    title = Column(Text)
    content = Column(Text)  # Full article content
    excerpt = Column(Text)  # Short summary
    author = Column(Text)
    published_date = Column(DateTime)
    extraction_date = Column(DateTime, default=datetime.utcnow, index=True)
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    markdown_content = Column(Text)  # Markdown version of the content
    markdown_file_path = Column(Text)  # Path to saved markdown file
    
    # Relationship
    link = relationship("Link", back_populates="content_extractions")
    
    __table_args__ = (
        Index('idx_link_extraction_date', 'link_id', 'extraction_date'),
    )
    
    def __repr__(self):
        return f"<ContentExtraction(id={self.id}, link_id={self.link_id}, success={self.success})>"


class MarkdownFile(Base):
    """Generated markdown files for Obsidian"""
    __tablename__ = 'markdown_files'
    
    id = Column(Integer, primary_key=True)
    link_id = Column(Integer, ForeignKey('links.id'), nullable=False, index=True)
    file_path = Column(Text, unique=True)
    generation_date = Column(DateTime, default=datetime.utcnow)
    include_content = Column(Boolean, default=False)
    obsidian_vault_path = Column(Text)
    
    # Relationship
    link = relationship("Link", back_populates="markdown_files")
    
    def __repr__(self):
        return f"<MarkdownFile(id={self.id}, link_id={self.link_id}, path='{self.file_path}')>"


class QualityMetric(Base):
    """Computed quality metrics for links (denormalized for performance)"""
    __tablename__ = 'quality_metrics'
    
    link_id = Column(Integer, ForeignKey('links.id'), primary_key=True)
    is_accessible = Column(Boolean, default=False)
    has_redirects = Column(Boolean, default=False)
    has_content = Column(Boolean, default=False)
    has_markdown = Column(Boolean, default=False)
    quality_score = Column(Integer, default=0)  # 0-100
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    link = relationship("Link", back_populates="quality_metric")
    
    def __repr__(self):
        return f"<QualityMetric(link_id={self.link_id}, score={self.quality_score})>"


# Database setup
def get_db_path():
    """Get the database file path"""
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)
    return str(data_dir / 'pocket_links.db')


def create_engine_instance(db_path=None):
    """Create SQLAlchemy engine"""
    if db_path is None:
        db_path = get_db_path()
    
    # SQLite-specific optimizations
    engine = create_engine(
        f'sqlite:///{db_path}',
        connect_args={'check_same_thread': False},  # For multi-threading
        echo=False  # Set to True for SQL debugging
    )
    return engine


def create_session(engine=None):
    """Create a database session"""
    if engine is None:
        engine = create_engine_instance()
    Session = sessionmaker(bind=engine)
    return Session()


# Global engine and session factory
_engine = None
_session_factory = None


def init_db_engine():
    """Initialize the global database engine"""
    global _engine, _session_factory
    if _engine is None:
        _engine = create_engine_instance()
        _session_factory = sessionmaker(bind=_engine)
    return _engine


def get_session():
    """Get a database session"""
    if _engine is None:
        init_db_engine()
    return _session_factory()


# For Flask-SQLAlchemy compatibility
class Database:
    """Database wrapper for Flask integration"""
    def __init__(self):
        self.engine = None
        self.Session = None
    
    def init_app(self, app):
        """Initialize database for Flask app"""
        db_path = app.config.get('DATABASE_PATH', get_db_path())
        self.engine = create_engine_instance(db_path)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get a database session"""
        return self.Session()


# Create global db instance for Flask
db = Database()
