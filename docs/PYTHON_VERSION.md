# Python Version Compatibility

## Recommended Versions

- **Python 3.12+** - Minimum supported version
- **Python 3.13+** - Recommended for best performance and latest features

## Version Requirements

The project requires Python 3.12 or higher. This is specified in:
- `pyproject.toml` - `requires-python = ">=3.12"`
- `README.md` - Installation requirements

## Python 3.13 Compatibility

The codebase has been verified for Python 3.13 compatibility. All dependencies support Python 3.13:

- ✅ Flask >= 2.0.0
- ✅ SQLAlchemy >= 1.4.0
- ✅ Pandas >= 1.3.0
- ✅ Playwright >= 1.40.0
- ✅ All other dependencies

## Known Deprecation Warnings

### `datetime.utcnow()` Deprecation

The codebase uses `datetime.utcnow()` in several places, which is deprecated in Python 3.12+ and will be removed in Python 3.14. This generates deprecation warnings but does not affect functionality.

**Affected files:**
- `database/models.py` - Multiple model default values
- `web/app.py` - Template context processor
- `web/routes.py` - Multiple route handlers
- `extractor/url_to_markdown.py` - Content extraction
- `scripts/browser_crawl/batch_browser_crawler.py` - Batch crawling

**Future Migration:**
When Python 3.14 is released, these should be updated to use:
```python
from datetime import datetime, timezone
datetime.now(timezone.utc)  # Instead of datetime.utcnow()
```

## Testing Compatibility

To verify your Python version:

```bash
python --version
```

Should show Python 3.12.x or 3.13.x

You can also use the version check script:

```bash
python scripts/utils/check_python_version.py
```

This will verify your Python version meets the requirements and provide recommendations.

To test installation:

```bash
pip install -r requirements.txt
```

All dependencies should install successfully on Python 3.12+.

## Performance Benefits of Python 3.13

Python 3.13 includes several performance improvements:

- **JIT Compiler** - Just-In-Time compilation for improved performance
- **Faster Startup** - Reduced interpreter startup time
- **Free-threaded Build** - Experimental GIL-free mode for better concurrency
- **Improved Error Messages** - Better debugging experience

## Migration Notes

If upgrading from Python 3.8-3.11:

1. Update Python to 3.12+ or 3.13+
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Test the application: `python run.py`
4. Watch for deprecation warnings (non-breaking)

No code changes are required for Python 3.12/3.13 compatibility.
