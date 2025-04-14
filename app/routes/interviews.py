"""
Interview Routes for JobMatch

This module handles routes related to scheduling and managing interviews
between recruiters and job applicants.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.models import db, Interview, Application, User, Job
from datetime import datetime

interviews = Blueprint('interviews', __name__, url_prefix='/interviews')

@interviews.route('/')
@login_required
def list_interviews():
    """View all interviews for the current user"""
    if current_user.is_recruiter():
        # Recruiters see interviews for their jobs
        user_interviews = Interview.query.join(Application).join(Job).filter(
            Job.recruiter_id == current_user.id
        ).order_by(Interview.scheduled_time.desc()).all()
    else:
        # Applicants see their own interviews
        user_interviews = Interview.query.join(Application).filter(
            Application.applicant_id == current_user.id
        ).order_by(Interview.scheduled_time.desc()).all()
    
    return render_template(
        'interviews/list.html',
        title='My Interviews',
        interviews=user_interviews
    )

@interviews.route('/schedule/<int:application_id>', methods=['GET', 'POST'])
@login_required
def schedule_interview(application_id):
    """Schedule an interview for an application"""
    application = Application.query.get_or_404(application_id)
    job = Job.query.get(application.job_id)
    
    # Security check: only recruiters who own the job can schedule interviews
    if current_user.is_recruiter() and job.recruiter_id != current_user.id:
        flash('Access denied. You can only schedule interviews for your own job postings.', 'danger')
        return redirect(url_for('jobs.view_applications', job_id=job.id))
    
    if request.method == 'POST':
        interview_date = request.form.get('interview_date')
        interview_time = request.form.get('interview_time')
        interview_type = request.form.get('interview_type')
        location = request.form.get('location')
        notes = request.form.get('notes')
        
        # Combine date and time
        try:
            scheduled_datetime = datetime.strptime(f"{interview_date} {interview_time}", "%Y-%m-%d %H:%M")
            
            # Create new interview
            interview = Interview(
                application_id=application.id,
                scheduled_time=scheduled_datetime,
                interview_type=interview_type,
                location=location,
                notes=notes
            )
            
            # Update application status
            application.status = 'interview_scheduled'
            
            db.session.add(interview)
            db.session.commit()
            
            flash('Interview scheduled successfully!', 'success')
            return redirect(url_for('interviews.list_interviews'))
        except ValueError:
            flash('Invalid date or time format', 'danger')
    
    return render_template(
        'interviews/schedule.html',
        title='Schedule Interview',
        application=application,
        job=job,
        now=datetime.now()
    )

@interviews.route('/<int:interview_id>')
@login_required
def view_interview(interview_id):
    """View details of a specific interview"""
    interview = Interview.query.get_or_404(interview_id)
    application = Application.query.get(interview.application_id)
    job = Job.query.get(application.job_id)
    
    # Security check: only relevant parties can view the interview
    if current_user.is_recruiter():
        if job.recruiter_id != current_user.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('interviews.list_interviews'))
    else:
        if application.applicant_id != current_user.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('interviews.list_interviews'))
    
    return render_template(
        'interviews/view.html',
        title='Interview Details',
        interview=interview,
        application=application,
        job=job
    )

@interviews.route('/update/<int:interview_id>', methods=['POST'])
@login_required
def update_interview_status(interview_id):
    """Update the status of an interview"""
    interview = Interview.query.get_or_404(interview_id)
    application = Application.query.get(interview.application_id)
    job = Job.query.get(application.job_id)
    
    # Security check: only recruiters who own the job can update interview status
    if not current_user.is_recruiter() or job.recruiter_id != current_user.id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    status = request.form.get('status')
    feedback = request.form.get('feedback')
    
    if status in ['completed', 'cancelled', 'rescheduled']:
        interview.status = status
        interview.feedback = feedback
        
        # Update application status based on interview outcome
        if status == 'completed':
            result = request.form.get('result')
            if result in ['passed', 'failed']:
                interview.result = result
                if result == 'passed':
                    application.status = 'offer_pending'
                else:
                    application.status = 'rejected'
        
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Invalid status'}), 400

@interviews.route('/reschedule/<int:interview_id>', methods=['GET', 'POST'])
@login_required
def reschedule_interview(interview_id):
    """Reschedule an existing interview"""
    interview = Interview.query.get_or_404(interview_id)
    application = Application.query.get(interview.application_id)
    job = Job.query.get(application.job_id)
    
    # Security check
    if current_user.is_recruiter():
        if job.recruiter_id != current_user.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('interviews.list_interviews'))
    else:
        if application.applicant_id != current_user.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('interviews.list_interviews'))
    
    if request.method == 'POST':
        interview_date = request.form.get('interview_date')
        interview_time = request.form.get('interview_time')
        
        # Combine date and time
        try:
            scheduled_datetime = datetime.strptime(f"{interview_date} {interview_time}", "%Y-%m-%d %H:%M")
            
            # Update interview
            interview.scheduled_time = scheduled_datetime
            interview.status = 'scheduled'  # Reset status
            
            db.session.commit()
            
            flash('Interview rescheduled successfully!', 'success')
            return redirect(url_for('interviews.view_interview', interview_id=interview.id))
        except ValueError:
            flash('Invalid date or time format', 'danger')
    
    return render_template(
        'interviews/reschedule.html',
        title='Reschedule Interview',
        interview=interview,
        application=application,
        job=job,
        now=datetime.now()
    ) 