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
from app.models.models import db, User

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
        engine.execute(sql)
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
            db.engine.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME"))
            
            # Update the column with values from created_at
            db.engine.execute(text("UPDATE users SET updated_at = created_at"))
            
            print("Column updated_at added to users table")
        else:
            print("Column updated_at already exists in users table")
        
        # Update applications table
        app_columns = [c['name'] for c in inspector.get_columns('applications')]
        if 'updated_at' not in app_columns:
            print("Adding updated_at column to applications table...")
            
            # Add the column without a default
            db.engine.execute(text("ALTER TABLE applications ADD COLUMN updated_at DATETIME"))
            
            # Update the column with values from created_at
            db.engine.execute(text("UPDATE applications SET updated_at = created_at"))
            
            print("Column updated_at added to applications table")
        else:
            print("Column updated_at already exists in applications table")
        
        # Fix any null or invalid application status values
        print("Checking for invalid application status values...")
        try:
            # Check and fix applications with null status
            db.engine.execute(text("UPDATE applications SET status = 'pending' WHERE status IS NULL"))
            
            # Count status types for logging
            result = db.session.execute(text("SELECT status, COUNT(*) FROM applications GROUP BY status")).fetchall()
            
            status_counts = {}
            for row in result:
                status_counts[row[0]] = row[1]
            
            print(f"Application status distribution: {status_counts}")
            
            # Check for any match scores that are null and could be calculated
            null_score_count = db.session.execute(text("SELECT COUNT(*) FROM applications WHERE match_score IS NULL")).scalar()
            if null_score_count > 0:
                print(f"Found {null_score_count} applications with null match scores")
                
                # These will be updated when users view their applications
                
        except Exception as e:
            print(f"Error checking application statuses: {str(e)}")
        
        # Commit the changes
        db.session.commit()
        
        print("Database migration completed successfully!")

if __name__ == "__main__":
    run_migrations() 