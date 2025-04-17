from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app.models.models import User, Skill, Job, SkillRecommendation, job_skills, user_skills
from app.extensions import db
from sqlalchemy import func, desc
from app.utils.gemini_ai import get_ai_skill_recommendation, get_skill_details
from app.utils.ai_helpers import get_skill_details_from_ai, get_skill_recommendations
from app.utils.skill_recommendations import get_fallback_recommendations, get_fallback_skill_details
import numpy as np
from collections import Counter
import logging

# Set up logging
logger = logging.getLogger(__name__)

skills = Blueprint('skills', __name__)

@skills.route('/recommendations')
@login_required
def recommendations():
    """Show skill recommendations for the user"""
    # Fetch active (not dismissed, not acquired) recommendations for the user
    active_recommendations = SkillRecommendation.query.filter_by(
        user_id=current_user.id,
        is_dismissed=False,
        is_acquired=False
    ).all()
    
    # Fetch acquired recommendations
    acquired_recommendations = SkillRecommendation.query.filter_by(
        user_id=current_user.id,
        is_acquired=True
    ).all()
    
    # Check if the Gemini API is configured
    gemini_api_available = current_app.config.get('GEMINI_API_KEY') is not None
    
    return render_template(
        'skills/recommendations.html',
        active_recommendations=active_recommendations,
        acquired_recommendations=acquired_recommendations,
        has_recommendations=bool(active_recommendations or acquired_recommendations),
        gemini_api_available=gemini_api_available
    )

