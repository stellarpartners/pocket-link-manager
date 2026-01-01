#!/usr/bin/env python3
"""
Pocket Export Merger Script
Combines multiple CSV files and JSON annotations into a single comprehensive dataset
for importing into Obsidian or other knowledge management systems.
"""

import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path

class PocketMerger:
    def __init__(self, export_folder="data/pocket_export"):
        self.export_folder = Path(export_folder)
        self.csv_files = []
        self.annotations = {}
        self.merged_data = []
        
    def find_files(self):
        """Discover all CSV and JSON files in the export folder"""
        # Find CSV files
        self.csv_files = list(self.export_folder.glob("part_*.csv"))
        print(f"Found {len(self.csv_files)} CSV files: {[f.name for f in self.csv_files]}")
        
        # Find annotations
        annotations_folder = self.export_folder / "annotations"
        if annotations_folder.exists():
            annotation_files = list(annotations_folder.glob("*.json"))
            print(f"Found {len(annotation_files)} annotation files: {[f.name for f in annotation_files]}")
            
            for file in annotation_files:
                self.load_annotations(file)
        else:
            print("No annotations folder found")
    
    def load_annotations(self, json_file):
        """Load highlights/annotations from JSON file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    url = item.get('url')
                    if url:
                        self.annotations[url] = {
                            'title': item.get('title', ''),
                            'highlights': item.get('highlights', [])
                        }
            print(f"Loaded {len(data)} annotations from {json_file.name}")
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    def merge_csv_files(self):
        """Combine all CSV files into a single DataFrame"""
        all_dataframes = []
        
        for csv_file in self.csv_files:
            try:
                df = pd.read_csv(csv_file)
                print(f"Loaded {len(df)} rows from {csv_file.name}")
                all_dataframes.append(df)
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
        
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            print(f"Combined total: {len(combined_df)} articles")
            return combined_df
        return pd.DataFrame()
    
    def convert_timestamp(self, timestamp):
        """Convert Unix timestamp to readable date"""
        try:
            return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp
    
    def process_tags(self, tags):
        """Clean and format tags"""
        if pd.isna(tags) or tags == '':
            return []
        if isinstance(tags, str):
            # Split by common delimiters and clean
            tag_list = []
            for delimiter in [',', ';', '|']:
                if delimiter in tags:
                    tag_list = [tag.strip() for tag in tags.split(delimiter)]
                    break
            if not tag_list:
                tag_list = [tags.strip()]
            return [tag for tag in tag_list if tag]
        return []
    
    def enhance_with_annotations(self, df):
        """Add highlights and annotations to the main dataset"""
        df['highlights'] = ''
        df['highlight_count'] = 0
        
        for index, row in df.iterrows():
            url = row['url']
            if url in self.annotations:
                annotation_data = self.annotations[url]
                highlights = annotation_data.get('highlights', [])
                
                if highlights:
                    df.at[index, 'highlight_count'] = len(highlights)
                    
                    # Format highlights as markdown
                    highlight_text = []
                    for highlight in highlights:
                        quote = highlight.get('quote', '').strip()
                        created_at = highlight.get('created_at', '')
                        
                        if created_at:
                            highlight_date = self.convert_timestamp(created_at)
                            highlight_text.append(f"> {quote}\n*Highlighted: {highlight_date}*")
                        else:
                            highlight_text.append(f"> {quote}")
                    
                    df.at[index, 'highlights'] = '\n\n'.join(highlight_text)
        
        return df
    
    def create_comprehensive_dataset(self):
        """Main method to create the merged dataset"""
        print("=== Pocket Export Merger ===\n")
        
        # Discover files
        self.find_files()
        
        # Merge CSV files
        df = self.merge_csv_files()
        if df.empty:
            print("No data found to merge!")
            return None
        
        # Clean and enhance data
        print(f"\nProcessing {len(df)} articles...")
        
        # Convert timestamps
        df['date_saved'] = df['time_added'].apply(self.convert_timestamp)
        
        # Process tags
        df['tag_list'] = df['tags'].apply(self.process_tags)
        df['tag_count'] = df['tag_list'].apply(len)
        
        # Add highlights
        df = self.enhance_with_annotations(df)
        
        # Add useful metadata
        df['domain'] = df['url'].apply(lambda x: self.extract_domain(x))
        df['has_highlights'] = df['highlight_count'] > 0
        df['has_tags'] = df['tag_count'] > 0
        
        # Reorder columns for better readability
        column_order = [
            'title', 'url', 'domain', 'status', 'date_saved', 'time_added',
            'tags', 'tag_list', 'tag_count', 'has_tags',
            'highlights', 'highlight_count', 'has_highlights'
        ]
        
        df = df[column_order]
        
        return df
    
    def extract_domain(self, url):
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ''
    
    def save_to_formats(self, df, base_filename="data/pocket_merged"):
        """Save the merged data in multiple formats"""
        if df is None or df.empty:
            print("No data to save!")
            return
        
        # Save as CSV
        csv_file = f"{base_filename}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8')
        print(f"✅ Saved CSV: {csv_file} ({len(df)} articles)")
        
        # Save as JSON
        json_file = f"{base_filename}.json"
        df.to_json(json_file, orient='records', indent=2, force_ascii=False)
        print(f"✅ Saved JSON: {json_file}")
        
        # Save as Markdown for Obsidian
        md_file = f"{base_filename}.md"
        self.save_as_markdown(df, md_file)
        print(f"✅ Saved Markdown: {md_file}")
        
        # Create summary
        self.create_summary(df, f"{base_filename}_summary.txt")
    
    def save_as_markdown(self, df, filename):
        """Save as Markdown file suitable for Obsidian"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Pocket Export - Merged Articles\n\n")
            f.write(f"**Total Articles**: {len(df)}\n")
            f.write(f"**Date Exported**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Statistics
            f.write("## Statistics\n\n")
            f.write(f"- **Unread**: {len(df[df['status'] == 'unread'])}\n")
            f.write(f"- **Archived**: {len(df[df['status'] == 'archive'])}\n")
            f.write(f"- **With Tags**: {len(df[df['has_tags']])}\n")
            f.write(f"- **With Highlights**: {len(df[df['has_highlights']])}\n\n")
            
            # Group by status
            for status in ['unread', 'archive']:
                status_articles = df[df['status'] == status]
                if len(status_articles) > 0:
                    f.write(f"## {status.title()} Articles ({len(status_articles)})\n\n")
                    
                    for _, article in status_articles.iterrows():
                        f.write(f"### {article['title']}\n\n")
                        f.write(f"**URL**: {article['url']}\n")
                        f.write(f"**Domain**: {article['domain']}\n")
                        f.write(f"**Saved**: {article['date_saved']}\n")
                        
                        if article['has_tags']:
                            tags = ', '.join(article['tag_list'])
                            f.write(f"**Tags**: {tags}\n")
                        
                        if article['has_highlights']:
                            f.write(f"**Highlights ({article['highlight_count']}):**\n\n")
                            f.write(f"{article['highlights']}\n")
                        
                        f.write("\n---\n\n")
    
    def create_summary(self, df, filename):
        """Create a summary report"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("POCKET EXPORT SUMMARY REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total Articles: {len(df)}\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Status breakdown
            f.write("STATUS BREAKDOWN:\n")
            f.write(f"- Unread: {len(df[df['status'] == 'unread'])}\n")
            f.write(f"- Archived: {len(df[df['status'] == 'archive'])}\n\n")
            
            # Tag analysis
            f.write("TAG ANALYSIS:\n")
            f.write(f"- Articles with tags: {len(df[df['has_tags']])}\n")
            f.write(f"- Total unique tags: {len(set([tag for sublist in df['tag_list'] for tag in sublist]))}\n")
            
            # Most common tags
            all_tags = [tag for sublist in df['tag_list'] for tag in sublist]
            if all_tags:
                from collections import Counter
                common_tags = Counter(all_tags).most_common(10)
                f.write("- Top 10 tags:\n")
                for tag, count in common_tags:
                    f.write(f"  {tag}: {count}\n")
            
            f.write(f"\n")
            
            # Highlights
            f.write("HIGHLIGHTS:\n")
            f.write(f"- Articles with highlights: {len(df[df['has_highlights']])}\n")
            f.write(f"- Total highlights: {df['highlight_count'].sum()}\n\n")
            
            # Domain analysis
            f.write("TOP DOMAINS:\n")
            domain_counts = df['domain'].value_counts().head(10)
            for domain, count in domain_counts.items():
                f.write(f"- {domain}: {count}\n")
            
        print(f"✅ Saved summary: {filename}")

def main():
    merger = PocketMerger("data/pocket_export")
    merged_data = merger.create_comprehensive_dataset()
    
    if merged_data is not None:
        print(f"\n=== MERGE COMPLETE ===")
        print(f"Total articles processed: {len(merged_data)}")
        print(f"Articles with highlights: {len(merged_data[merged_data['has_highlights']])}")
        print(f"Articles with tags: {len(merged_data[merged_data['has_tags']])}")
        
        # Save in multiple formats
        merger.save_to_formats(merged_data)
        
        print(f"\n✨ All files saved! Check the output files for your merged Pocket data.")
    else:
        print("❌ Failed to create merged dataset")

if __name__ == "__main__":
    main()
