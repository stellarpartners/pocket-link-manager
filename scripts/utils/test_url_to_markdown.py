#!/usr/bin/env python3
"""
Test script for URL to Markdown converter

Usage:
    python scripts/utils/test_url_to_markdown.py <url>
    python scripts/utils/test_url_to_markdown.py <url> --output output.md
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extractor.url_to_markdown import URLToMarkdownConverter


def main():
    parser = argparse.ArgumentParser(description='Convert URL to markdown')
    parser.add_argument('url', help='URL to convert')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    parser.add_argument('--method', '-m', choices=['auto', 'trafilatura', 'readability'], 
                       default='auto', help='Extraction method')
    parser.add_argument('--no-metadata', action='store_true', 
                       help='Skip frontmatter metadata')
    
    args = parser.parse_args()
    
    print(f"Converting URL to markdown: {args.url}")
    print(f"Extraction method: {args.method}")
    print("-" * 60)
    
    converter = URLToMarkdownConverter()
    result = converter.convert(
        args.url,
        extract_method=args.method,
        include_metadata=not args.no_metadata
    )
    
    if result['success']:
        print(f"✅ Success!")
        print(f"Title: {result['title'] or 'N/A'}")
        print(f"Method: {result['extraction_method']}")
        print(f"Final URL: {result['final_url']}")
        
        if result['excerpt']:
            print(f"\nExcerpt: {result['excerpt'][:200]}...")
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result['markdown'], encoding='utf-8')
            print(f"\n✅ Saved to: {output_path}")
        else:
            print("\n" + "=" * 60)
            print("MARKDOWN OUTPUT:")
            print("=" * 60)
            print(result['markdown'][:2000])
            if len(result['markdown']) > 2000:
                print(f"\n... (truncated, total length: {len(result['markdown'])} characters)")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        if 'metadata' in result:
            print(f"Status code: {result['metadata'].get('status_code', 'N/A')}")
        sys.exit(1)


if __name__ == '__main__':
    main()
