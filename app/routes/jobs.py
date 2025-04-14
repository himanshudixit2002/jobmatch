from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.models import db, Job, User, Skill, Application
from app.forms.job_forms import JobForm, ApplicationForm
from datetime import datetime
from flask import current_app

jobs = Blueprint('jobs', __name__)

@jobs.route('/jobs')
def browse_jobs():
    """View all available jobs for applicants"""
    # Get search parameters
    search_query = request.args.get('q', '').strip()
    skill_filter = request.args.get('skill', '').strip()
    location_filter = request.args.get('location', '').strip()
    
    # Base query - active jobs
    job_query = Job.query.filter_by(is_active=True)
    
    # Apply filters
    if search_query:
        job_query = job_query.filter(
            Job.title.ilike(f'%{search_query}%') | 
            Job.description.ilike(f'%{search_query}%') |
            Job.recruiter.has(User.company.ilike(f'%{search_query}%'))
        )
    
    if location_filter:
        job_query = job_query.filter(Job.location.ilike(f'%{location_filter}%'))
    
    if skill_filter:
        skill = Skill.query.filter(Skill.name.ilike(f'%{skill_filter}%')).first()
        if skill:
            job_query = job_query.filter(Job.skills.contains(skill))
    
    # Order by most recent
    active_jobs = job_query.order_by(Job.created_at.desc()).all()
    
    # For applicants, calculate match scores
    if current_user.is_authenticated and current_user.is_applicant():
        # Calculate match scores for each job
        for job in active_jobs:
            job.user_match = job.match_score(current_user)
        
        # Sort jobs by match score (descending)
        active_jobs.sort(key=lambda x: x.user_match, reverse=True)
    
    # Get all skills for filter dropdown
    all_skills = Skill.query.order_by(Skill.name).all()
    
    # Get unique locations for filter dropdown
    locations = db.session.query(Job.location).distinct().order_by(Job.location).all()
    locations = [location[0] for location in locations]
    
    return render_template(
        'jobs/browse.html', 
        title='Browse Jobs', 
        jobs=active_jobs,
        all_skills=all_skills,
        locations=locations,
        search_query=search_query,
        skill_filter=skill_filter,
        location_filter=location_filter
    )

@jobs.route('/jobs/manage')
@login_required
def manage_jobs():
    """View for recruiters to manage their posted jobs"""
    if not current_user.is_recruiter():
        flash('Access denied. Recruiters only.', 'danger')
        return redirect(url_for('main.index'))
    
    recruiter_jobs = Job.query.filter_by(recruiter_id=current_user.id).order_by(Job.created_at.desc()).all()
    return render_template('jobs/manage.html', title='Manage Jobs', jobs=recruiter_jobs)

@jobs.route('/jobs/create', methods=['GET', 'POST'])
@login_required
def create_job():
    """Create a new job posting"""
    if not current_user.is_recruiter():
        flash('Access denied. Recruiters only.', 'danger')
        return redirect(url_for('main.index'))
    
    form = JobForm()
    all_skills = Skill.query.all()
    form.skills.choices = [(skill.id, skill.name) for skill in all_skills]
    
    if form.validate_on_submit():
        job = Job(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            salary=form.salary.data,
            experience_required=form.experience_required.data,
            recruiter_id=current_user.id
        )
        
        # Add selected skills
        for skill_id in form.skills.data:
            skill = Skill.query.get(skill_id)
            if skill:
                job.skills.append(skill)
        
        db.session.add(job)
        db.session.commit()
        
        flash('Job posting created successfully!', 'success')
        return redirect(url_for('jobs.manage_jobs'))
    
    return render_template('jobs/create.html', title='Create Job', form=form)

@jobs.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    """Edit an existing job posting"""
    if not current_user.is_recruiter():
        flash('Access denied. Recruiters only.', 'danger')
        return redirect(url_for('main.index'))
    
    job = Job.query.get_or_404(job_id)
    
    # Ensure recruiter owns this job
    if job.recruiter_id != current_user.id:
        flash('Access denied. You can only edit your own job postings.', 'danger')
        return redirect(url_for('jobs.manage_jobs'))
    
    form = JobForm(obj=job)
    all_skills = Skill.query.all()
    form.skills.choices = [(skill.id, skill.name) for skill in all_skills]
    
    # Pre-select current job skills
    if request.method == 'GET':
        form.skills.data = [skill.id for skill in job.skills]
    
    if form.validate_on_submit():
        job.title = form.title.data
        job.description = form.description.data
        job.location = form.location.data
        job.salary = form.salary.data
        job.experience_required = form.experience_required.data
        
        # Update skills - first remove all current skills
        job.skills = []
        
        # Then add selected skills
        for skill_id in form.skills.data:
            skill = Skill.query.get(skill_id)
            if skill:
                job.skills.append(skill)
        
        db.session.commit()
        
        flash('Job posting updated successfully!', 'success')
        return redirect(url_for('jobs.view_job', job_id=job.id))
    
    return render_template('jobs/edit.html', title='Edit Job', form=form, job=job)

