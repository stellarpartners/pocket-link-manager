#!/usr/bin/env python3
"""
Run the Pocket Link Manager web application
"""

from web import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)
