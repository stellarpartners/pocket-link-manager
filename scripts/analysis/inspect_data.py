import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Load the merged data
df = pd.read_csv('data/pocket_merged.csv')

print("MERGED DATA STRUCTURE")
print("=" * 50)
print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")

print("\nCOLUMNS:")
for i, col in enumerate(df.columns, 1):
    print(f"{i:2d}. {col}")

print("\nSAMPLE ROWS:")
print("-" * 100)
for idx, row in df.head(3).iterrows():
    print(f"Row {idx + 1}:")
    print(f"  Title: {row['title'][:80]}...")
    print(f"  URL: {row['url']}")
    print(f"  Domain: {row['domain']}")
    print(f"  Status: {row['status']}")
    print(f"  Date Saved: {row['date_saved']}")
    print(f"  Tags: {row['tags'] if pd.notna(row['tags']) else 'None'}")
    print(f"  Has Highlights: {row['has_highlights']}")
    print("-" * 50)

# Show articles with tags
tagged_articles = df[df['has_tags']]
if len(tagged_articles) > 0:
    print(f"\nSAMPLE TAGGED ARTICLES ({len(tagged_articles)} total):")
    for idx, row in tagged_articles.head(3).iterrows():
        print(f"- {row['title'][:60]}... | Tags: {row['tags']}")

# Show articles with highlights  
highlighted_articles = df[df['has_highlights']]
if len(highlighted_articles) > 0:
    print(f"\nARTICLES WITH HIGHLIGHTS ({len(highlighted_articles)} total):")
    for idx, row in highlighted_articles.iterrows():
        print(f"- {row['title']}")
        print(f"  Highlights: {row['highlights'][:200]}...")
