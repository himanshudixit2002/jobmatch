from app import create_app
from datetime import datetime
import os
from app.models.models import db, User
from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = create_app()

# Add current year to Jinja2 global context for footer
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Add nl2br filter for newlines in job descriptions
@app.template_filter('nl2br')
def nl2br(value):
    if value:
        return value.replace('\n', '<br>')
    return ''

# Create database tables only if they don't exist
with app.app_context():
    # Try to query the User table to check if it exists
    try:
        User.query.first()
        print("Database tables already exist, skipping creation")
    except:
        # If the table doesn't exist, create all tables
        print("Creating database tables...")
        db.create_all()

if __name__ == '__main__':
    # Get configuration from environment variables
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() in ['true', 'yes', '1']
    
    print(f"Starting JobMatch with Gemini AI integration...")
    if os.environ.get('GEMINI_API_KEY'):
        print("✓ Gemini API key found - AI features enabled")
    else:
        print("⚠ Gemini API key not found - AI features will use fallback mode")
    
    app.run(host=host, port=port, debug=debug) 