@jobs.route('/jobs/<int:job_id>')
def view_job(job_id):
    """View a specific job posting"""
    job = Job.query.get_or_404(job_id)
    
    # Check if the current user has already applied
    has_applied = False
    if current_user.is_authenticated and current_user.is_applicant():
        application = Application.query.filter_by(
            job_id=job.id, 
            applicant_id=current_user.id
        ).first()
        has_applied = application is not None
        
        # Calculate match score
        match_score = job.match_score(current_user)
    else:
        match_score = None
    
    form = ApplicationForm() if current_user.is_authenticated and current_user.is_applicant() else None
    
    return render_template(
        'jobs/view.html', 
        title=job.title, 
        job=job, 
        has_applied=has_applied,
        match_score=match_score,
        form=form
    )

@jobs.route('/jobs/<int:job_id>/apply', methods=['POST'])
@login_required
def apply_for_job(job_id):
    """Apply for a job"""
    if not current_user.is_applicant():
        flash('Only applicants can apply for jobs.', 'danger')
        return redirect(url_for('jobs.view_job', job_id=job_id))
    
    job = Job.query.get_or_404(job_id)
    
    # Check if already applied
    existing_application = Application.query.filter_by(
        job_id=job.id,
        applicant_id=current_user.id
    ).first()
    
    if existing_application:
        flash('You have already applied for this job.', 'warning')
        return redirect(url_for('jobs.view_job', job_id=job_id))
    
    form = ApplicationForm()
    if form.validate_on_submit():
        # Calculate match score
        match_score = job.match_score(current_user)
        
        application = Application(
            job_id=job.id,
            applicant_id=current_user.id,
            cover_letter=form.cover_letter.data,
            match_score=match_score
        )
        
        db.session.add(application)
        db.session.commit()
        
        flash('Application submitted successfully!', 'success')
    
    return redirect(url_for('jobs.view_job', job_id=job_id))

@jobs.route('/jobs/<int:job_id>/applications')
@login_required
def view_applications(job_id):
    """View all applications for a specific job (recruiters only)"""
    if not current_user.is_recruiter():
        flash('Access denied. Recruiters only.', 'danger')
        return redirect(url_for('main.index'))
    
    job = Job.query.get_or_404(job_id)
    
    # Ensure recruiter owns this job
    if job.recruiter_id != current_user.id:
        flash('Access denied. You can only view applications for your own job postings.', 'danger')
        return redirect(url_for('jobs.manage_jobs'))
    
    # Get applications sorted by match score (highest first)
    applications = Application.query.filter_by(job_id=job.id).order_by(Application.match_score.desc()).all()
    
    return render_template(
        'jobs/applications.html',
        title=f'Applications for {job.title}',
        job=job,
        applications=applications
    )

@jobs.route('/jobs/<int:job_id>/toggle', methods=['POST'])
@login_required
def toggle_job_status(job_id):
    """Toggle job active status (recruiters only)"""
    if not current_user.is_recruiter():
        flash('Access denied. Recruiters only.', 'danger')
        return redirect(url_for('main.index'))
    
    job = Job.query.get_or_404(job_id)
    
    # Ensure recruiter owns this job
    if job.recruiter_id != current_user.id:
        flash('Access denied. You can only modify your own job postings.', 'danger')
        return redirect(url_for('jobs.manage_jobs'))
    
    job.is_active = not job.is_active
    db.session.commit()
    
    status = 'activated' if job.is_active else 'deactivated'
    flash(f'Job {status} successfully!', 'success')
    
    return redirect(url_for('jobs.manage_jobs'))

