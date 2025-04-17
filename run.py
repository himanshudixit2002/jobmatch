from app import create_app
from datetime import datetime
import os
from app.models.models import db
from flask import Flask

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

# Create database tables if they don't exist
# @app.before_first_request  # Deprecated in Flask 2.3+
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True) 