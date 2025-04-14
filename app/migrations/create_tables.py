"""
Script to create all database tables

This script will create all database tables including the new chatbot models.
"""

from app import create_app
from app.models.models import db

def create_tables():
    """Create all database tables"""
    app = create_app()
    
    with app.app_context():
        db.create_all()
        print("All database tables created successfully!")

if __name__ == "__main__":
    create_tables() 