@jobs.route('/api/applications/<int:application_id>/status', methods=['POST'])
@login_required
def update_application_status(application_id):
    """API endpoint to update application status"""
    if not current_user.is_recruiter():
        return jsonify({'error': 'Unauthorized'}), 403
    
    application = Application.query.get_or_404(application_id)
    job = Job.query.get(application.job_id)
    
    # Check if recruiter owns this job
    if job.recruiter_id != current_user.id:
        return jsonify({'error': 'You can only update status for your own job applications'}), 403
    
    data = request.get_json()
    
    # Validate status
    valid_statuses = Application.get_valid_statuses()
    if 'status' not in data or data['status'] not in valid_statuses:
        return jsonify({'error': 'Invalid status', 'valid_statuses': valid_statuses}), 400
    
    # Skip update if status hasn't changed
    if application.status == data['status']:
        return jsonify({
            'success': True,
            'application_id': application.id,
            'status': application.status,
            'message': 'Status already set to ' + data['status']
        })
        
    # Update status
    previous_status = application.status
    application.status = data['status']
    application.updated_at = datetime.utcnow()
    
    # Add feedback if provided
    feedback = data.get('feedback', None)
    if feedback:
        # If a notes field exists in the application model, store it there
        if hasattr(application, 'notes'):
            application.notes = feedback
    
    # Commit changes to database
    db.session.commit()
    
    # Send email notification to applicant
    from app.utils.email import send_status_update
    try:
        send_status_update(application)
        email_sent = True
    except Exception as e:
        current_app.logger.error(f"Failed to send status update email: {str(e)}")
        email_sent = False
    
    return jsonify({
        'success': True,
        'application_id': application.id,
        'status': application.status,
        'previous_status': previous_status,
        'email_sent': email_sent,
        'message': 'Application status updated successfully'
    })

