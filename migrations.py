#!/usr/bin/env python
"""
Database migration script for JobMatch

This script will update the database schema by adding new columns
and applying any necessary changes to existing data.
"""

import os
import sys
import sqlite3
from datetime import datetime
from sqlalchemy import inspect, text
from app import create_app, db
from app.models.models import User
from flask import Flask

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
    """Run all database migrations in order"""
    print("Running database migrations...")
    
    try:
        # First try the new migration approach
        migrate()
    except Exception as e:
        print(f"Error running new migrations: {e}")
        print("Falling back to original migration approach...")
        
        # Fall back to original migration approach
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

def get_connection():
    """Get a SQLite connection to the database"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'job_recruitment.db')
    return sqlite3.connect(db_path)

def upgrade_to_v1():
    """Initial migration to establish base schema"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create initial tables if they don't exist
    # ...implementation would go here
    
    # Update database version
    cursor.execute('PRAGMA user_version = 1')
    
    conn.commit()
    conn.close()

def upgrade_to_v2():
    """Add support for interviews"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create interviews table
    # ...implementation would go here
    
    # Update database version
    cursor.execute('PRAGMA user_version = 2')
    
    conn.commit()
    conn.close()

def upgrade_to_v3():
    """Add support for chat features"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create chat related tables
    # ...implementation would go here
    
    # Update database version
    cursor.execute('PRAGMA user_version = 3')
    
    conn.commit()
    conn.close()

def upgrade_to_v4():
    """Adds support for skill recommendations"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create skill_recommendations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS skill_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        skill_id INTEGER NOT NULL,
        relevance_score FLOAT NOT NULL,
        recommendation_reason TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_dismissed BOOLEAN DEFAULT 0,
        is_acquired BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (skill_id) REFERENCES skills (id) ON DELETE CASCADE
    )
    ''')
    
    # Update database version
    cursor.execute('PRAGMA user_version = 4')
    
    conn.commit()
    conn.close()

def upgrade_to_v5():
    """Rename candidate_id to applicant_id in interviews table"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if the interviews table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interviews'")
        if cursor.fetchone():
            # Check if the candidate_id column exists
            cursor.execute("PRAGMA table_info(interviews)")
            columns = cursor.fetchall()
            has_candidate_id = any(col[1] == 'candidate_id' for col in columns)
            has_applicant_id = any(col[1] == 'applicant_id' for col in columns)
            
            if has_candidate_id and not has_applicant_id:
                print("Renaming candidate_id to applicant_id in interviews table...")
                
                # SQLite doesn't directly support renaming columns, so we need to:
                # 1. Create a new table with the desired schema
                # 2. Copy data from the old table
                # 3. Drop the old table
                # 4. Rename the new table
                
                # Get the current table schema
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='interviews'")
                create_stmt = cursor.fetchone()[0]
                
                # Create a new table with the updated schema
                new_create_stmt = create_stmt.replace('candidate_id', 'applicant_id')
                cursor.execute(f"CREATE TABLE interviews_new AS SELECT * FROM interviews")
                
                # Rename the columns in the new table
                cursor.execute("PRAGMA table_info(interviews_new)")
                old_columns = [col[1] for col in cursor.fetchall()]
                
                # Drop the new table
                cursor.execute("DROP TABLE interviews_new")
                
                # Create the new table with correct schema
                cursor.execute(new_create_stmt.replace('CREATE TABLE interviews', 'CREATE TABLE interviews_new'))
                
                # Prepare column lists for the INSERT statement
                old_columns_str = ', '.join(old_columns)
                new_columns = [col if col != 'candidate_id' else 'applicant_id' for col in old_columns]
                new_columns_str = ', '.join(new_columns)
                
                # Copy the data
                cursor.execute(f"INSERT INTO interviews_new SELECT {old_columns_str} FROM interviews")
                
                # Drop the old table and rename the new one
                cursor.execute("DROP TABLE interviews")
                cursor.execute("ALTER TABLE interviews_new RENAME TO interviews")
                
                print("Successfully renamed candidate_id to applicant_id in interviews table")
            else:
                if has_applicant_id:
                    print("Column applicant_id already exists in interviews table")
                else:
                    print("Column candidate_id not found in interviews table")
        else:
            print("Table interviews does not exist, skipping migration")
    except Exception as e:
        print(f"Error renaming column: {e}")
        conn.rollback()
        raise
    
    # Update database version
    cursor.execute('PRAGMA user_version = 5')
    
    conn.commit()
    conn.close()

