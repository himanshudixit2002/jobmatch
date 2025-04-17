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
        now = datetime.utcnow()
        if current_user.user_type == 'recruiter':
            # Fetch upcoming interviews for the recruiter
            upcoming_interviews = Interview.query.join(Job).filter(
                Job.recruiter_id == current_user.id,
                Interview.scheduled_at > now,
                Interview.status == 'scheduled'
            ).order_by(Interview.scheduled_at).all()
            
            # Fetch past interviews for the recruiter
            past_interviews = Interview.query.join(Job).filter(
                Job.recruiter_id == current_user.id,
                Interview.scheduled_at < now
            ).order_by(Interview.scheduled_at.desc()).all()
            
            # Fetch all interviews for the recruiter (for the All tab)
            all_interviews = Interview.query.join(Job).filter(
                Job.recruiter_id == current_user.id
            ).order_by(Interview.scheduled_at.desc()).all()
            
            return render_template('interviews/recruiter_dashboard.html', 
                                  title='Manage Interviews',
                                  upcoming_interviews=upcoming_interviews,
                                  past_interviews=past_interviews,
                                  all_interviews=all_interviews,
                                  now=now)
        else:
            # Fetch interviews for this applicant
            upcoming_interviews = Interview.query.filter(
                Interview.applicant_id == current_user.id,
                Interview.scheduled_at > now,
                Interview.status == 'scheduled'
            ).order_by(Interview.scheduled_at).all()
            
            past_interviews = Interview.query.filter(
                Interview.applicant_id == current_user.id,
                Interview.scheduled_at < now
            ).order_by(Interview.scheduled_at.desc()).all()
            
            return render_template('interviews/applicant_dashboard.html', 
                                  title='My Interviews',
                                  upcoming_interviews=upcoming_interviews,
                                  past_interviews=past_interviews,
                                  now=now)
    except Exception as e:
        flash(f'Error loading interviews: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@interviews.route('/manage')
@login_required
def manage():
    """Advanced interview management view for recruiters"""
    if current_user.user_type != 'recruiter':
        flash('Only recruiters can access this page', 'danger')
        return redirect(url_for('interviews.index'))
    
    try:
        now = datetime.utcnow()
        # Get all jobs managed by this recruiter
        jobs = Job.query.filter_by(recruiter_id=current_user.id).all()
        job_ids = [job.id for job in jobs]
        
        # Get all interviews for these jobs
        all_interviews = Interview.query.filter(Interview.job_id.in_(job_ids)).order_by(Interview.scheduled_at.desc()).all()
        
        # Organize interviews by status
        scheduled = [i for i in all_interviews if i.status == 'scheduled' and i.scheduled_at > now]
        completed = [i for i in all_interviews if i.status == 'completed']
        cancelled = [i for i in all_interviews if i.status == 'cancelled']
        past_due = [i for i in all_interviews if i.status == 'scheduled' and i.scheduled_at < now]
        needs_feedback = [i for i in all_interviews if i.status == 'completed' and not hasattr(i, 'feedback')]
        
        return render_template('interviews/manage.html', 
                            title='Interview Management',
                            all_interviews=all_interviews,
                            scheduled=scheduled,
                            completed=completed,
                            cancelled=cancelled, 
                            past_due=past_due,
                            needs_feedback=needs_feedback,
                            jobs=jobs,
                            now=now)
    except Exception as e:
        flash(f'Error loading interview management: {str(e)}', 'danger')
        return redirect(url_for('interviews.index'))

@interviews.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule_interview():
    """Schedule a new interview"""
    if current_user.user_type != 'recruiter':
        flash('Only recruiters can schedule interviews', 'danger')
        return redirect(url_for('main.index'))
    
    # Get recruiter's job listings with applications
    jobs = Job.query.filter_by(recruiter_id=current_user.id).all()
    
    # Default values
    edit_mode = False
    today = datetime.utcnow().strftime('%Y-%m-%d')
    notify_candidate = True
    notify_interviewers = True
    add_to_calendar = True
    candidate_availability = []
    available_interviewers = []
    
    # Get job and application details from query parameters
    job_id = request.args.get('job_id')
    application_id = request.args.get('application_id')
    
    job = None
    application = None
    candidate = None
    
    if job_id and application_id:
        job = Job.query.get(job_id)
        application = Application.query.get(application_id)
        if application:
            candidate = User.query.get(application.applicant_id)
            # Get available interviewers (for now, just use all users who are recruiters)
            available_interviewers = User.query.filter_by(user_type='recruiter').all()
    
    if request.method == 'POST':
        try:
            # Process the form data
            job_id = request.form.get('job_id')
            applicant_id = request.form.get('applicant_id')
            application_id = request.form.get('application_id')
            interview_type = request.form.get('interview_type')
            date_str = request.form.get('scheduled_date')
            time_str = request.form.get('scheduled_time')
            duration = int(request.form.get('duration', 60))
            interview_stage = request.form.get('interview_stage')
            custom_stage = request.form.get('custom_stage')
            
            # Validate required fields
            if not all([job_id, applicant_id, application_id, interview_type, date_str, time_str, interview_stage]):
                flash('All fields are required', 'danger')
                return redirect(url_for('interviews.schedule_interview'))
            
            # Parse date and time
            scheduled_at = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            
            # Create new interview
            new_interview = Interview(
                job_id=job_id,
                recruiter_id=current_user.id,
                applicant_id=applicant_id,
                application_id=application_id,
                scheduled_at=scheduled_at,
                duration=duration,
                interview_type=interview_type,
                stage=interview_stage,
                status='scheduled'
            )
            
            # Add custom stage if provided
            if interview_stage == 'custom' and custom_stage:
                new_interview.custom_stage = custom_stage
            
            # Add type-specific details if provided
            if interview_type == 'video':
                new_interview.video_link = request.form.get('video_link')
            elif interview_type == 'in_person':
                new_interview.location = request.form.get('location')
            
            # Add notes if provided
            if request.form.get('notes'):
                new_interview.notes = request.form.get('notes')
            
            db.session.add(new_interview)
            db.session.commit()
            
            flash('Interview scheduled successfully', 'success')
            return redirect(url_for('interviews.view_interview', interview_id=new_interview.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error scheduling interview: {str(e)}', 'danger')
    
    # GET request - display the form
    applications = Application.query.join(Job).filter(Job.recruiter_id == current_user.id).all()
    now = datetime.utcnow()
    
    # Get application_id from request if not set
    if application_id is None:
        application_id = request.args.get('application_id')
    
    return render_template('interviews/schedule.html', 
                          title='Schedule Interview',
                          jobs=jobs,
                          applications=applications,
                          job=job,
                          application=application,
                          application_id=application_id,
                          candidate=candidate,
                          edit_mode=edit_mode,
                          available_interviewers=available_interviewers,
                          candidate_availability=candidate_availability,
                          notify_candidate=notify_candidate,
                          notify_interviewers=notify_interviewers,
                          add_to_calendar=add_to_calendar,
                          today=today,
                          now=now)

@interviews.route('/<int:interview_id>')
@login_required
def view_interview(interview_id):
    """View details of a specific interview"""
    try:
        interview = Interview.query.get_or_404(interview_id)
        now = datetime.utcnow()
        
        # Check if user is authorized to view this interview
        if current_user.user_type == 'recruiter':
            if interview.job and interview.job.recruiter_id != current_user.id:
                flash('You are not authorized to view this interview', 'danger')
                return redirect(url_for('interviews.index'))
        else:  # applicant
            if interview.applicant_id != current_user.id:
                flash('You are not authorized to view this interview', 'danger')
                return redirect(url_for('interviews.index'))
        
        # Create dummy application stages for the UI
        application_stages = [
            {"name": "Application Submitted", "completed": True, "date": "Aug 15, 2023"},
            {"name": "Resume Screened", "completed": True, "date": "Aug 18, 2023"},
            {"name": "Interview Scheduled", "completed": True, "date": "Aug 20, 2023"},
            {"name": "Interview Completed", "completed": interview.status in ['completed', 'cancelled'], "current": interview.status not in ['completed', 'cancelled'], "date": interview.scheduled_at.strftime('%b %d, %Y') if interview.status in ['completed', 'cancelled'] else None},
            {"name": "Decision", "completed": False, "current": interview.status == 'completed'}
        ]
        
        # Create dummy documents for UI
        documents = [
            {"id": 1, "name": "Resume", "type": "resume", "uploaded_at": datetime.now() - timedelta(days=15)},
            {"id": 2, "name": "Cover Letter", "type": "cover_letter", "uploaded_at": datetime.now() - timedelta(days=15)},
            {"id": 3, "name": "Portfolio", "type": "portfolio", "uploaded_at": datetime.now() - timedelta(days=10)}
        ]
        
        return render_template('interviews/view.html', 
                              title='Interview Details',
                              interview=interview,
                              application_stages=application_stages,
                              documents=documents,
                              is_interviewer=False,
                              can_edit_feedback=current_user.user_type == 'recruiter',
                              now=now)
    except Exception as e:
        flash(f'Error loading interview: {str(e)}', 'danger')
        return redirect(url_for('interviews.index'))

@interviews.route('/<int:interview_id>/reschedule', methods=['GET', 'POST'])
@login_required
def reschedule_interview(interview_id):
    """Reschedule an existing interview"""
    try:
        interview = Interview.query.get_or_404(interview_id)
        now = datetime.utcnow()
        
        # Check authorization
        if current_user.user_type == 'recruiter' and interview.job.recruiter_id != current_user.id:
            flash('You are not authorized to reschedule this interview', 'danger')
            return redirect(url_for('interviews.index'))
        
        if interview.status not in ['scheduled', 'confirmed']:
            flash('Only scheduled interviews can be rescheduled', 'warning')
            return redirect(url_for('interviews.view_interview', interview_id=interview_id))
        
        if request.method == 'POST':
            date_str = request.form.get('scheduled_date')
            time_str = request.form.get('scheduled_time')
            duration = int(request.form.get('duration'))
            reschedule_reason = request.form.get('reschedule_reason')
            
            if not all([date_str, time_str, duration, reschedule_reason]):
                flash('All fields are required', 'danger')
                return redirect(url_for('interviews.reschedule_interview', interview_id=interview_id))
            
            # Parse date and time
            new_scheduled_at = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            
            # Update interview
            interview.scheduled_at = new_scheduled_at
            interview.duration = duration
            interview.notes = f"{interview.notes or ''}\n\nRescheduled on {datetime.now().strftime('%Y-%m-%d %H:%M')}. Reason: {reschedule_reason}"
            interview.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Interview rescheduled successfully', 'success')
            return redirect(url_for('interviews.view_interview', interview_id=interview_id))
        
        return render_template('interviews/reschedule.html', 
                              title='Reschedule Interview',
                              interview=interview,
                              now=now)
    except Exception as e:
        flash(f'Error rescheduling interview: {str(e)}', 'danger')
        return redirect(url_for('interviews.index'))

@interviews.route('/<int:interview_id>/cancel', methods=['POST'])
@login_required
def cancel_interview(interview_id):
    """Cancel an existing interview"""
    try:
        interview = Interview.query.get_or_404(interview_id)
        now = datetime.utcnow()
    
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
        interview.updated_at = datetime.utcnow()
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
    """Submit or view feedback for an interview"""
    try:
        interview = Interview.query.get_or_404(interview_id)
        now = datetime.utcnow()
        
        # Check authorization
        if current_user.user_type == 'recruiter':
            if interview.job.recruiter_id != current_user.id:
                flash('You are not authorized to access this feedback', 'danger')
                return redirect(url_for('interviews.index'))
                
            # Handle feedback logic for recruiters
            return render_template('interviews/feedback_form.html', 
                                title='Interview Feedback',
                                interview=interview,
                                now=now)
        else:  # applicant
            if interview.applicant_id != current_user.id:
                flash('You are not authorized to access this feedback', 'danger')
                return redirect(url_for('interviews.index'))
            
            # Applicants can only view feedback, not submit it
            if hasattr(interview, 'feedback') and interview.feedback:
                return render_template('interviews/feedback.html', 
                                    title='Interview Feedback',
                                    interview=interview,
                                    feedback=interview.feedback,
                                    view_only=True,
                                    now=now)
            else:
                flash('Feedback for this interview is not available yet', 'info')
                return redirect(url_for('interviews.view_interview', interview_id=interview_id))
    except Exception as e:
        flash(f'Error with interview feedback: {str(e)}', 'danger')
        return redirect(url_for('interviews.index'))

# API endpoints for calendar and scheduling

@interviews.route('/api/calendar-data')
@login_required
def calendar_data():
    """API endpoint for calendar view of interviews"""
    try:
        now = datetime.utcnow()
        # Determine which interviews to fetch based on user type
        if current_user.user_type == 'recruiter':
            interviews_query = Interview.query.join(Job).filter(Job.recruiter_id == current_user.id)
        else:  # applicant
            interviews_query = Interview.query.filter(Interview.applicant_id == current_user.id)
        
        interviews_list = interviews_query.all()
        
        calendar_events = []
        for interview in interviews_list:
            # Create a calendar event for each interview
            job_title = interview.job.title if hasattr(interview, 'job') and interview.job and hasattr(interview.job, 'title') else 'Untitled Job'
            job_company = interview.job.company if hasattr(interview, 'job') and interview.job and hasattr(interview.job, 'company') else ''
            
            event = {
                "id": interview.id,
                "title": f"Interview: {job_title}" if current_user.user_type == 'recruiter' else f"Interview with {job_company}",
                "start": interview.scheduled_at.strftime('%Y-%m-%dT%H:%M:%S'),
                "end": interview.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
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
        now = datetime.utcnow()
        
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
                interview_end = interview.end_time
                
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