"""
Flask application factory
"""

from flask import Flask
from database.models import db, init_db_engine, get_db_path
import os

def create_app(config=None):
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['DATABASE_PATH'] = os.environ.get('DATABASE_PATH', get_db_path())
    app.config['JSON_AS_ASCII'] = False  # Support non-ASCII characters
    
    # Initialize database
    db.init_app(app)
    
    # Add custom Jinja2 filters
    @app.template_filter('number_format')
    def number_format_filter(value):
        """Format number with commas"""
        if value is None:
            return '0'
        return f"{value:,}"
    
    # Add global variables to templates
    from datetime import datetime
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