def upgrade_to_v6():
    """Rename start_time to scheduled_at and add duration column in interviews table"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if the interviews table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interviews'")
        if cursor.fetchone():
            # Check if start_time column exists and scheduled_at doesn't exist
            cursor.execute("PRAGMA table_info(interviews)")
            columns = cursor.fetchall()
            has_start_time = any(col[1] == 'start_time' for col in columns)
            has_end_time = any(col[1] == 'end_time' for col in columns)
            has_scheduled_at = any(col[1] == 'scheduled_at' for col in columns)
            has_duration = any(col[1] == 'duration' for col in columns)
            
            if has_start_time and not has_scheduled_at:
                print("Renaming start_time to scheduled_at and adding duration column in interviews table...")
                
                # SQLite doesn't directly support renaming columns, so we need to create a new table
                # 1. Create a backup of current table including schema
                # 2. Create new table with modified schema
                # 3. Copy data with column transformations
                # 4. Drop backup and rename tables
                
                # First, let's get a list of all the column names and their types
                cursor.execute("PRAGMA table_info(interviews)")
                columns_info = cursor.fetchall()
                columns = [(col[1], col[2]) for col in columns_info]  # name, type
                
                # Create a new schema string replacing start_time with scheduled_at
                # and end_time with duration
                new_columns = []
                old_columns = []
                for name, type in columns:
                    if name == 'start_time':
                        new_columns.append(('scheduled_at', type))
                        old_columns.append(name)
                    elif name == 'end_time':
                        new_columns.append(('duration', 'INTEGER NOT NULL DEFAULT 60'))
                        old_columns.append(name)
                    else:
                        new_columns.append((name, type))
                        old_columns.append(name)
                
                # Create the new table
                create_stmt = f"CREATE TABLE interviews_new ("
                create_stmt += ", ".join([f"{name} {type}" for name, type in new_columns])
                create_stmt += ")"
                
                cursor.execute(create_stmt)
                
                # Figure out how to map old columns to new ones
                mapping = {}
                for i, name in enumerate(old_columns):
                    if name == 'start_time':
                        mapping[i] = 'scheduled_at'
                    elif name == 'end_time':
                        mapping[i] = None  # Skip this column in the INSERT
                    else:
                        mapping[i] = name
                
                # Insert statement with mapping - excluding end_time
                insert_old_cols = []
                insert_new_cols = []
                for i, name in enumerate(old_columns):
                    if mapping[i] is not None:
                        insert_old_cols.append(name)
                        insert_new_cols.append(mapping[i])
                
                insert_stmt = f"INSERT INTO interviews_new ({', '.join(insert_new_cols)}) SELECT {', '.join(insert_old_cols)} FROM interviews"
                cursor.execute(insert_stmt)
                
                # Now calculate and set the duration based on end_time - start_time
                cursor.execute("SELECT id, start_time, end_time FROM interviews")
                for row in cursor.fetchall():
                    id, start_time, end_time = row
                    if start_time and end_time:
                        try:
                            # Convert strings to datetime objects
                            start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                            end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                            
                            # Calculate duration in minutes
                            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
                            
                            # Update the duration column
                            cursor.execute("UPDATE interviews_new SET duration = ? WHERE id = ?", (duration_minutes, id))
                        except Exception as e:
                            print(f"Error calculating duration for interview {id}: {e}")
                            # Set a default value
                            cursor.execute("UPDATE interviews_new SET duration = 60 WHERE id = ?", (id,))
                
                # Rename tables
                cursor.execute("DROP TABLE interviews")
                cursor.execute("ALTER TABLE interviews_new RENAME TO interviews")
                
                print("Successfully renamed start_time to scheduled_at and added duration column in interviews table")
            else:
                if has_scheduled_at:
                    print("Column scheduled_at already exists in interviews table")
                else:
                    print("Column start_time not found in interviews table")
        else:
            print("Table interviews does not exist, skipping migration")
    except Exception as e:
        print(f"Error updating schema: {e}")
        conn.rollback()
        raise
    
    # Update database version
    cursor.execute('PRAGMA user_version = 6')
    
    conn.commit()
    conn.close()

def get_current_version():
    """Get the current database version"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('PRAGMA user_version')
    version = cursor.fetchone()[0]
    conn.close()
    return version

def migrate():
    """Run necessary migrations to bring the database up to date"""
    version = get_current_version()
    
    if version < 1:
        upgrade_to_v1()
        version = 1
    
    if version < 2:
        upgrade_to_v2()
        version = 2
    
    if version < 3:
        upgrade_to_v3()
        version = 3
        
    if version < 4:
        upgrade_to_v4()
        version = 4
        
    if version < 5:
        upgrade_to_v5()
        version = 5
        
    if version < 6:
        upgrade_to_v6()
        version = 6
    
    print(f"Database is now at version {version}")

if __name__ == "__main__":
    run_migrations() 