@skills.route('/generate_recommendations', methods=['POST'])
@login_required
def generate_recommendations():
    """Generate skill recommendations for the user based on job market and user profile"""
    try:
        # Check if user has skills first
        if not current_user.skills:
            flash('Please add some skills to your profile before generating recommendations.', 'warning')
            return redirect(url_for('skills.recommendations'))
        
        # Get current user jobs of interest to use as context
        jobs_of_interest = [job.title for job in current_user.jobs_of_interest]
        
        if not jobs_of_interest:
            flash('Please add some jobs of interest to your profile first.', 'warning')
            return redirect(url_for('skills.recommendations'))
        
        # Get current user skills to avoid recommending what they already know
        user_skill_names = [skill.skill.name for skill in current_user.skills]
        
        # Try to get AI-powered recommendations using Gemini API
        try:
            logger.info(f"Generating AI recommendations for user {current_user.id}")
            
            # Check if Gemini API is configured
            if not current_app.config.get('GEMINI_API_KEY'):
                logger.warning("Gemini API key not found in configuration")
                raise Exception("Gemini API is not configured")
                
            recommendations = get_skill_recommendations(
                current_user_skills=user_skill_names,
                jobs_of_interest=jobs_of_interest,
                experience_level=current_user.experience_level or "Entry-level"
            )
            
            logger.info(f"Successfully generated {len(recommendations)} AI recommendations")
            
            # Clear previous not-acquired recommendations
            SkillRecommendation.query.filter_by(
                user_id=current_user.id, 
                is_acquired=False
            ).delete()
            
            # Create new recommendations
            for rec in recommendations:
                # Check if skill exists, create if not
                skill = Skill.query.filter_by(name=rec['skill_name']).first()
                if not skill:
                    skill = Skill(name=rec['skill_name'])
                    db.session.add(skill)
                    db.session.flush()  # Generate ID without committing
                
                # Create recommendation
                recommendation = SkillRecommendation(
                    user_id=current_user.id,
                    skill_id=skill.id,
                    recommendation_reason=rec['reason'],
                    relevance_score=rec['relevance_score']
                )
                db.session.add(recommendation)
            
            db.session.commit()
            flash('Successfully generated skill recommendations!', 'success')
            
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {str(e)}", exc_info=True)
            logger.info("Using fallback recommendation algorithm")
            flash('Could not generate AI recommendations. Using fallback method.', 'warning')
            
            # Use the fallback recommendation generator
            try:
                filtered_skills = get_fallback_recommendations(
                    user_skills=user_skill_names,
                    job_interests=jobs_of_interest,
                    count=8
                )
                
                # Clear previous not-acquired recommendations
                SkillRecommendation.query.filter_by(
                    user_id=current_user.id, 
                    is_acquired=False
                ).delete()
                
                # Create new recommendations
                for rec in filtered_skills:
                    # Check if skill exists, create if not
                    skill = Skill.query.filter_by(name=rec['name']).first()
                    if not skill:
                        skill = Skill(name=rec['name'])
                        db.session.add(skill)
                        db.session.flush()  # Generate ID without committing
                    
                    # Create recommendation with fallback scores
                    recommendation = SkillRecommendation(
                        user_id=current_user.id,
                        skill_id=skill.id,
                        recommendation_reason=rec['reason'],
                        relevance_score=rec['relevance_score']
                    )
                    db.session.add(recommendation)
                
                db.session.commit()
                logger.info(f"Successfully created {len(filtered_skills)} fallback recommendations")
                
            except Exception as fallback_error:
                logger.error(f"Error in fallback recommendation system: {str(fallback_error)}", exc_info=True)
                # If even the fallback fails, use the most basic approach
                common_skills = [
                    {"name": "SQL", "reason": "Database query skills are in high demand"},
                    {"name": "Python", "reason": "Versatile programming language used in many domains"},
                    {"name": "Data Analysis", "reason": "Valuable across multiple industries"},
                    {"name": "Project Management", "reason": "Essential for team coordination and delivery"},
                    {"name": "React", "reason": "Popular front-end framework with growing demand"},
                    {"name": "DevOps", "reason": "Important for modern software delivery"},
                ]
                
                # Filter out skills the user already has
                filtered_skills = [s for s in common_skills if s["name"] not in user_skill_names]
            
            if not filtered_skills:
                flash('You already have all the common skills we typically recommend. Try exploring more specialized skills in your field.', 'info')
                return redirect(url_for('skills.recommendations'))
            
            # Clear previous not-acquired recommendations
            SkillRecommendation.query.filter_by(
                user_id=current_user.id, 
                is_acquired=False
            ).delete()
            
            # Create new recommendations
            for idx, rec in enumerate(filtered_skills):
                # Check if skill exists, create if not
                skill = Skill.query.filter_by(name=rec['name']).first()
                if not skill:
                    skill = Skill(name=rec['name'])
                    db.session.add(skill)
                    db.session.flush()  # Generate ID without committing
                
                # Create recommendation with fallback scores
                recommendation = SkillRecommendation(
                    user_id=current_user.id,
                    skill_id=skill.id,
                    recommendation_reason=rec['reason'],
                    relevance_score=90 - (idx * 5)  # Simple decreasing score
                )
                db.session.add(recommendation)
            
            db.session.commit()
        
        return redirect(url_for('skills.recommendations'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in generate_recommendations: {str(e)}", exc_info=True)
        flash('An error occurred while generating recommendations. Please try again later.', 'danger')
        return redirect(url_for('skills.recommendations'))

@skills.route('/recommendations/<int:recommendation_id>/dismiss', methods=['POST'])
@login_required
def dismiss_recommendation(recommendation_id):
    """Dismiss a skill recommendation"""
    recommendation = SkillRecommendation.query.filter_by(
        id=recommendation_id, 
        user_id=current_user.id
    ).first_or_404()
    
    recommendation.is_dismissed = True
    db.session.commit()
    
    return jsonify({'success': True})

@skills.route('/recommendations/<int:recommendation_id>/acquire', methods=['POST'])
@login_required
def acquire_recommendation(recommendation_id):
    """Mark a recommendation as acquired and add the skill to user's profile"""
    recommendation = SkillRecommendation.query.filter_by(
        id=recommendation_id, 
        user_id=current_user.id
    ).first_or_404()
    
    # Get the skill
    skill = Skill.query.get(recommendation.skill_id)
    
    # Check if user already has this skill
    if skill not in current_user.skills:
        # Add skill to user's profile using the relationship
        current_user.skills.append(skill)
    
    # Mark recommendation as acquired
    recommendation.is_acquired = True
    db.session.commit()
    
    return jsonify({'success': True})

@skills.route('/skill-details/<int:skill_id>')
@login_required
def skill_details(skill_id):
    """Get detailed information about a skill"""
    skill = Skill.query.get_or_404(skill_id)
    
    try:
        # Check if Gemini API is configured
        if current_app.config.get('GEMINI_API_KEY'):
            # Try to get AI-enhanced details
            skill_details = get_skill_details_from_ai(skill.name)
        else:
            # Use fallback if API is not configured
            logger.info(f"Using fallback for skill details: {skill.name}")
            skill_details = get_fallback_skill_details(skill.name)
        
        return jsonify({
            'name': skill.name,
            'description': skill_details.get('description', 'No description available.'),
            'market_value': skill_details.get('market_value', 'Information not available.'),
            'learning_time': skill_details.get('learning_time', 'Varies based on experience.'),
            'resources': skill_details.get('resources', [])
        })
    except Exception as e:
        logger.error(f"Error getting skill details for {skill.name}: {str(e)}", exc_info=True)
        # Return basic information if AI enhancement fails
        fallback_details = get_fallback_skill_details(skill.name)
        return jsonify({
            'name': skill.name,
            'description': fallback_details['description'],
            'market_value': fallback_details['market_value'],
            'learning_time': fallback_details['learning_time'],
            'resources': fallback_details['resources'],
            'error': 'Some advanced information is temporarily unavailable'
        })

@skills.route('/api/skill-info', methods=['GET', 'POST'])
@login_required
def api_skill_info():
    """API endpoint to get information about a skill by name"""
    # Get skill name from either GET parameters or POST JSON
    if request.method == 'POST':
        data = request.get_json()
        skill_name = data.get('skill_name') if data else None
    else:
        skill_name = request.args.get('name')
    
    if not skill_name:
        return jsonify({
            'success': False,
            'error': 'Missing skill name parameter'
        }), 400
    
    skill = Skill.query.filter_by(name=skill_name).first()
    
    if not skill:
        return jsonify({
            'success': False,
            'error': 'Skill not found'
        }), 404
    
    try:
        # Check if Gemini API is configured
        if current_app.config.get('GEMINI_API_KEY'):
            # Try to get AI-enhanced details
            skill_details = get_skill_details_from_ai(skill.name)
        else:
            # Use fallback if API is not configured
            logger.info(f"Using fallback for skill API info: {skill.name}")
            skill_details = get_fallback_skill_details(skill.name)
        
        return jsonify({
            'success': True,
            'name': skill.name,
            'description': skill_details.get('description', 'No description available.'),
            'market_value': skill_details.get('market_value', 'Information not available.'),
            'learning_time': skill_details.get('learning_time', 'Varies based on experience.'),
            'resources': skill_details.get('resources', [])
        })
    except Exception as e:
        logger.error(f"Error getting API skill info for {skill.name}: {str(e)}", exc_info=True)
        # Return basic information if AI enhancement fails
        fallback_details = get_fallback_skill_details(skill.name)
        return jsonify({
            'success': True,
            'name': skill.name,
            'description': fallback_details['description'],
            'market_value': fallback_details['market_value'],
            'learning_time': fallback_details['learning_time'],
            'resources': fallback_details['resources'],
            'note': 'Using fallback information system'
        })

@skills.route('/trending')
def trending_skills():
    """Display trending skills based on recent job postings"""
    try:
        # In a real application, this would be determined dynamically
        # based on job posting analysis or external API data
        trending_skills = [
            {"name": "Machine Learning", "growth": 43, "jobs_count": 2500, "count": 2500},
            {"name": "React", "growth": 38, "jobs_count": 5600, "count": 5600},
            {"name": "DevOps", "growth": 35, "jobs_count": 3200, "count": 3200},
            {"name": "Data Science", "growth": 30, "jobs_count": 4100, "count": 4100},
            {"name": "Cloud Computing", "growth": 28, "jobs_count": 6800, "count": 6800},
            {"name": "Cybersecurity", "growth": 25, "jobs_count": 3900, "count": 3900},
            {"name": "UI/UX Design", "growth": 22, "jobs_count": 2800, "count": 2800},
            {"name": "Node.js", "growth": 20, "jobs_count": 3500, "count": 3500},
        ]
        
        return render_template(
            'skills/trending.html',
            trending_skills=trending_skills
        )
    except Exception as e:
        logger.error(f"Error in trending_skills: {str(e)}", exc_info=True)
        flash('An error occurred while fetching trending skills. Please try again later.', 'danger')
        return redirect(url_for('main.index')) 