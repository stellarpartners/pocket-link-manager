# Import Scripts

Tools for importing and processing Pocket export data.

## Scripts

### pocket_merge_script.py

Merges multiple Pocket export CSV files and JSON annotations into a single comprehensive dataset.

**Features:**

- Combines multiple CSV files (`part_*.csv`)
- Merges highlights/annotations from JSON files
- Converts timestamps to readable dates
- Processes and cleans tags
- Adds domain extraction
- Saves in multiple formats (CSV, JSON, Markdown)

**Usage:**

```bash
python scripts/import/pocket_merge_script.py
```

**Input:**

Expects Pocket export files in `data/pocket_export/`:
- `part_*.csv` - CSV files with Pocket data
- `annotations/*.json` - JSON files with highlights

**Output:**

- `data/pocket_merged.csv` - Merged CSV file
- `data/pocket_merged.json` - JSON format
- `data/pocket_merged.md` - Markdown format for Obsidian
- `data/pocket_merged_summary.txt` - Summary report

### clean_utm_parameters.py

Removes UTM tracking parameters from URLs in the database.

**Features:**

- Finds URLs with UTM parameters
- Removes all `utm_*` parameters
- Dry-run mode by default
- Batch processing
- Progress tracking

**Usage:**

```bash
# Dry run (preview changes)
python scripts/import/clean_utm_parameters.py

# Actually update database
python scripts/import/clean_utm_parameters.py --execute

# Skip confirmation prompt
python scripts/import/clean_utm_parameters.py --execute --yes
```

**Options:**

- `--execute` - Actually update the database (default: dry-run)
- `--yes` - Skip confirmation prompt
- `--batch-size N` - Process N records per batch (default: 100)
