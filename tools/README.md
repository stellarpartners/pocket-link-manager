# Tools Directory

Root-level utility tools for database operations and maintenance.

## Scripts

### import_full_dataset.py

Import the full Pocket dataset from CSV into the database.

**Features:**

- Batch processing (1000 records at a time)
- Skip existing records
- Progress tracking
- Comprehensive statistics

**Usage:**

```bash
python tools/import_full_dataset.py
```

**Requirements:**

- CSV file: `data/pocket_merged_crawled.csv`
- Database must be initialized

**Output:**

- Imports links, crawl results, and quality metrics
- Prints import statistics

### fix_tags_in_db.py

Fix incorrectly stored tags in the database (handles double-encoding issues).

**Usage:**

```bash
python tools/fix_tags_in_db.py
```

**What it does:**

- Finds links with tags
- Fixes double-encoded tag JSON
- Updates tag counts
- Shows sample of fixed tags

Use this if you notice tags are stored incorrectly (e.g., as strings containing JSON instead of proper JSON arrays).
