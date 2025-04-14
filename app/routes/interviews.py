"""
Interview Management Routes for JobMatch

This module handles routes related to scheduling, managing, and conducting job interviews.
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, abort, send_file
from flask_login import login_required, current_user
from app.models.models import Job, Application, Interview, User
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
    interview = Interview.query.get_or_404(interview_id)
    
    # Check permissions
    if current_user.is_recruiter():
        if (current_user.id != interview.created_by_id and 
            current_user.id not in interview.interviewer_ids):
            abort(403)
    elif current_user.id != interview.candidate_id:
        abort(403)
    
    return render_template('interviews/view.html', 
                          title='Interview Details', 
                          interview=interview)

@interviews.route('/<int:interview_id>/reschedule', methods=['GET', 'POST'])
@login_required
def reschedule_interview(interview_id):
    """Reschedule an existing interview"""
    interview = Interview.query.get_or_404(interview_id)
    
    # Check permissions
    if current_user.id != interview.created_by_id:
        flash('You do not have permission to reschedule this interview', 'danger')
        return redirect(url_for('interviews.view_interview', interview_id=interview.id))
    
    if interview.status not in ['scheduled', 'rescheduled']:
        flash('This interview cannot be rescheduled', 'warning')
        return redirect(url_for('interviews.view_interview', interview_id=interview.id))
    
    if request.method == 'POST':
        # Update interview time
        interview.scheduled_at = datetime.strptime(
            f"{request.form.get('interview_date')} {request.form.get('interview_time')}", 
            '%Y-%m-%d %H:%M'
        )
        interview.duration = int(request.form.get('duration', 60))
        interview.status = 'rescheduled'
        interview.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send notification
        # send_interview_reminder(interview)
        
        flash('Interview rescheduled successfully', 'success')
        return redirect(url_for('interviews.view_interview', interview_id=interview.id))
    
    return render_template('interviews/reschedule.html', 
                          title='Reschedule Interview', 
                          interview=interview)

@interviews.route('/<int:interview_id>/cancel', methods=['POST'])
@login_required
def cancel_interview(interview_id):
    """Cancel an existing interview"""
    interview = Interview.query.get_or_404(interview_id)
    
    # Check permissions
    if current_user.is_recruiter():
        if current_user.id != interview.created_by_id:
            flash('You do not have permission to cancel this interview', 'danger')
            return redirect(url_for('interviews.view_interview', interview_id=interview.id))
    elif current_user.id != interview.candidate_id:
        abort(403)
    
    if interview.status not in ['scheduled', 'rescheduled']:
        flash('This interview cannot be cancelled', 'warning')
        return redirect(url_for('interviews.view_interview', interview_id=interview.id))
    
    # Update interview status
    interview.status = 'cancelled'
    interview.cancelled_at = datetime.utcnow()
    interview.cancelled_by_id = current_user.id
    interview.cancellation_reason = request.form.get('cancellation_reason', '')
    
    db.session.commit()
    
    flash('Interview cancelled', 'info')
    return redirect(url_for('interviews.index'))

@interviews.route('/<int:interview_id>/feedback', methods=['GET', 'POST'])
@login_required
@interviewer_required
def submit_feedback(interview_id):
    """Submit feedback for an interview"""
    interview = Interview.query.get_or_404(interview_id)
    
    # Check if the user is authorized to submit feedback
    if current_user.id not in interview.interviewer_ids and current_user.id != interview.created_by_id:
        flash('You are not authorized to submit feedback for this interview', 'danger')
        return redirect(url_for('interviews.index'))
    
    # Check if the interview is completed
    if interview.status != 'completed':
        flash('You can only submit feedback for completed interviews', 'warning')
        return redirect(url_for('interviews.view_interview', interview_id=interview.id))
    
    # Check if feedback already exists
    existing_feedback = InterviewFeedback.query.filter_by(
        interview_id=interview.id, submitted_by_id=current_user.id
    ).first()
    
    if request.method == 'POST':
        data = {
            'interview_id': interview.id,
            'submitted_by_id': current_user.id,
            'overall_rating': int(request.form.get('overall_rating')),
            'recommendation': request.form.get('recommendation'),
            'strengths': request.form.get('strengths'),
            'areas_for_improvement': request.form.get('areas_for_improvement'),
            'cultural_fit': request.form.get('cultural_fit'),
            'additional_comments': request.form.get('additional_comments'),
            'is_draft': request.form.get('is_draft') == 'true',
            'is_private': request.form.get('is_private') == 'true'
        }
        
        # Handle skills assessment
        skills_data = []
        for i in range(int(request.form.get('skill_count', 0))):
            if request.form.get(f'skill_name_{i}'):
                skills_data.append({
                    'name': request.form.get(f'skill_name_{i}'),
                    'rating': int(request.form.get(f'skill_rating_{i}')),
                    'comments': request.form.get(f'skill_comments_{i}', '')
                })
        
        if skills_data:
            data['skills_assessment'] = skills_data
        
        if existing_feedback:
            # Update existing feedback
            for key, value in data.items():
                setattr(existing_feedback, key, value)
            existing_feedback.updated_at = datetime.utcnow()
            feedback = existing_feedback
        else:
            # Create new feedback
            feedback = InterviewFeedback(**data)
            db.session.add(feedback)
        
        db.session.commit()
        
        # Mark interview as completed if it wasn't already
        if not data['is_draft'] and interview.status != 'completed':
            interview.status = 'completed'
            interview.completed_at = datetime.utcnow()
            db.session.commit()
        
        flash('Feedback submitted successfully', 'success')
        return redirect(url_for('interviews.view_interview', interview_id=interview.id))
    
    return render_template('interviews/feedback.html', 
                          title='Interview Feedback', 
                          interview=interview,
                          feedback=existing_feedback)

@interviews.route('/upcoming')
@login_required
def upcoming_interviews():
    """View all upcoming interviews"""
    now = datetime.utcnow()
    
    if current_user.is_recruiter():
        # Fetch upcoming interviews for this recruiter
        interviews_list = Interview.query.filter(
            ((Interview.created_by_id == current_user.id) | 
            (Interview.interviewers.any(id=current_user.id))) &
            (Interview.scheduled_at > now) &
            (Interview.status.in_(['scheduled', 'rescheduled']))
        ).order_by(Interview.scheduled_at).all()
    else:
        # Fetch upcoming interviews for this applicant
        interviews_list = Interview.query.filter(
            (Interview.candidate_id == current_user.id) &
            (Interview.scheduled_at > now) &
            (Interview.status.in_(['scheduled', 'rescheduled']))
        ).order_by(Interview.scheduled_at).all()
    
    return render_template('interviews/list.html', 
                          title='Upcoming Interviews',
                          interviews=interviews_list,
                          list_type='upcoming')

@interviews.route('/past')
@login_required
def past_interviews():
    """View all past interviews"""
    now = datetime.utcnow()
    
    if current_user.is_recruiter():
        # Fetch past interviews for this recruiter
        interviews_list = Interview.query.filter(
            ((Interview.created_by_id == current_user.id) | 
            (Interview.interviewers.any(id=current_user.id))) &
            ((Interview.scheduled_at < now) |
            (Interview.status.in_(['completed', 'cancelled', 'no_show'])))
        ).order_by(Interview.scheduled_at.desc()).all()
    else:
        # Fetch past interviews for this applicant
        interviews_list = Interview.query.filter(
            (Interview.candidate_id == current_user.id) &
            ((Interview.scheduled_at < now) |
            (Interview.status.in_(['completed', 'cancelled', 'no_show'])))
        ).order_by(Interview.scheduled_at.desc()).all()
    
    return render_template('interviews/list.html', 
                          title='Past Interviews',
                          interviews=interviews_list,
                          list_type='past')

# API endpoints for calendar and scheduling

@interviews.route('/api/calendar-data')
@login_required
def calendar_data():
    """API endpoint for calendar view of interviews"""
    if current_user.is_recruiter():
        # Fetch interviews for this recruiter
        interviews_list = Interview.query.filter(
            (Interview.created_by_id == current_user.id) | 
            (Interview.interviewers.any(id=current_user.id))
        ).all()
    else:
        # Fetch interviews for this applicant
        interviews_list = Interview.query.filter_by(candidate_id=current_user.id).all()
    
    calendar_events = []
    for interview in interviews_list:
        event = {
            "id": interview.id,
            "title": f"{interview.stage.capitalize()} Interview - {interview.job.title}",
            "start": interview.scheduled_at.isoformat(),
            "end": interview.end_time.isoformat(),
            "url": url_for('interviews.view_interview', interview_id=interview.id),
            "className": f"event-{interview.status}"
        }
        calendar_events.append(event)
    
    return jsonify(calendar_events)

@interviews.route('/api/available-times/<int:job_id>/<date>')
@login_required
@recruiter_required
def available_times(job_id, date):
    """API endpoint to get available interview time slots for a given date"""
    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
    
    # Get all interviews on the selected date
    start_of_day = datetime.combine(selected_date, datetime.min.time())
    end_of_day = datetime.combine(selected_date, datetime.max.time())
    
    # Find all interviews for the job's recruiter on that day
    job = Job.query.get_or_404(job_id)
    
    existing_interviews = Interview.query.filter(
        (Interview.created_by_id == job.recruiter_id) &
        (Interview.scheduled_at >= start_of_day) &
        (Interview.scheduled_at <= end_of_day) &
        (Interview.status.in_(['scheduled', 'rescheduled']))
    ).all()
    
    # Find all busy slots
    busy_slots = []
    for interview in existing_interviews:
        start = interview.scheduled_at
        end = interview.end_time
        busy_slots.append({"start": start, "end": end})
    
    # Generate available time slots
    available_slots = []
    
    # Assume working hours are 9 AM to 5 PM
    work_start = datetime.combine(selected_date, datetime.strptime("09:00", "%H:%M").time())
    work_end = datetime.combine(selected_date, datetime.strptime("17:00", "%H:%M").time())
    
    # Create 30-minute slots
    current_slot_start = work_start
    while current_slot_start < work_end:
        current_slot_end = current_slot_start + timedelta(minutes=30)
        
        # Check if slot overlaps with any busy slots
        is_available = True
        for busy in busy_slots:
            if (current_slot_start < busy["end"] and current_slot_end > busy["start"]):
                is_available = False
                break
        
        if is_available:
            available_slots.append({
                "start": current_slot_start.strftime("%H:%M"),
                "end": current_slot_end.strftime("%H:%M")
            })
        
        current_slot_start = current_slot_end
    
    return jsonify(available_slots) 