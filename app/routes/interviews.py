"""
Interview Management Routes for JobMatch

This module handles routes related to scheduling, managing, and conducting job interviews.
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.models.models import Job, Application, User, Interview, db
from datetime import datetime, timedelta
import io
import pytz

interviews = Blueprint('interviews', __name__, url_prefix='/interviews')

@interviews.route('/')
@login_required
def index():
    """Main interviews dashboard view"""
    try:
        if current_user.user_type == 'recruiter':
            # Fetch upcoming interviews for the recruiter
            upcoming_interviews = Interview.query.join(Job).filter(
                Job.recruiter_id == current_user.id,
                Interview.scheduled_at > datetime.utcnow(),
                Interview.status == 'scheduled'
            ).order_by(Interview.scheduled_at).all()
            
            # Fetch past interviews for the recruiter
            past_interviews = Interview.query.join(Job).filter(
                Job.recruiter_id == current_user.id,
                Interview.scheduled_at < datetime.utcnow()
            ).order_by(Interview.scheduled_at.desc()).all()
            
            # Fetch all interviews for the recruiter (for the All tab)
            all_interviews = Interview.query.join(Job).filter(
                Job.recruiter_id == current_user.id
            ).order_by(Interview.scheduled_at.desc()).all()
            
            return render_template('interviews/recruiter_dashboard.html', 
                                  title='Manage Interviews',
                                  upcoming_interviews=upcoming_interviews,
                                  past_interviews=past_interviews,
                                  all_interviews=all_interviews)
        else:
            # Fetch interviews for this applicant
            upcoming_interviews = Interview.query.filter(
                Interview.candidate_id == current_user.id,
                Interview.scheduled_at > datetime.utcnow(),
                Interview.status == 'scheduled'
            ).order_by(Interview.scheduled_at).all()
            
            past_interviews = Interview.query.filter(
                Interview.candidate_id == current_user.id,
                Interview.scheduled_at < datetime.utcnow()
            ).order_by(Interview.scheduled_at.desc()).all()
            
            return render_template('interviews/applicant_dashboard.html', 
                                  title='My Interviews',
                                  upcoming_interviews=upcoming_interviews,
                                  past_interviews=past_interviews)
    except Exception as e:
        flash(f'Error loading interviews: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@interviews.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule_interview():
    """Schedule a new interview"""
    if current_user.user_type != 'recruiter':
        flash('Only recruiters can schedule interviews', 'danger')
        return redirect(url_for('main.index'))
    
    # Get recruiter's job listings with applications
    jobs = Job.query.filter_by(recruiter_id=current_user.id).all()
    
    if request.method == 'POST':
        try:
            # Process the form data
            job_id = request.form.get('job_id')
            candidate_id = request.form.get('candidate_id')
            application_id = request.form.get('application_id')
            interview_type = request.form.get('interview_type')
            date_str = request.form.get('interview_date')
            time_str = request.form.get('interview_time')
            duration = request.form.get('duration', 60)
            
            # Validate required fields
            if not all([job_id, candidate_id, application_id, interview_type, date_str, time_str]):
                flash('All fields are required', 'danger')
                return redirect(url_for('interviews.schedule_interview'))
            
            # Parse date and time
            interview_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            
            # Create new interview
            new_interview = Interview(
                job_id=job_id,
                candidate_id=candidate_id,
                application_id=application_id,
                stage='first_round',  # Default stage
                interview_type=interview_type,
                scheduled_at=interview_datetime,
                duration=duration,
                status='scheduled',
                created_by_id=current_user.id
            )
            
            # Add type-specific details if provided
            if interview_type == 'video':
                new_interview.video_platform = request.form.get('video_platform')
                new_interview.video_link = request.form.get('video_link')
            elif interview_type == 'phone':
                new_interview.phone_number = request.form.get('phone_number')
                new_interview.who_calls = request.form.get('who_calls')
            elif interview_type == 'in_person':
                new_interview.location = request.form.get('location')
            
            db.session.add(new_interview)
            db.session.commit()
            
            flash('Interview scheduled successfully', 'success')
            return redirect(url_for('interviews.view_interview', interview_id=new_interview.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error scheduling interview: {str(e)}', 'danger')
    
    # GET request - display the form
    applications = Application.query.join(Job).filter(Job.recruiter_id == current_user.id).all()
    return render_template('interviews/schedule.html', 
                          title='Schedule Interview',
                          jobs=jobs,
                          applications=applications)

@interviews.route('/<int:interview_id>')
@login_required
def view_interview(interview_id):
    """View details of a specific interview"""
    try:
        interview = Interview.query.get_or_404(interview_id)
        
        # Check if user is authorized to view this interview
        if current_user.user_type == 'recruiter':
            if interview.job.recruiter_id != current_user.id:
                flash('You are not authorized to view this interview', 'danger')
                return redirect(url_for('interviews.index'))
        else:  # applicant
            if interview.candidate_id != current_user.id:
                flash('You are not authorized to view this interview', 'danger')
                return redirect(url_for('interviews.index'))
        
        return render_template('interviews/view.html', 
                              title='Interview Details',
                              interview=interview)
    except Exception as e:
        flash(f'Error loading interview: {str(e)}', 'danger')
        return redirect(url_for('interviews.index'))

@interviews.route('/<int:interview_id>/reschedule', methods=['GET', 'POST'])
@login_required
def reschedule_interview(interview_id):
    """Reschedule an existing interview"""
    try:
        interview = Interview.query.get_or_404(interview_id)
        
        # Check authorization
        if current_user.user_type == 'recruiter' and interview.job.recruiter_id != current_user.id:
            flash('You are not authorized to reschedule this interview', 'danger')
            return redirect(url_for('interviews.index'))
        
        if interview.status not in ['scheduled', 'confirmed']:
            flash('Only scheduled interviews can be rescheduled', 'warning')
            return redirect(url_for('interviews.view_interview', interview_id=interview_id))
        
        if request.method == 'POST':
            date_str = request.form.get('interview_date')
            time_str = request.form.get('interview_time')
            duration = request.form.get('duration')
            reschedule_reason = request.form.get('reschedule_reason')
            
            if not all([date_str, time_str, duration, reschedule_reason]):
                flash('All fields are required', 'danger')
                return redirect(url_for('interviews.reschedule_interview', interview_id=interview_id))
            
            # Parse date and time
            new_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            
            # Update interview
            interview.scheduled_at = new_datetime
            interview.duration = duration
            interview.notes = f"{interview.notes or ''}\n\nRescheduled on {datetime.now().strftime('%Y-%m-%d %H:%M')}. Reason: {reschedule_reason}"
            interview.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Interview rescheduled successfully', 'success')
            return redirect(url_for('interviews.view_interview', interview_id=interview_id))
        
        return render_template('interviews/reschedule.html', 
                              title='Reschedule Interview',
                              interview=interview)
    except Exception as e:
        flash(f'Error rescheduling interview: {str(e)}', 'danger')
        return redirect(url_for('interviews.index'))

@interviews.route('/<int:interview_id>/cancel', methods=['POST'])
@login_required
def cancel_interview(interview_id):
    """Cancel an existing interview"""
    try:
        interview = Interview.query.get_or_404(interview_id)
    
        # Check authorization
        if current_user.user_type == 'recruiter' and interview.job.recruiter_id != current_user.id:
            flash('You are not authorized to cancel this interview', 'danger')
            return redirect(url_for('interviews.index'))
        
        if interview.status not in ['scheduled', 'confirmed']:
            flash('Only scheduled interviews can be cancelled', 'warning')
            return redirect(url_for('interviews.view_interview', interview_id=interview_id))
        
        # Update interview
        cancellation_reason = request.form.get('cancellation_reason', 'No reason provided')
        interview.status = 'cancelled'
        interview.cancelled_at = datetime.utcnow()
        interview.cancelled_by_id = current_user.id
        interview.cancellation_reason = cancellation_reason
        
        db.session.commit()
        flash('Interview cancelled successfully', 'success')
        return redirect(url_for('interviews.index'))
    except Exception as e:
        flash(f'Error cancelling interview: {str(e)}', 'danger')
        return redirect(url_for('interviews.view_interview', interview_id=interview_id))

@interviews.route('/<int:interview_id>/feedback', methods=['GET', 'POST'])
@login_required
def interview_feedback(interview_id):
    """Submit feedback for an interview (for recruiters)"""
    if current_user.user_type != 'recruiter':
        flash('Only recruiters can submit interview feedback', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        interview = Interview.query.get_or_404(interview_id)
        
        # Check authorization
        if interview.job.recruiter_id != current_user.id:
            flash('You are not authorized to provide feedback for this interview', 'danger')
            return redirect(url_for('interviews.index'))
        
        if interview.status != 'completed':
            flash('Feedback can only be provided for completed interviews', 'warning')
            return redirect(url_for('interviews.view_interview', interview_id=interview_id))
        
        if request.method == 'POST':
            # Process feedback form
            rating = request.form.get('overall_rating')
            recommendation = request.form.get('recommendation')
            strengths = request.form.get('strengths')
            areas_for_improvement = request.form.get('areas_for_improvement')
            cultural_fit = request.form.get('cultural_fit', '')
            additional_comments = request.form.get('additional_comments', '')
            
            if not all([rating, recommendation, strengths, areas_for_improvement]):
                flash('Please fill out all required fields', 'danger')
                return redirect(url_for('interviews.interview_feedback', interview_id=interview_id))
            
            # Check if feedback already exists
            if hasattr(interview, 'feedback') and interview.feedback:
                # Update existing feedback
                interview.feedback.overall_rating = rating
                interview.feedback.recommendation = recommendation
                interview.feedback.strengths = strengths
                interview.feedback.areas_for_improvement = areas_for_improvement
                interview.feedback.cultural_fit = cultural_fit
                interview.feedback.additional_comments = additional_comments
                interview.feedback.updated_at = datetime.utcnow()
            else:
                # Create new feedback object
                from app.models.interview import InterviewFeedback
                feedback = InterviewFeedback(
                    interview_id=interview_id,
                    submitted_by_id=current_user.id,
                    overall_rating=rating,
                    recommendation=recommendation,
                    strengths=strengths,
                    areas_for_improvement=areas_for_improvement,
                    cultural_fit=cultural_fit,
                    additional_comments=additional_comments
                )
                db.session.add(feedback)
            
            db.session.commit()
            flash('Feedback submitted successfully', 'success')
            return redirect(url_for('interviews.view_interview', interview_id=interview_id))
        
        return render_template('interviews/feedback.html', 
                              title='Interview Feedback',
                              interview=interview)
    except Exception as e:
        flash(f'Error processing feedback: {str(e)}', 'danger')
        return redirect(url_for('interviews.index'))

# API endpoints for calendar and scheduling

@interviews.route('/api/calendar-data')
@login_required
def calendar_data():
    """API endpoint for calendar view of interviews"""
    try:
        # Determine which interviews to fetch based on user type
        if current_user.user_type == 'recruiter':
            interviews_query = Interview.query.join(Job).filter(Job.recruiter_id == current_user.id)
        else:  # applicant
            interviews_query = Interview.query.filter(Interview.candidate_id == current_user.id)
        
        interviews_list = interviews_query.all()
        
        calendar_events = []
        for interview in interviews_list:
            # Create a calendar event for each interview
            event = {
                "id": interview.id,
                "title": f"Interview: {interview.job.title}" if current_user.user_type == 'recruiter' else f"Interview with {interview.job.company}",
                "start": interview.scheduled_at.strftime('%Y-%m-%dT%H:%M:%S'),
                "end": (interview.scheduled_at + timedelta(minutes=interview.duration)).strftime('%Y-%m-%dT%H:%M:%S'),
                "url": url_for('interviews.view_interview', interview_id=interview.id),
                "className": f"event-{interview.status}",  # CSS class based on status
                "description": f"Type: {interview.interview_type}"
            }
            calendar_events.append(event)
        
        return jsonify(calendar_events)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@interviews.route('/api/available-times/<int:job_id>/<date>')
@login_required
def available_times(job_id, date):
    """API endpoint to get available interview time slots for a given date"""
    try:
        # Parse the date string
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # In a real implementation, this would check existing interviews and calendar
        # For now, return standard business hours with some slots marked as busy
        
        # Standard business hours slots (9 AM to 5 PM, 30-minute intervals)
        all_slots = []
        start_time = datetime.combine(selected_date, datetime.min.time().replace(hour=9))
        end_time = datetime.combine(selected_date, datetime.min.time().replace(hour=17))
        
        current_slot = start_time
        while current_slot < end_time:
            slot_end = current_slot + timedelta(minutes=30)
            all_slots.append({
                "start": current_slot.strftime('%H:%M'),
                "end": slot_end.strftime('%H:%M'),
                "available": True  # Default to available
            })
            current_slot = slot_end
        
        # Find existing interviews on this date to mark slots as busy
        busy_slots = []
        job = Job.query.get_or_404(job_id)
        if job.recruiter_id == current_user.id:
            # Get recruiter's interviews for this date
            day_start = datetime.combine(selected_date, datetime.min.time())
            day_end = datetime.combine(selected_date, datetime.max.time())
            
            recruiter_interviews = Interview.query.join(Job).filter(
                Job.recruiter_id == current_user.id,
                Interview.scheduled_at >= day_start,
                Interview.scheduled_at <= day_end
            ).all()
            
            # Mark slots that overlap with existing interviews as busy
            for interview in recruiter_interviews:
                interview_start = interview.scheduled_at
                interview_end = interview_start + timedelta(minutes=interview.duration)
                
                for slot in all_slots:
                    slot_start = datetime.strptime(f"{date} {slot['start']}", '%Y-%m-%d %H:%M')
                    slot_end = datetime.strptime(f"{date} {slot['end']}", '%Y-%m-%d %H:%M')
                    
                    # Check if slot overlaps with interview
                    if (slot_start < interview_end and slot_end > interview_start):
                        slot['available'] = False
        
        # Return only available slots
        available_slots = [slot for slot in all_slots if slot['available']]
        return jsonify(available_slots)
    except Exception as e:
        return jsonify({"error": str(e)}), 500