"""
Market Insights Routes for JobMatch

This module handles routes related to job market insights and analytics.
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models.models import Job, Skill, Application, User

insights = Blueprint('insights', __name__, url_prefix='/insights')

@insights.route('/')
@login_required
def dashboard():
    """Main insights dashboard view"""
    return render_template('insights/dashboard.html', title='Job Market Insights')

@insights.route('/trending-skills')
@login_required
def trending_skills():
    """View for trending skills in the job market"""
    # In a real app, this would fetch actual data from the database
    # For now, we'll return mock data
    return render_template('insights/trending_skills.html', title='Trending Skills')

@insights.route('/salary-data')
@login_required
def salary_data():
    """View for salary data and trends"""
    return render_template('insights/salary_data.html', title='Salary Insights')

@insights.route('/career-paths')
@login_required
def career_paths():
    """View for career path visualization"""
    return render_template('insights/career_paths.html', title='Career Path Explorer')

@insights.route('/job-growth')
@login_required
def job_growth():
    """View for job growth by industry and location"""
    return render_template('insights/job_growth.html', title='Job Market Growth')

# API endpoints for fetching chart data

@insights.route('/api/trending-skills-data')
@login_required
def trending_skills_data():
    """API endpoint for trending skills data for charts"""
    # In a real application, this would query the database for actual trending skills data
    
    # Mock data for demonstration
    skills_data = {
        "skills": [
            "Python", "React", "AWS", "Data Science", "Machine Learning", 
            "JavaScript", "Docker", "SQL", "Java", "Node.js"
        ],
        "job_counts": [250, 220, 210, 180, 175, 160, 150, 140, 130, 120],
        "growth_rate": [15, 22, 18, 25, 30, 8, 20, 5, 3, 12]  # percentage growth YoY
    }
    
    return jsonify(skills_data)

@insights.route('/api/salary-range-data')
@login_required
def salary_range_data():
    """API endpoint for salary range data for charts"""
    # Mock salary data by role
    salary_data = {
        "roles": [
            "Software Developer", "Data Scientist", "Product Manager",
            "DevOps Engineer", "UX Designer", "Project Manager",
            "Marketing Specialist", "Sales Manager", "Financial Analyst",
            "HR Specialist"
        ],
        "median_salary": [
            85000, 95000, 110000, 92000, 80000, 
            88000, 65000, 82000, 75000, 62000
        ],
        "salary_range_low": [
            65000, 75000, 85000, 75000, 60000,
            70000, 50000, 65000, 60000, 48000
        ],
        "salary_range_high": [
            120000, 130000, 150000, 125000, 110000,
            120000, 85000, 110000, 95000, 80000
        ]
    }
    
    return jsonify(salary_data)

@insights.route('/api/job-market-growth')
@login_required
def job_market_growth_data():
    """API endpoint for job market growth data by industry"""
    # Mock job growth data by industry
    growth_data = {
        "industries": [
            "Technology", "Healthcare", "Finance", "Education",
            "Manufacturing", "Retail", "Construction", "Energy",
            "Media & Entertainment", "Hospitality"
        ],
        "growth_percentage": [
            8.5, 6.2, 4.1, 3.8, 2.5, 2.2, 3.6, 2.8, 3.2, 1.5
        ],
        "job_openings": [
            45000, 38000, 25000, 22000, 18000, 
            16000, 20000, 17000, 19000, 12000
        ]
    }
    
    return jsonify(growth_data)

@insights.route('/api/user-skill-gap')
@login_required
def user_skill_gap():
    """API endpoint for user's personal skill gap analysis relative to market demand"""
    # This would typically fetch the user's skills and compare with in-demand skills
    # For now, we'll return mock data
    
    # Mock data: User's skills vs market demand
    user_skill_gap_data = {
        "user_skills": ["Python", "JavaScript", "HTML/CSS", "React", "SQL"],
        "market_demand": {
            "Python": 85,  # percentile of market demand
            "JavaScript": 90,
            "HTML/CSS": 75,
            "React": 88,
            "SQL": 80,
            "AWS": 92,  # skill user doesn't have
            "Docker": 86,  # skill user doesn't have
            "Machine Learning": 89  # skill user doesn't have
        },
        "recommended_skills": ["AWS", "Docker", "Machine Learning"],
        "skill_gap_score": 72  # percentage match with market demand
    }
    
    return jsonify(user_skill_gap_data)

@insights.route('/api/career-path-data')
@login_required
def career_path_data():
    """API endpoint for career path visualization data"""
    # Mock career path data
    if current_user.type == 'applicant':
        # Get current user's role or provide a default
        current_role = "Software Developer"  # This should come from user profile in a real app
        
        # Career progression data for the user's role
        career_data = {
            "current_role": current_role,
            "paths": [
                {
                    "name": "Technical Track",
                    "progression": [
                        {"role": "Junior Developer", "level": 1, "median_salary": 65000},
                        {"role": "Software Developer", "level": 2, "median_salary": 85000},
                        {"role": "Senior Developer", "level": 3, "median_salary": 110000},
                        {"role": "Lead Developer", "level": 4, "median_salary": 130000},
                        {"role": "Software Architect", "level": 5, "median_salary": 150000},
                        {"role": "Chief Technology Officer", "level": 6, "median_salary": 180000}
                    ]
                },
                {
                    "name": "Management Track",
                    "progression": [
                        {"role": "Junior Developer", "level": 1, "median_salary": 65000},
                        {"role": "Software Developer", "level": 2, "median_salary": 85000},
                        {"role": "Team Lead", "level": 3, "median_salary": 105000},
                        {"role": "Engineering Manager", "level": 4, "median_salary": 125000},
                        {"role": "Director of Engineering", "level": 5, "median_salary": 160000},
                        {"role": "VP of Engineering", "level": 6, "median_salary": 190000}
                    ]
                }
            ],
            "skills_needed": {
                "Senior Developer": ["Advanced JavaScript", "System Design", "CI/CD", "Mentorship"],
                "Lead Developer": ["Architecture Design", "Technical Leadership", "Project Management"],
                "Team Lead": ["People Management", "Project Planning", "Performance Reviews"],
                "Engineering Manager": ["Resource Allocation", "Budgeting", "Strategic Planning"]
            }
        }
        
        return jsonify(career_data)
    else:
        # For recruiters, provide overall career trend data
        return jsonify({"error": "Career path data for recruiters not yet implemented"}) 