@jobs.route('/jobs/dashboard')
@login_required
def recruiter_dashboard():
    """Dashboard for recruiters with statistics and insights"""
    if not current_user.is_recruiter():
        flash('Access denied. Recruiters only.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all jobs posted by this recruiter
    recruiter_jobs = Job.query.filter_by(recruiter_id=current_user.id).all()
    
    # Count active and inactive jobs
    active_jobs_count = sum(1 for job in recruiter_jobs if job.is_active)
    inactive_jobs_count = len(recruiter_jobs) - active_jobs_count
    
    # Get application statistics
    total_applications = sum(len(job.applications) for job in recruiter_jobs)
    
    # Calculate applications by status
    status_counts = {
        'pending': 0,
        'reviewed': 0,
        'interviewed': 0,
        'offered': 0,
        'accepted': 0,
        'rejected': 0,
        'withdrawn': 0
    }
    
    # Calculate applications by job
    jobs_with_applications = []
    
    # Get unique applicants who have applied to this recruiter's jobs
    unique_applicants = set()
    top_applicants = []
    
    for job in recruiter_jobs:
        job_applications = job.applications
        
        # Count applications by status for this job
        job_status_counts = {
            'pending': 0,
            'reviewed': 0,
            'interviewed': 0,
            'offered': 0,
            'accepted': 0,
            'rejected': 0,
            'withdrawn': 0
        }
        
        for application in job_applications:
            status = application.status
            # Update overall status counts
            status_counts[status] += 1
            # Update job-specific status counts
            job_status_counts[status] += 1
            # Add to unique applicants set
            unique_applicants.add(application.applicant_id)
            
            # Add to top applicants list for sorting
            top_applicants.append({
                'applicant': application.applicant,
                'match_score': application.match_score,
                'job': job,
                'application': application
            })
        
        # Calculate average match score for this job
        avg_match_score = 0
        if job_applications:
            avg_match_score = sum(app.match_score for app in job_applications) / len(job_applications)
        
        jobs_with_applications.append({
            'job': job,
            'application_count': len(job_applications),
            'status_counts': job_status_counts,
            'avg_match_score': round(avg_match_score, 1)
        })
    
    # Sort jobs by application count (descending)
    jobs_with_applications.sort(key=lambda x: x['application_count'], reverse=True)
    
    # Sort top applicants by match score
    top_applicants.sort(key=lambda x: x['match_score'] if x['match_score'] is not None else 0, reverse=True)
    top_applicants = top_applicants[:5]  # Get top 5
    
    # Get recent applications (last 5)
    recent_applications = Application.query.join(Job).filter(
        Job.recruiter_id == current_user.id
    ).order_by(Application.created_at.desc()).limit(5).all()
    
    return render_template(
        'jobs/dashboard.html',
        title='Recruiter Dashboard',
        jobs_count=len(recruiter_jobs),
        active_jobs_count=active_jobs_count,
        inactive_jobs_count=inactive_jobs_count,
        total_applications=total_applications,
        status_counts=status_counts,
        jobs_with_applications=jobs_with_applications,
        recent_applications=recent_applications,
        unique_applicants_count=len(unique_applicants),
        top_applicants=top_applicants
    )

@jobs.route('/api/jobs/dashboard-data')
@login_required
def dashboard_data():
    """API endpoint for dashboard real-time data"""
    if not current_user.is_recruiter():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all jobs posted by this recruiter
    recruiter_jobs = Job.query.filter_by(recruiter_id=current_user.id).all()
    
    # Count active and inactive jobs
    active_jobs_count = sum(1 for job in recruiter_jobs if job.is_active)
    
    # Get application statistics
    total_applications = sum(len(job.applications) for job in recruiter_jobs)
    
    # Calculate applications by status
    status_counts = {
        'pending': 0,
        'reviewed': 0,
        'interviewed': 0,
        'offered': 0,
        'accepted': 0,
        'rejected': 0,
        'withdrawn': 0
    }
    
    # Get unique applicants who have applied to this recruiter's jobs
    unique_applicants = set()
    
    for job in recruiter_jobs:
        for application in job.applications:
            status = application.status
            # Update status counts
            status_counts[status] += 1
            # Add to unique applicants set
            unique_applicants.add(application.applicant_id)
    
    # Get recent applications (last 5)
    recent_applications_data = []
    recent_applications = Application.query.join(Job).filter(
        Job.recruiter_id == current_user.id
    ).order_by(Application.created_at.desc()).limit(5).all()
    
    for app in recent_applications:
        recent_applications_data.append({
            'id': app.id,
            'applicant_id': app.applicant_id,
            'applicant_name': app.applicant.name,
            'job_id': app.job_id,
            'job_title': app.job.title,
            'status': app.status,
            'match_score': int(round(app.match_score)) if app.match_score is not None else 0,
            'created_at': app.created_at.strftime('%b %d, %Y')
        })
    
    return jsonify({
        'success': True,
        'jobs_count': len(recruiter_jobs),
        'active_jobs_count': active_jobs_count,
        'inactive_jobs_count': len(recruiter_jobs) - active_jobs_count,
        'total_applications': total_applications,
        'status_counts': status_counts,
        'unique_applicants_count': len(unique_applicants),
        'recent_applications': recent_applications_data
    })

@jobs.route('/api/jobs/<int:job_id>/applications-data')
@login_required
def applications_data(job_id):
    """API endpoint for retrieving real-time applications data"""
    if not current_user.is_recruiter():
        return jsonify({'error': 'Unauthorized'}), 403
    
    job = Job.query.get_or_404(job_id)
    
    # Ensure recruiter owns this job
    if job.recruiter_id != current_user.id:
        return jsonify({'error': 'You can only view applications for your own job postings.'}), 403
    
    # Get applications sorted by match score (highest first)
    applications = Application.query.filter_by(job_id=job.id).order_by(Application.match_score.desc()).all()
    
    applications_data = []
    for app in applications:
        applications_data.append({
            'id': app.id,
            'applicant_id': app.applicant_id,
            'applicant_name': app.applicant.name,
            'job_id': app.job_id,
            'status': app.status,
            'match_score': int(round(app.match_score)) if app.match_score is not None else 0,
            'created_at': app.created_at.strftime('%b %d, %Y'),
            'updated_at': app.updated_at.strftime('%b %d, %Y')
        })
    
    return jsonify({
        'success': True,
        'job_id': job_id,
        'applications': applications_data
    })

@jobs.route('/api/jobs/manage-data')
@login_required
def manage_jobs_data():
    """API endpoint for retrieving real-time manage jobs data"""
    if not current_user.is_recruiter():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all jobs posted by this recruiter
    recruiter_jobs = Job.query.filter_by(recruiter_id=current_user.id).order_by(Job.created_at.desc()).all()
    
    jobs_data = []
    for job in recruiter_jobs:
        # Get skill names
        skill_names = [skill.name for skill in job.skills]
        
        jobs_data.append({
            'id': job.id,
            'title': job.title,
            'location': job.location,
            'skills': skill_names,
            'created_at': job.created_at.strftime('%b %d, %Y'),
            'is_active': job.is_active,
            'application_count': len(job.applications)
        })
    
    return jsonify({
        'success': True,
        'jobs': jobs_data
    }) 