# Utility Scripts

Helper scripts and dependencies for various operations.

## Scripts

### test_url_to_markdown.py

Test script for the URL to markdown converter. Useful for testing content extraction on individual URLs.

**Usage:**

```bash
# Basic conversion
python scripts/utils/test_url_to_markdown.py https://example.com/article

# Save to file
python scripts/utils/test_url_to_markdown.py https://example.com/article --output article.md

# Specify extraction method
python scripts/utils/test_url_to_markdown.py https://example.com/article --method trafilatura

# Skip metadata
python scripts/utils/test_url_to_markdown.py https://example.com/article --no-metadata
```

**Options:**

- `--output, -o` - Output file path
- `--method, -m` - Extraction method (auto, trafilatura, readability)
- `--no-metadata` - Skip frontmatter metadata

## Dependencies

### requirements_crawler.txt

Additional Python dependencies required for crawler scripts:

- `pandas>=1.3.0` - Data manipulation
- `requests>=2.25.0` - HTTP requests
- `urllib3>=1.26.0` - URL handling

Install with:

```bash
pip install -r scripts/utils/requirements_crawler.txt
```

Note: These are in addition to the main project requirements in `requirements.txt`.
