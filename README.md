# Pocket Link Manager

A comprehensive toolkit for extracting, crawling, processing, and managing Pocket saved articles. Transform your Pocket export into a searchable, organized knowledge base with web interface, content extraction, and export capabilities.

## 🚨 Pocket Has Shut Down - We're Here to Help

**Important Update**: As of 2025, [Pocket has been shut down](https://getpocket.com/home) by Mozilla. After careful consideration, Mozilla made the difficult decision to phase out Pocket, including the Pocket Web, Android, iOS, and macOS apps, as well as browser extensions.

### What This Means for Pocket Users

If you've been using Pocket to save articles and manage your reading list, you now need a way to:
- **Preserve your saved articles** before they're lost
- **Export your Pocket data** while you still can
- **Migrate to a new system** for managing your reading list
- **Maintain access** to your curated content collection

### How Pocket Link Manager Helps

This tool was designed specifically to help Pocket users transition smoothly:

1. **Export Your Data**: Import your Pocket export CSV files into a local, self-hosted database
2. **Preserve Your Collection**: Keep all your saved links, tags, and metadata safe and accessible
3. **Crawl & Verify**: Automatically check which links still work and track redirects
4. **Search & Organize**: Browse and search your entire collection with advanced filtering
5. **Export Anywhere**: Convert your Pocket data to CSV, JSON, or Markdown for use in other tools
6. **Obsidian Integration**: Generate Obsidian-ready markdown files for knowledge management
7. **Self-Hosted**: Your data stays on your machine - no cloud dependencies

### Quick Migration Steps

1. **Export from Pocket** (if still available) - Download your Pocket data export
2. **Import to Pocket Link Manager** - Use our import tools to bring your data in
3. **Crawl & Verify** - Check which links are still accessible
4. **Organize & Export** - Use the web interface to organize and export to your preferred format

**Your Pocket data is valuable** - don't let it disappear. This tool helps you take control of your reading list and preserve your curated content collection.

---

## Features

### 🔍 **Web Interface**
- Browse and search your Pocket links with advanced filtering
- View statistics and quality metrics
- Export links to CSV or Markdown
- Tag browsing and management
- Link detail pages with full metadata

### 📊 **Data Management**
- Import Pocket exports (CSV) into SQLite database
- Track crawl results, redirects, and status codes
- Quality metrics and accessibility tracking
- Content extraction and markdown conversion
- UTM parameter cleaning

### 🕷️ **Crawling & Extraction**
- Automated URL crawling with redirect following
- Content extraction using multiple methods (trafilatura, readability)
- Convert web pages to clean markdown
- Extract metadata (title, author, published date)
- Browser-based crawling with Playwright support

### 📝 **Export & Integration**
- Export to CSV, JSON, or Markdown formats
- Obsidian-ready markdown generation
- Batch processing capabilities
- Custom filtering and search

## Requirements

- **Python**: 3.12+ (3.13+ recommended)
- **Database**: SQLite (included)
- **Browser**: For crawler scripts (Playwright)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pocket-link-manager
   ```

2. **Install dependencies**
   ```bash
   pip install -e .
   ```

   Or install with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Initialize the database**
   ```bash
   python -c "from database.init_db import init_database; init_database()"
   ```

## Quick Start

### 0. Export Your Pocket Data (If Still Available)

**Important**: If you haven't already exported your Pocket data, try to do so immediately. Pocket has been shut down, but export functionality may still be temporarily available.

**If you already have a Pocket export**: Skip this step and proceed to importing your CSV file.

**If you need to export from Pocket** (if still accessible):
1. Visit [getpocket.com](https://getpocket.com) and try to log in
2. Navigate to your account settings
3. Look for the export/download option
4. Download your Pocket data as CSV

**Note**: If Pocket export is no longer available, you may need to use any previously downloaded exports or contact Mozilla support for assistance with data recovery.

### 1. Import Your Pocket Data

Import your Pocket export CSV file:

```bash
python tools/import_full_dataset.py
```

Or use the import script:
```bash
python scripts/import/pocket_merge_script.py
```

### 2. Run the Web Interface

Start the Flask web application:

```bash
python run.py
```

Access the interface at `http://127.0.0.1:5000`

### 3. Browse and Manage Links

- **Dashboard**: View statistics and data quality metrics (`/data-quality`)
- **Links**: Browse all links with filtering (`/links`)
- **Tags**: Explore tags and tagged articles (`/tags`)
- **Export**: Export filtered results (`/export`)

## Project Structure

```
pocket-link-manager/
├── database/          # Database models, queries, and import functionality
├── extractor/         # Content extraction and URL processing
├── web/               # Flask web application
│   ├── app.py        # Application factory
│   ├── routes.py     # Route handlers
│   ├── templates/    # Jinja2 templates
│   └── static/       # CSS, JS, assets
├── scripts/           # Utility scripts
│   ├── crawler/      # URL crawling scripts
│   ├── analysis/     # Data analysis tools
│   ├── import/       # Data import scripts
│   └── utils/        # Utility scripts
├── tools/             # Root-level utility tools
├── tests/             # Test suite
├── docs/              # Documentation
└── data/              # Data files and database
```

## Usage Examples

### Web Interface

```bash
# Start the web server
python run.py

# Access different pages:
# - http://127.0.0.1:5000/data-quality  (Dashboard)
# - http://127.0.0.1:5000/links         (Browse links)
# - http://127.0.0.1:5000/tags          (Tag browser)
# - http://127.0.0.1:5000/export        (Export interface)
```

### Content Extraction

```python
from extractor.url_to_markdown import URLToMarkdownConverter

converter = URLToMarkdownConverter()
result = converter.convert("https://example.com/article")

if result['success']:
    print(result['markdown'])
    print(f"Title: {result['title']}")
```

### Database Queries

```python
from database.models import create_session
from database.queries import LinkQuery, StatisticsQuery

session = create_session()
link_query = LinkQuery()
links = link_query.search("python", limit=10)

stats_query = StatisticsQuery()
total = stats_query.get_total_count()
session.close()
```

### URL Crawling

```bash
# Run the crawler
python scripts/crawler/url_crawler.py

# Analyze crawl results
python scripts/analysis/analyze_crawl_results.py
```

## Documentation

- **[Module Documentation](docs/README.md)** - Detailed documentation for each module
- **[Database Module](database/README.md)** - Database models and queries
- **[Web Module](web/README.md)** - Web interface documentation
- **[Extractor Module](extractor/README.md)** - Content extraction utilities
- **[Scripts](scripts/README.md)** - Utility scripts documentation
- **[Python Version](docs/PYTHON_VERSION.md)** - Python compatibility guide

## Configuration

### Environment Variables

- `SECRET_KEY` - Flask secret key (default: dev key)
- `DATABASE_PATH` - Custom database path (default: `data/pocket_links.db`)
- `FLASK_ENV` - Flask environment (`development` or `production`)

### Database Location

The database is stored at `data/pocket_links.db` by default. You can customize this by setting the `DATABASE_PATH` environment variable.

## Development

### Running Tests

```bash
# Run test suite
python -m pytest tests/

# Verify database
python tests/verify_database.py
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .
```

### Project Dependencies

Key dependencies:
- **Flask** - Web framework
- **SQLAlchemy** - ORM and database toolkit
- **trafilatura** - Content extraction
- **readability-lxml** - HTML readability
- **markdownify** - HTML to markdown conversion
- **requests** - HTTP library
- **Playwright** - Browser automation (for crawler)

See `pyproject.toml` for complete dependency list.

## Features in Detail

### Web Interface Features

- **Advanced Filtering**: Filter by domain, status code, Pocket status, quality score, tags
- **Full-Text Search**: Search across titles and URLs
- **Pagination**: Efficient handling of large datasets (20,000+ links)
- **Statistics Dashboard**: Overview metrics and data quality insights
- **Export Options**: CSV and Markdown export with custom filtering
- **Tag Management**: Browse tags, view tag statistics, filter by tags

### Content Extraction

- **Multiple Methods**: Auto-select, trafilatura, or readability-based extraction
- **Metadata Extraction**: Title, author, published date, excerpt
- **URL Cleaning**: Remove UTM parameters, normalize URLs
- **Redirect Following**: Automatically follow redirects to final URL
- **Error Handling**: Graceful handling of extraction failures

### Data Management

- **Batch Import**: Efficient CSV import with progress tracking
- **Crawl Tracking**: Track URL status, redirects, response times
- **Quality Metrics**: Calculate accessibility and quality scores
- **Tag Processing**: Parse and store Pocket tags as JSON
- **Highlights Support**: Store and manage article highlights

## Troubleshooting

### Database Issues

If you encounter database errors:

```bash
# Reinitialize the database
python -c "from database.init_db import init_database; init_database()"

# Fix tag encoding issues
python tools/fix_tags_in_db.py
```

### Import Issues

If CSV import fails:

1. Check CSV format matches Pocket export format
2. Ensure database is initialized
3. Check file path and permissions

### Web Interface Issues

If the web interface doesn't start:

1. Check Python version: `python --version` (should be 3.12+)
2. Verify dependencies: `pip list`
3. Check database exists: `ls data/pocket_links.db`

## Contributing

This project is in active development. Contributions are welcome!

1. Check existing issues and documentation
2. Follow the code style (Black formatting)
3. Add tests for new features
4. Update documentation as needed

## License

[Add your license information here]

## Status

**Development Status**: Beta (v0.1.0)

The project is actively maintained and suitable for managing personal Pocket link collections.
