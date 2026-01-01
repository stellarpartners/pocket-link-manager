# Analysis Scripts

Tools for analyzing crawl results and exploring your Pocket data.

## Scripts

### analyze_crawl_results.py

Comprehensive analysis of crawl results with statistics and insights.

**Features:**

- Status code breakdown
- Error analysis by type and domain
- Redirect pattern analysis
- Domain-level statistics
- Response time analysis
- Summary report generation

**Usage:**

```bash
python scripts/analysis/analyze_crawl_results.py
```

**Output:**

- Console output with detailed statistics
- Summary report saved to `data/crawl_summary_report.txt`

**Analysis Sections:**

1. **Basic Statistics** - Overview of crawl results
2. **Status Code Breakdown** - HTTP status code distribution
3. **Error Analysis** - Error types and patterns
4. **Redirect Analysis** - Redirect patterns and domain changes
5. **Domain Analysis** - Success rates by domain
6. **Response Times** - Performance metrics

### inspect_data.py

Simple script to inspect the structure and contents of your Pocket data.

**Usage:**

```bash
python scripts/analysis/inspect_data.py
```

**Output:**

- Total rows and columns
- Column names
- Sample rows
- Tagged articles preview
- Articles with highlights preview

Useful for understanding your data structure before processing.
