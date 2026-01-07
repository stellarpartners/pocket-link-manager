# User Guides & Documentation

Welcome! This section contains helpful guides for getting the most out of Pocket Link Manager.

## 📚 Getting Started Guides

### New to Pocket Link Manager?

Start here if you're setting up for the first time:

1. **[Installation Guide](../README.md#getting-started)** - Get up and running in 5 minutes
2. **[First Import](../README.md#step-3-import-your-data)** - Bring your Pocket data in
3. **[Web Interface Tour](#visual-tour)** - Learn what each section does

### Visual Tour

Take a quick visual tour of the Pocket Link Manager interface:

#### 1. Setup & Import
![Setup Page](docs/screenshots/01-setup-page.png)
*The setup wizard guides you through importing your Pocket CSV export. Simply drag and drop your file or click to browse.*

#### 2. Dashboard & Data Quality
![Dashboard](docs/screenshots/02-dashboard-data-quality.png)
*Your main dashboard shows collection statistics, quality metrics, status code breakdowns, and top domains at a glance.*

#### 3. Links Library
![Links Page](docs/screenshots/03-links-page.png)
*Browse all your saved articles with powerful filtering, sorting, and bulk actions. Search by title, filter by domain, status, or tags.*

#### 4. Tags Management
![Tags Page](docs/screenshots/04-tags-page.png)
*Organize your collection with tags. View all tags, see how many articles each has, and quickly filter to specific topics.*

#### 5. Export to Obsidian
![Export Page](docs/screenshots/05-export-page.png)
*Export your links to Obsidian vaults with full content extraction. Configure export options and sync directly to your knowledge base.*

#### 6. Link Details
![Link Detail Page](docs/screenshots/06-link-detail-page.png)
*View comprehensive details for any link: metadata, crawl results, content extraction, tags, and quick actions for editing or exporting.*

### Migrating from Pocket?

**[Quick Migration Guide](../README.md#-pocket-has-shut-down---were-here-to-help)** - Everything you need to preserve your Pocket collection

---

## 🎯 How-To Guides

### Organizing Your Collection

**Find Articles Quickly**
- Use the search bar to find articles by title or URL
- Filter by domain to see all articles from a specific website
- Browse tags to explore articles by topic
- Combine filters to narrow down results

**Manage Tags**
- Add tags to individual articles
- Bulk tag multiple articles at once
- Rename tags across your entire collection
- Remove unused tags

**Clean Up Your Collection**
- Find and remove duplicate URLs
- Identify broken links (404 errors)
- Remove tracking parameters from URLs
- Archive articles you've read

### Working with Your Data

**Export Your Links**
- Export to CSV for spreadsheets
- Create markdown files for Obsidian/Logseq
- Generate JSON for custom tools
- Filter before export to create curated lists

**Verify Link Status**
- Run the crawler to check all links
- View status codes and redirects
- Find broken or moved content
- Track which articles are still accessible

**Convert to Markdown**
- Turn web pages into clean, readable markdown
- Extract article content without ads
- Save full article text locally
- Create your own web archive

---

## 💡 Use Cases

### Building a Personal Knowledge Base

Use Pocket Link Manager as a stepping stone to Obsidian or another knowledge management system:

1. Import your Pocket data
2. Tag and organize your articles
3. Convert important articles to markdown
4. Export to your knowledge base

**Best for**: Researchers, students, writers building reference libraries

### Curating Topic-Specific Collections

Create focused reading lists on specific topics:

1. Use tags to categorize articles
2. Filter by tag to see topic-specific content  
3. Export filtered lists to share with others
4. Track which articles you've read

**Best for**: Educators, course creators, reading groups

### Archiving Important Content

Preserve articles that might disappear:

1. Import your collection
2. Run the crawler to check accessibility
3. Convert important articles to markdown
4. Keep local copies independent of the web

**Best for**: Journalists, researchers, digital archivists

### Cleaning Up Years of Saves

Finally tackle that overwhelming backlog:

1. Import everything from Pocket
2. Use quality metrics to prioritize
3. Filter out broken links
4. Archive what you've read, export what matters

**Best for**: Anyone with 1000+ saved articles

---

## 🔧 Common Workflows

### Daily Reading Workflow

1. Open the web interface
2. Filter to "Unread" articles
3. Browse by quality score (highest first)
4. Open articles in new tabs
5. Mark as "Archived" when done

### Weekly Curation

1. Review new articles
2. Add relevant tags
3. Convert key articles to markdown
4. Export tagged collections

### Monthly Maintenance

1. Run crawler to check link health
2. Remove broken links
3. Archive old, read articles
4. Update tags and organization

---

## 📖 Understanding Features

### Dashboard & Statistics

**What you see:**
- Total article count
- Unread vs archived ratio
- Top domains
- Quality score distribution
- Recent activity

**Why it matters:**
Understand your reading patterns, identify your most-saved sources, and track collection health.

### Link Browser

**What you can do:**
- View all articles in a paginated list
- Filter by multiple criteria
- Sort by date, domain, or quality
- See metadata at a glance

**Best practices:**
- Use filters to narrow down large collections
- Sort by quality to find best articles first
- Use pagination to browse systematically

### Tag System

**How it works:**
Tags from Pocket are preserved and you can add new ones. Tags help you categorize and find articles by topic.

**Tips:**
- Use consistent naming (e.g., "web-design" not "WebDesign")
- Don't over-tag - 2-4 tags per article is plenty
- Create topic-based tags, not status tags (use filters for that)
- Periodically review and consolidate similar tags

### Quality Metrics

**What they measure:**
- Link accessibility (does it work?)
- Response time (how fast?)
- Redirect chains (any issues?)
- HTTP status (what happened?)

**How to use them:**
- Filter by quality score to find best content
- Identify broken links for cleanup
- Spot redirect issues
- Prioritize reliable sources

### Export System

**Available formats:**
- **CSV**: Great for spreadsheets, data analysis, sharing
- **Markdown**: Perfect for Obsidian, note-taking apps
- **JSON**: Use in custom scripts and applications

**Export tips:**
- Filter before exporting to create focused lists
- Include metadata in exports for context
- Export regularly as backups
- Create multiple exports for different purposes

---

## 🛠️ Technical Documentation

For developers and advanced users who want to customize or extend the tool:

### Code Documentation

- **[Database Module](../database/README.md)** - Data models, queries, database operations
- **[Web Module](../web/README.md)** - Web interface, routes, API endpoints
- **[Extractor Module](../extractor/README.md)** - Content extraction, URL processing
- **[Scripts](../scripts/README.md)** - Utility scripts, crawler, analysis tools
- **[Tools](../tools/README.md)** - Maintenance and admin tools

### Development Resources

- **[Python Version Guide](PYTHON_VERSION.md)** - Version compatibility and requirements
- **[Testing Guide](../tests/README.md)** - Running tests, verification scripts
- **Project Structure** - See the module READMEs above

---

## 🎓 Learning Resources

### Video Tutorials

*Coming soon - we're working on video guides for visual learners!*

### Example Workflows

**Scenario: Converting Pocket to Obsidian**

1. Export from Pocket (CSV)
2. Import to Pocket Link Manager
3. Review and tag articles
4. Convert important articles to markdown
5. Export markdown files
6. Import into Obsidian vault

**Scenario: Creating a Shared Reading List**

1. Tag articles for a specific topic
2. Filter by that tag
3. Export to CSV
4. Share the CSV file
5. Recipients can import or view in spreadsheet

**Scenario: Building a Research Archive**

1. Import research articles
2. Add detailed tags
3. Convert to markdown for full-text search
4. Export to reference manager
5. Keep local markdown copies as backup

---

## 💬 Getting Help

### Troubleshooting

Common issues and solutions are in the [Troubleshooting section](../README.md#need-help) of the main README.

### Community

- **Questions?** [Open an issue](https://github.com/stellarpartners/pocket-link-manager/issues)
- **Ideas?** Share feature requests in issues
- **Found a bug?** Report it with details

### Contributing

Want to improve the documentation?

1. Identify what's unclear or missing
2. Submit an issue or pull request
3. Help others by sharing your experience

---

## 📋 Quick Reference

### Essential Commands

```bash
# Start web interface
python run.py

# Import Pocket data
python tools/import_full_dataset.py

# Run crawler
python scripts/crawler/url_crawler.py

# Analyze results
python scripts/analysis/analyze_crawl_results.py
```

### Important Locations

- **Web Interface**: `http://127.0.0.1:5000`
- **Database**: `data/pocket_links.db`
- **Markdown Files**: `data/markdown/`
- **Exports**: `data/exports/` (or download via web)

### Key Keyboard Shortcuts

*In the web interface:*
- `/` - Focus search box
- `Esc` - Clear filters
- `←` `→` - Navigate pages

---

## 🌟 Tips & Tricks

**Speed up imports**: Place CSV file in `data/` folder before importing

**Bulk operations**: Use checkboxes to select multiple articles for bulk actions

**Custom filters**: Combine multiple filters for precise results

**Quality threshold**: Set minimum quality score (e.g., 70+) for reliable links

**Export templates**: Create filtered views and save export configurations

**Backup your data**: Periodically export everything to CSV as backup

---

## What's Next?

- ✅ You've set up Pocket Link Manager
- ✅ You've imported your data  
- ✅ You understand the features

**Now:**
1. Explore your collection in the web interface
2. Try different filters and search queries
3. Export some content to test workflows
4. Set up your own organization system

**Questions or feedback?** We'd love to hear from you in the [issues](https://github.com/stellarpartners/pocket-link-manager/issues)!
