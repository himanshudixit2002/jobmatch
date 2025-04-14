"""
Interview Management Routes for JobMatch

This module handles routes related to scheduling, managing, and conducting job interviews.
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, abort, send_file
from flask_login import login_required, current_user
from app.models.models import Job, Application, Interview, User
from app.models.user import Role
from app.models.job import JobApplication
from app.models.interview import InterviewFeedback
from app.extensions import db
from datetime import datetime, timedelta
import pytz
from app.decorators import recruiter_required, interviewer_required
from app.utils.email import send_interview_invitation, send_interview_reminder, send_interview_feedback_notification
from app.utils.calendar import generate_calendar_invite
import io

interviews = Blueprint('interviews', __name__, url_prefix='/interviews')

@interviews.route('/')
@login_required
def index():
    """Main interviews dashboard view"""
    if current_user.type == 'recruiter':
        # Fetch interviews scheduled by this recruiter
        return render_template('interviews/recruiter_dashboard.html', title='Manage Interviews')
    else:
        # Fetch interviews for this applicant
        return render_template('interviews/applicant_dashboard.html', title='My Interviews')

@interviews.route('/schedule/<int:application_id>', methods=['GET', 'POST'])
@login_required
def schedule_interview(application_id):
    """Schedule an interview for a job application"""
    if current_user.type != 'recruiter':
        flash('Only recruiters can schedule interviews', 'danger')
        return redirect(url_for('main.index'))
    
    # In a real app, we would validate that the application belongs to a job posted by this recruiter
    
    if request.method == 'POST':
        # Process the form submission to schedule an interview
        # In a real app, this would create an Interview record in the database
        flash('Interview scheduled successfully', 'success')
        return redirect(url_for('interviews.index'))
    
    # Display the form to schedule an interview
    return render_template('interviews/schedule.html', title='Schedule Interview', application_id=application_id)

@interviews.route('/<int:interview_id>')
@login_required
def view_interview(interview_id):
    """View details of a specific interview"""
    # In a real app, fetch the interview from the database and check if the current user is authorized to view it
    return render_template('interviews/view.html', title='Interview Details', interview_id=interview_id)

@interviews.route('/<int:interview_id>/reschedule', methods=['GET', 'POST'])
@login_required
def reschedule_interview(interview_id):
    """Reschedule an existing interview"""
    # In a real app, fetch the interview from the database and check if the current user is authorized to reschedule it
    
    if request.method == 'POST':
        # Process the form submission to reschedule the interview
        flash('Interview rescheduled successfully', 'success')
        return redirect(url_for('interviews.view_interview', interview_id=interview_id))
    
    return render_template('interviews/reschedule.html', title='Reschedule Interview', interview_id=interview_id)

@interviews.route('/<int:interview_id>/cancel')
@login_required
def cancel_interview(interview_id):
    """Cancel an existing interview"""
    # In a real app, fetch the interview from the database and check if the current user is authorized to cancel it
    
    # Process the cancellation
    flash('Interview cancelled', 'info')
    return redirect(url_for('interviews.index'))

@interviews.route('/<int:interview_id>/feedback', methods=['GET', 'POST'])
@login_required
def interview_feedback(interview_id):
    """Submit feedback for an interview (for recruiters)"""
    if current_user.type != 'recruiter':
        flash('Only recruiters can submit interview feedback', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Process the form submission for interview feedback
        flash('Feedback submitted successfully', 'success')
        return redirect(url_for('interviews.view_interview', interview_id=interview_id))
    
    return render_template('interviews/feedback.html', title='Interview Feedback', interview_id=interview_id)

@interviews.route('/upcoming')
@login_required
def upcoming_interviews():
    """View all upcoming interviews"""
    # In a real app, fetch upcoming interviews from the database based on current user type
    return render_template('interviews/upcoming.html', title='Upcoming Interviews')

@interviews.route('/past')
@login_required
def past_interviews():
    """View all past interviews"""
    # In a real app, fetch past interviews from the database based on current user type
    return render_template('interviews/past.html', title='Past Interviews')

# API endpoints for calendar and scheduling

@interviews.route('/api/calendar-data')
@login_required
def calendar_data():
    """API endpoint for calendar view of interviews"""
    # In a real app, this would fetch actual interview data from the database
    # Mock data for demonstration
    calendar_events = [
        {
            "id": 1,
            "title": "Interview with XYZ Corp",
            "start": "2023-07-15T10:00:00",
            "end": "2023-07-15T11:00:00",
            "url": "/interviews/1"
        },
        {
            "id": 2,
            "title": "Technical Assessment",
            "start": "2023-07-18T14:00:00",
            "end": "2023-07-18T15:30:00",
            "url": "/interviews/2"
        }
    ]
    
    return jsonify(calendar_events)

@interviews.route('/api/available-times/<int:job_id>/<date>')
@login_required
def available_times(job_id, date):
    """API endpoint to get available interview time slots for a given date"""
    # In a real app, this would check the recruiter's calendar and return available slots
    # Mock data for demonstration
    available_slots = [
        {"start": "09:00", "end": "10:00"},
        {"start": "10:30", "end": "11:30"},
        {"start": "13:00", "end": "14:00"},
        {"start": "14:30", "end": "15:30"},
        {"start": "16:00", "end": "17:00"}
    ]
    
    return jsonify(available_slots) 