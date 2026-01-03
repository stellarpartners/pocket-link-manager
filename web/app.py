"""
Flask application factory
"""

from flask import Flask, send_from_directory, make_response, request
from database.models import db, init_db_engine, get_db_path
import os
from functools import wraps
from datetime import datetime, timedelta

# Simple in-memory cache for frequently accessed data
_cache = {}
_cache_timestamps = {}

def create_app(config=None):
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['DATABASE_PATH'] = os.environ.get('DATABASE_PATH', get_db_path())
    app.config['JSON_AS_ASCII'] = False  # Support non-ASCII characters
    
    # Enable template caching in production
    app.config['TEMPLATES_AUTO_RELOAD'] = os.environ.get('FLASK_ENV') != 'production'
    
    # Initialize database
    db.init_app(app)
    
    # Add caching headers for static files
    @app.after_request
    def add_cache_headers(response):
        """Add cache headers to static files"""
        if response.status_code == 200:
            # Cache static files (CSS, JS, images) for 1 year
            if request.endpoint == 'static' or request.path.startswith('/static/'):
                cache_time = 31536000  # 1 year in seconds
                response.cache_control.max_age = cache_time
                response.cache_control.public = True
                response.expires = datetime.utcnow() + timedelta(seconds=cache_time)
            # Cache HTML pages for shorter time (5 minutes)
            elif response.content_type and 'text/html' in response.content_type:
                response.cache_control.max_age = 300  # 5 minutes
                response.cache_control.private = True
            # Cache API responses for 1 minute
            elif request.path.startswith('/api/'):
                response.cache_control.max_age = 60  # 1 minute
                response.cache_control.private = True
        return response
    
    # Add custom Jinja2 filters
    @app.template_filter('number_format')
    def number_format_filter(value):
        """Format number with commas"""
        if value is None:
            return '0'
        return f"{value:,}"
    
    # Add global variables to templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow}
    
    # Register blueprints
    from .routes import main_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    return app


def cache_result(expiration_seconds=300):
    """Decorator to cache function results in memory"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Check if cached and still valid
            if cache_key in _cache:
                timestamp = _cache_timestamps.get(cache_key, datetime.min)
                if datetime.utcnow() - timestamp < timedelta(seconds=expiration_seconds):
                    return _cache[cache_key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache[cache_key] = result
            _cache_timestamps[cache_key] = datetime.utcnow()
            
            return result
        return wrapper
    return decorator


def clear_cache(pattern=None):
    """Clear cache entries matching a pattern"""
    if pattern is None:
        _cache.clear()
        _cache_timestamps.clear()
    else:
        keys_to_remove = [k for k in _cache.keys() if pattern in k]
        for key in keys_to_remove:
            _cache.pop(key, None)
            _cache_timestamps.pop(key, None)
