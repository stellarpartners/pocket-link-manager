# Web Module

Flask web application for browsing and managing Pocket links.

## Overview

A web interface for viewing, searching, and managing your Pocket link collection with filtering, statistics, and export capabilities.

## Components

### Application Factory (`app.py`)

- **create_app()** - Flask application factory
- Database initialization
- Blueprint registration
- Template filters and context processors

### Routes (`routes.py`)

**Main Routes:**

- `/` - Redirects to `/data-quality` (dashboard)
- `/data-quality` - Combined dashboard with statistics and data quality metrics
- `/links` - Links listing with filtering and pagination
- `/links/<id>` - Link detail page with full metadata
- `/links/add` - Add new link manually
- `/tags` - Tag browsing and statistics
- `/domains` - Domain statistics and filtering
- `/export` - Export links to CSV/Markdown
- `/sync` - Sync and refresh operations
- `/quality` - Quality metrics view (legacy, redirects to data-quality)

**Link Management Routes:**

- `/links/<id>/archive` - Archive/unarchive link (POST)
- `/links/<id>/delete` - Delete link (POST)
- `/links/<id>/add-tag` - Add tag to link (POST)
- `/links/<id>/remove-tag` - Remove tag from link (POST)
- `/links/<id>/update-final-url` - Update final URL (POST)
- `/links/<id>/update-metadata` - Update link metadata (POST)
- `/links/<id>/refresh` - Refresh link data (POST)
- `/links/<id>/convert-to-markdown` - Convert link to markdown (POST)
- `/links/bulk-action` - Bulk operations on links (POST)

**API Routes (`/api`):**

- `/api/stats` - Statistics endpoint
- `/api/links` - JSON API for links with filtering
- `/api/links/<id>` - Get single link details
- `/api/domains` - Domain statistics API
- `/api/tags` - Tag statistics API
- `/api/links/get-all-ids` - Get all link IDs
- `/api/links/bulk-refresh` - Bulk refresh links (POST)
- `/api/domains/<domain>/bulk-refresh` - Bulk refresh domain links (POST)
- `/api/convert-to-markdown` - Convert URL to markdown (POST)

### Templates (`templates/`)

Jinja2 templates:

- `base.html` - Base template
- `data_quality.html` - Combined dashboard and quality metrics view
- `links.html` - Links listing
- `link_detail.html` - Link details
- `tags.html` - Tag browser
- `export.html` - Export interface

### Static Files (`static/`)

- CSS styles (`css/style.css`)
- JavaScript (`js/main.js`)
- Assets (favicon, logos)

## Usage

```bash
# Run the web application
python run.py

# Access at http://127.0.0.1:5000
```

## Features

### Browsing & Search
- **Advanced Filtering**: By domain, status code, pocket status, quality score, tags
- **Full-Text Search**: Search across titles and URLs
- **Pagination**: Efficient handling of large datasets (configurable per-page)
- **Sorting**: Sort by date, title, domain, quality score
- **Domain View**: Browse links grouped by domain with statistics

### Link Management
- **Link Details**: View full metadata, crawl results, quality metrics
- **Manual Add**: Add new links manually
- **Bulk Operations**: Archive, delete, tag multiple links at once
- **Tag Management**: Add/remove tags, rename tags across all links
- **URL Updates**: Update final URLs and metadata
- **Refresh**: Refresh link data and crawl status

### Content & Export
- **Markdown Conversion**: Convert links to markdown files
- **Export Options**: Download filtered results as CSV or Markdown
- **Statistics Dashboard**: Overview metrics and data quality insights
- **Tag Statistics**: View tag usage and distribution

### Performance
- **Caching**: In-memory caching for frequently accessed data
- **Efficient Queries**: Optimized database queries with proper indexing
- **Batch Processing**: Support for bulk operations

## Configuration

Set environment variables:

- `SECRET_KEY` - Flask secret key (default: dev key)
- `DATABASE_PATH` - Custom database path (default: auto-detected)
