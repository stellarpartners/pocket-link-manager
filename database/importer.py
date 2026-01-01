"""
Import CSV data into the database
"""

import pandas as pd
import json
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy.exc import IntegrityError

try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm is not installed
    def tqdm(iterable, *args, **kwargs):
        return iterable

from .models import (
    Link, CrawlResult, ContentExtraction, QualityMetric,
    create_session
)
from .models import get_db_path
from extractor.url_utils import remove_utm_parameters


def parse_json_field(value):
    """Safely parse JSON field from CSV"""
    if pd.isna(value) or value == '':
        return []
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            # Try JSON parsing first
            return json.loads(value)
        except json.JSONDecodeError:
            # If JSON parsing fails, try Python list syntax (e.g., "['tag1', 'tag2']")
            if value.startswith('[') and value.endswith(']'):
                try:
                    # Use ast.literal_eval for safe Python literal evaluation
                    import ast
                    result = ast.literal_eval(value)
                    if isinstance(result, list):
                        return result
                except:
                    pass
            # Try as comma-separated string
            if ',' in value:
                return [tag.strip().strip("'\"") for tag in value.split(',') if tag.strip()]
            # Single tag, remove quotes if present
            cleaned = value.strip().strip("'\"")
            return [cleaned] if cleaned else []
    return value if isinstance(value, list) else []


