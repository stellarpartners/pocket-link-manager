# Scripts Directory

Utility scripts organized by purpose for data processing, crawling, analysis, and import operations.

## Structure

```
scripts/
├── crawler/      # URL crawling scripts
├── analysis/     # Data analysis tools
├── import/       # Data import and processing
└── utils/        # Utility scripts and dependencies
```

## Scripts by Category

### Crawler (`crawler/`)

- **url_crawler.py** - Main URL crawler for visiting Pocket links and tracking redirects
- **test_crawler.py** - Test crawler with sample URLs

### Analysis (`analysis/`)

- **analyze_crawl_results.py** - Analyze crawl results and generate statistics
- **inspect_data.py** - Inspect and explore Pocket data structure

### Import (`import/`)

- **pocket_merge_script.py** - Merge multiple Pocket export files into one dataset
- **clean_utm_parameters.py** - Clean UTM parameters from database URLs

### Utils (`utils/`)

- **test_url_to_markdown.py** - Test URL to markdown conversion
- **requirements_crawler.txt** - Additional dependencies for crawler scripts

## Usage Examples

```bash
# Run crawler
python scripts/crawler/url_crawler.py

# Analyze results
python scripts/analysis/analyze_crawl_results.py

# Merge Pocket exports
python scripts/import/pocket_merge_script.py

# Clean UTM parameters
python scripts/import/clean_utm_parameters.py --execute
```

## Dependencies

Most scripts require the main project dependencies (`requirements.txt`). Crawler scripts have additional requirements in `scripts/utils/requirements_crawler.txt`.
