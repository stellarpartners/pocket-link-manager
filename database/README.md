# Database Module

Database layer for the Pocket Link Management System using SQLAlchemy.

## Overview

This module provides database models, queries, and import functionality for managing Pocket links, crawl results, content extractions, and quality metrics.

## Components

### Models (`models.py`)

SQLAlchemy ORM models:

- **Link** - Main table storing Pocket links with metadata (title, URL, domain, status, tags, highlights)
- **CrawlResult** - Stores URL crawling results (final URL, status codes, redirects, response times)
- **ContentExtraction** - Stores extracted content from URLs
- **MarkdownFile** - Tracks generated markdown files
- **QualityMetric** - Quality scores and accessibility metrics for links

### Queries (`queries.py`)

Query classes for database operations:

- **LinkQuery** - Search and filter links
- **StatisticsQuery** - Aggregate statistics and analytics

### Importer (`importer.py`)

CSV import functionality:

- **import_csv_to_database()** - Import Pocket data from CSV files
- Batch processing with progress tracking
- Automatic creation of related records (crawl results, quality metrics)

### Database Initialization (`init_db.py`)

- **init_database()** - Initialize database schema
- **get_database_info()** - Get database metadata

### Migrations (`migrate_add_markdown_fields.py`)

Database migration scripts for schema updates.

## Usage

```python
from database.models import create_session, Link
from database.queries import LinkQuery, StatisticsQuery

# Create session
session = create_session()

# Query links
link_query = LinkQuery()
links = link_query.search("python", limit=10)

# Get statistics
stats_query = StatisticsQuery()
total = stats_query.get_total_count()

session.close()
```

## Database Schema

The database uses SQLite by default (stored in `data/pocket_links.db`). All models include proper indexes for common query patterns.
