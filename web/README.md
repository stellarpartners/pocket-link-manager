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

- `/` - Dashboard with statistics
- `/links` - Links listing with filtering and pagination
- `/link/<id>` - Link detail page
- `/tags` - Tag browsing and statistics
- `/quality` - Quality metrics and filtering
- `/export` - Export links to CSV/Markdown

**API Routes (`/api`):**

- `/api/links` - JSON API for links
- `/api/stats` - Statistics endpoint
- `/api/link/<id>/extract` - Trigger content extraction

### Templates (`templates/`)

Jinja2 templates:

- `base.html` - Base template
- `index.html` - Dashboard
- `links.html` - Links listing
- `link_detail.html` - Link details
- `tags.html` - Tag browser
- `quality.html` - Quality metrics
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

- **Filtering**: By domain, status code, pocket status, quality score, tags
- **Search**: Full-text search across titles and URLs
- **Pagination**: Efficient handling of large datasets
- **Statistics**: Dashboard with overview metrics
- **Export**: Download filtered results as CSV or Markdown

## Configuration

Set environment variables:

- `SECRET_KEY` - Flask secret key (default: dev key)
- `DATABASE_PATH` - Custom database path (default: auto-detected)
