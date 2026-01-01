"""Fix incorrectly stored tags in the database"""

from database.models import create_session, Link
import json
import ast

def fix_tags():
    """Fix tags that were double-encoded"""
    session = create_session()
    
    try:
        # Get all links with tags
        links_with_tags = session.query(Link).filter(Link.tag_count > 0).all()
        
        print(f"Found {len(links_with_tags)} links with tags")
        print("Fixing tags...")
        
        fixed_count = 0
        
        for link in links_with_tags:
            if not link.tags:
                continue
                
            try:
                # Parse the current tags (which might be double-encoded)
                current_tags = json.loads(link.tags)
                
                # Check if it's double-encoded (list containing a string that looks like a list)
                if isinstance(current_tags, list) and len(current_tags) > 0:
                    first_tag = current_tags[0]
                    
                    # If the first tag is a string that looks like a Python list, parse it
                    if isinstance(first_tag, str) and first_tag.startswith('[') and first_tag.endswith(']'):
                        try:
                            # Parse the inner list
                            fixed_tags = ast.literal_eval(first_tag)
                            if isinstance(fixed_tags, list):
                                # Update the link
                                link.tags = json.dumps(fixed_tags)
                                link.tag_count = len(fixed_tags)
                                fixed_count += 1
                        except:
                            pass
                    # If it's a string that's wrapped in quotes, clean it
                    elif isinstance(first_tag, str) and first_tag.startswith("'") and first_tag.endswith("'"):
                        fixed_tags = [tag.strip().strip("'\"") for tag in current_tags]
                        link.tags = json.dumps(fixed_tags)
                        link.tag_count = len(fixed_tags)
                        fixed_count += 1
                        
            except Exception as e:
                print(f"Error fixing tags for link {link.id}: {e}")
                continue
        
        session.commit()
        print(f"\n✅ Fixed {fixed_count} links")
        
        # Show sample of fixed tags
        print("\nSample of fixed tags:")
        sample_links = session.query(Link).filter(Link.tag_count > 0).limit(5).all()
        for link in sample_links:
            tags_list = link.get_tags_list()
            print(f"  - {link.title[:50]}... | Tags: {tags_list}")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    print("="*60)
    print("FIX TAGS IN DATABASE")
    print("="*60)
    fix_tags()
