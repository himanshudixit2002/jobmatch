"""
Migration script to add advanced features to JobMatch

This script adds the necessary tables for:
1. Automated interview scheduling
2. Market insights and analytics
"""

import sqlite3
import os
from datetime import datetime

def migrate():
    """Run migrations to add advanced features"""
    # Connect to database
    db_path = os.path.join('app', 'job_recruitment.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting migration for advanced features...")
    
    # Add interviews table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interviews (
        id TEXT PRIMARY KEY,
        job_id INTEGER NOT NULL,
        recruiter_id INTEGER NOT NULL,
        applicant_id INTEGER NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'scheduled',
        interview_type TEXT NOT NULL,
        location TEXT,
        video_link TEXT,
        notes TEXT,
        cancellation_reason TEXT,
        FOREIGN KEY (job_id) REFERENCES jobs (id),
        FOREIGN KEY (recruiter_id) REFERENCES users (id),
        FOREIGN KEY (applicant_id) REFERENCES users (id)
    )
    ''')
    
    # Add job market analytics table to store historical data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS job_market_trends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_name TEXT NOT NULL,
        job_count INTEGER NOT NULL,
        average_salary REAL,
        growth_rate REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Add table for user skill gap analysis
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS skill_gap_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        job_id INTEGER,
        analysis_data TEXT NOT NULL,  -- JSON data with analysis results
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (job_id) REFERENCES jobs (id)
    )
    ''')
    
    # Add table for learning recommendations
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS learning_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        skill_name TEXT NOT NULL,
        course_title TEXT NOT NULL,
        course_url TEXT NOT NULL,
        platform TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Add industry data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS industry_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        industry_name TEXT NOT NULL,
        job_openings INTEGER NOT NULL,
        growth_percentage REAL,
        avg_salary REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Seed some initial market data for testing
    skills = [
        ("Python", 250, 95000, 15.2),
        ("JavaScript", 220, 92000, 12.8),
        ("React", 180, 98000, 18.5),
        ("SQL", 150, 88000, 8.6),
        ("AWS", 140, 105000, 22.1),
        ("Machine Learning", 130, 110000, 25.4),
        ("Docker", 120, 96000, 20.7),
        ("Node.js", 110, 94000, 14.3),
        ("Java", 100, 90000, 5.2),
        ("C#", 90, 92000, 4.8)
    ]
    
    industries = [
        ("Technology", 45000, 8.5, 98000),
        ("Healthcare", 38000, 6.2, 85000),
        ("Finance", 25000, 4.1, 105000),
        ("Education", 22000, 3.8, 65000),
        ("Manufacturing", 18000, 2.5, 72000),
        ("Retail", 16000, 2.2, 58000),
        ("Construction", 20000, 3.6, 68000),
        ("Energy", 17000, 2.8, 95000),
        ("Media & Entertainment", 19000, 3.2, 82000),
        ("Hospitality", 12000, 1.5, 55000)
    ]
    
    # Insert sample market data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM job_market_trends")
    if cursor.fetchone()[0] == 0:
        for skill in skills:
            cursor.execute('''
            INSERT INTO job_market_trends (skill_name, job_count, average_salary, growth_rate)
            VALUES (?, ?, ?, ?)
            ''', skill)
    
    cursor.execute("SELECT COUNT(*) FROM industry_data")
    if cursor.fetchone()[0] == 0:
        for industry in industries:
            cursor.execute('''
            INSERT INTO industry_data (industry_name, job_openings, growth_percentage, avg_salary)
            VALUES (?, ?, ?, ?)
            ''', industry)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Migration for advanced features completed successfully!")

if __name__ == "__main__":
    migrate() 