def import_csv_to_database(csv_path, db_path=None, batch_size=1000, skip_existing=True):
    """
    Import Pocket merged CSV into the database.
    
    Args:
        csv_path: Path to CSV file
        db_path: Optional database path
        batch_size: Number of records to process per batch
        skip_existing: If True, skip URLs that already exist
    
    Returns:
        dict with import statistics
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting import from {csv_path}")
    
    # Read CSV in chunks
    total_rows = sum(1 for _ in open(csv_path, 'r', encoding='utf-8')) - 1
    logger.info(f"Total rows to import: {total_rows:,}")
    
    stats = {
        'total': 0,
        'imported': 0,
        'skipped': 0,
        'errors': 0,
        'crawl_results': 0,
        'quality_metrics': 0
    }
    
    session = create_session(db_path)
    
    try:
        # Process CSV in chunks
        chunk_iter = pd.read_csv(
            csv_path,
            chunksize=batch_size,
            low_memory=False,
            encoding='utf-8'
        )
        
        for chunk_num, chunk_df in enumerate(chunk_iter, 1):
            logger.info(f"Processing chunk {chunk_num} ({len(chunk_df)} rows)")
            
            for idx, row in tqdm(chunk_df.iterrows(), total=len(chunk_df), desc=f"Chunk {chunk_num}"):
                stats['total'] += 1
                
                try:
                    # Check if link already exists
                    existing_link = session.query(Link).filter_by(
                        original_url=row['url']
                    ).first()
                    
                    if existing_link and skip_existing:
                        stats['skipped'] += 1
                        continue
                    
                    # Parse tags
                    # Try tag_list first (JSON string), then tags (plain string)
                    tag_value = row.get('tag_list') or row.get('tags', '')
                    if pd.notna(tag_value) and tag_value:
                        # If tag_list exists and looks like JSON, parse it
                        if isinstance(tag_value, str) and tag_value.strip().startswith('['):
                            try:
                                tags_list = json.loads(tag_value)
                            except:
                                # If parsing fails, try as comma-separated string
                                tags_list = parse_json_field(tag_value)
                        else:
                            # Plain string tag, convert to list
                            tags_list = [tag_value.strip()] if tag_value.strip() else []
                    else:
                        tags_list = []
                    tags_json = json.dumps(tags_list) if tags_list else None
                    
                    # Parse highlights
                    highlights = row.get('highlights', '')
                    highlights_list = []
                    if pd.notna(highlights) and highlights:
                        # Highlights might be markdown formatted, parse if needed
                        highlights_list = [highlights] if isinstance(highlights, str) else highlights
                    highlights_json = json.dumps(highlights_list) if highlights_list else None
                    
                    # Parse date_saved
                    date_saved = None
                    if pd.notna(row.get('date_saved')):
                        try:
                            date_saved = pd.to_datetime(row['date_saved'])
                        except:
                            pass
                    
                    # Create or update link
                    if existing_link:
                        link = existing_link
                        link.title = row.get('title', '')
                        link.domain = row.get('domain', '')
                        link.pocket_status = row.get('status', 'archive')
                        link.date_saved = date_saved
                        link.time_added = int(row.get('time_added', 0)) if pd.notna(row.get('time_added')) else None
                        link.tags = tags_json
                        link.tag_count = len(tags_list)
                        link.highlights = highlights_json
                        link.highlight_count = len(highlights_list)
                        link.updated_at = datetime.utcnow()
                    else:
                        link = Link(
                            title=row.get('title', ''),
                            original_url=row['url'],
                            domain=row.get('domain', ''),
                            pocket_status=row.get('status', 'archive'),
                            date_saved=date_saved,
                            time_added=int(row.get('time_added', 0)) if pd.notna(row.get('time_added')) else None,
                            tags=tags_json,
                            tag_count=len(tags_list),
                            highlights=highlights_json,
                            highlight_count=len(highlights_list)
                        )
                        session.add(link)
                    
                    session.flush()  # Get the link ID
                    
                    # Import crawl results if available
                    if pd.notna(row.get('crawl_final_url')):
                        # Check if crawl result already exists
                        existing_crawl = session.query(CrawlResult).filter_by(
                            link_id=link.id
                        ).order_by(CrawlResult.crawl_date.desc()).first()
                        
                        if not existing_crawl or existing_crawl.status_code != row.get('crawl_status_code'):
                            final_url_raw = row.get('crawl_final_url')
                            final_url_cleaned = remove_utm_parameters(final_url_raw) if pd.notna(final_url_raw) else None
                            crawl_result = CrawlResult(
                                link_id=link.id,
                                final_url=final_url_cleaned,
                                status_code=int(row['crawl_status_code']) if pd.notna(row.get('crawl_status_code')) else None,
                                redirect_count=int(row.get('crawl_redirect_count', 0)) if pd.notna(row.get('crawl_redirect_count')) else 0,
                                response_time=float(row['crawl_response_time']) if pd.notna(row.get('crawl_response_time')) else None,
                                error_type=row.get('crawl_error_type') if pd.notna(row.get('crawl_error_type')) else None,
                                error_message=row.get('crawl_error_message') if pd.notna(row.get('crawl_error_message')) else None,
                                crawl_date=pd.to_datetime(row['crawl_date']) if pd.notna(row.get('crawl_date')) else datetime.utcnow()
                            )
                            session.add(crawl_result)
                            stats['crawl_results'] += 1
                    
                    # Create or update quality metric
                    status_code = int(row['crawl_status_code']) if pd.notna(row.get('crawl_status_code')) else None
                    redirect_count = int(row.get('crawl_redirect_count', 0)) if pd.notna(row.get('crawl_redirect_count')) else 0
                    
                    quality_metric = session.query(QualityMetric).filter_by(link_id=link.id).first()
                    if not quality_metric:
                        quality_metric = QualityMetric(link_id=link.id)
                        session.add(quality_metric)
                    
                    quality_metric.is_accessible = (status_code == 200)
                    quality_metric.has_redirects = (redirect_count > 0)
                    quality_metric.has_content = False  # Will be updated when content is extracted
                    quality_metric.has_markdown = False  # Will be updated when markdown is generated
                    quality_metric.quality_score = calculate_quality_score(
                        status_code, redirect_count, False, False
                    )
                    quality_metric.last_updated = datetime.utcnow()
                    
                    stats['imported'] += 1
                    
                except IntegrityError as e:
                    session.rollback()
                    stats['errors'] += 1
                    logger.warning(f"Error importing row {idx}: {e}")
                    continue
                except Exception as e:
                    session.rollback()
                    stats['errors'] += 1
                    logger.error(f"Unexpected error importing row {idx}: {e}", exc_info=True)
                    continue
            
            # Commit after each chunk
            try:
                session.commit()
                logger.info(f"Chunk {chunk_num} committed successfully")
            except Exception as e:
                session.rollback()
                logger.error(f"Error committing chunk {chunk_num}: {e}")
                raise
        
        stats['quality_metrics'] = session.query(QualityMetric).count()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Import failed: {e}", exc_info=True)
        raise
    finally:
        session.close()
    
    logger.info("Import completed")
    logger.info(f"Statistics: {stats}")
    
    return stats


def calculate_quality_score(status_code, redirect_count, has_content, has_markdown):
    """
    Calculate quality score (0-100) for a link.
    
    Scoring:
    - Accessibility (status 200): 40 points
    - No errors: 20 points
    - Has content: 20 points
    - Has markdown: 20 points
    """
    score = 0
    
    # Accessibility
    if status_code == 200:
        score += 40
    elif status_code and 200 <= status_code < 300:
        score += 30
    elif status_code and 400 <= status_code < 500:
        score += 10
    
    # Redirect health (fewer redirects is better, but some redirects are OK)
    if redirect_count == 0:
        score += 10
    elif redirect_count <= 3:
        score += 5
    
    # Content availability
    if has_content:
        score += 20
    
    # Markdown generation
    if has_markdown:
        score += 20
    
    return min(100, score)


if __name__ == '__main__':
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'data/pocket_merged_crawled.csv'
    
    print(f"Importing {csv_file} into database...")
    stats = import_csv_to_database(csv_file)
    
    print("\nImport Statistics:")
    print(f"  Total rows processed: {stats['total']:,}")
    print(f"  Successfully imported: {stats['imported']:,}")
    print(f"  Skipped (already exists): {stats['skipped']:,}")
    print(f"  Errors: {stats['errors']:,}")
    print(f"  Crawl results imported: {stats['crawl_results']:,}")
    print(f"  Quality metrics created: {stats['quality_metrics']:,}")
