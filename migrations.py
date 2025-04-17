#!/usr/bin/env python
"""
Database migration script for JobMatch

This script will update the database schema by adding new columns
and applying any necessary changes to existing data.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import inspect, text
from app import create_app
from app.models.models import User
from app.extensions import db

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.getcwd()))

def add_column(engine, table_name, column):
    """Add a column to a table if it doesn't exist"""
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    
    if column.name not in columns:
        column_name = column.name
        column_type = column.type.compile(engine.dialect)
        
        # Handle default values
        if column.default is not None:
            if column.default.is_callable:
                default_value = "DEFAULT CURRENT_TIMESTAMP"
            else:
                default_value = f"DEFAULT '{column.default.arg}'"
        else:
            default_value = ""
            
        # Handle nullability
        nullable = "" if column.nullable else "NOT NULL"
        
        # Build the SQL statement
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} {nullable} {default_value}"
        with engine.connect() as conn:
            conn.execute(text(sql))
        print(f"Added column {column_name} to {table_name}")
    else:
        print(f"Column {column.name} already exists in {table_name}")

def run_migrations():
    """Run all database migrations"""
    print("Starting database migrations...")
    
    app = create_app()
    with app.app_context():
        # For SQLite, we need to use a different approach for adding columns with defaults
        inspector = inspect(db.engine)
        
        # Update users table
        user_columns = [c['name'] for c in inspector.get_columns('users')]
        if 'updated_at' not in user_columns:
            print("Adding updated_at column to users table...")
            
            # Add the column without a default
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME"))
                
                # Update the column with values from created_at
                conn.execute(text("UPDATE users SET updated_at = created_at"))
            
            print("Column updated_at added to users table")
        else:
            print("Column updated_at already exists in users table")
        
        # Add profile_completed column to users table
        if 'profile_completed' not in user_columns:
            print("Adding profile_completed column to users table...")
            
            # Add the column with a default value of 0 (false)
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN profile_completed BOOLEAN DEFAULT 0 NOT NULL"))
            
            print("Column profile_completed added to users table")
        else:
            print("Column profile_completed already exists in users table")
        
        # Update applications table
        app_columns = [c['name'] for c in inspector.get_columns('applications')]
        if 'updated_at' not in app_columns:
            print("Adding updated_at column to applications table...")
            
            # Add the column without a default
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE applications ADD COLUMN updated_at DATETIME"))
                
                # Update the column with values from created_at
                conn.execute(text("UPDATE applications SET updated_at = created_at"))
            
            print("Column updated_at added to applications table")
        else:
            print("Column updated_at already exists in applications table")
        
        # Fix any null or invalid application status values
        print("Checking for invalid application status values...")
        with db.engine.connect() as conn:
            conn.execute(text("UPDATE applications SET status = 'pending' WHERE status IS NULL OR status = ''"))
        
        print("Database migration completed successfully!")

if __name__ == "__main__":
    run_migrations() 