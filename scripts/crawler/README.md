# Crawler Scripts

URL crawling tools for visiting Pocket links and tracking redirects, status codes, and errors.

## Scripts

### url_crawler.py

Main URL crawler that visits each URL from your Pocket data, follows redirects, and tracks:

- Final URLs after redirects
- HTTP status codes
- Redirect counts
- Response times
- Error types and messages

**Features:**

- Multi-threaded crawling with configurable workers
- Respectful delays between requests
- Progress saving every N URLs
- Resume capability for interrupted crawls
- Comprehensive logging

**Usage:**

```bash
python scripts/crawler/url_crawler.py
```

**Configuration:**

Edit the `config` dictionary in `main()`:

```python
config = {
    'csv_path': 'data/pocket_merged.csv',
    'max_workers': 5,           # Parallel requests
    'delay_range': (1, 3),      # Random delay (seconds)
    'batch_size': 100           # Save progress every N URLs
}
```

### test_crawler.py

Test script for validating the crawler with a small sample of URLs before running on the full dataset.

**Usage:**

```bash
python scripts/crawler/test_crawler.py
```

Creates a test CSV with 5 sample URLs and runs the crawler to verify everything works correctly.

## Output

The crawler adds new columns to your CSV:

- `crawl_final_url` - Final URL after redirects
- `crawl_status_code` - HTTP status code
- `crawl_redirect_count` - Number of redirects
- `crawl_response_time` - Response time in seconds
- `crawl_error_type` - Error type if any
- `crawl_error_message` - Error details
- `crawl_date` - When the URL was crawled

Results are saved to `data/pocket_merged_crawled.csv`.
