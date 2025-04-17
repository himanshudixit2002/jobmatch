from flask import render_template
from flask_mail import Message
from app import mail
from app import app
from datetime import datetime

def send_job_recommendations(user, job_matches):
    """
    Send job recommendation emails to users
    
    Args:
        user: User object containing email and name
        job_matches: List of job matches with score
    """
    subject = "Job Recommendations Just For You"
    
    html = render_template(
        'email/job_recommendation.html',
        user=user,
        job_matches=job_matches,
        now=datetime.utcnow(),
        email_address=user.email
    )
    
    msg = Message(
        subject=subject,
        recipients=[user.email],
        html=html
    )
    
    mail.send(msg)

def send_application_status_update(applicant, job, status, feedback=None):
    """
    Send application status update emails to applicants
    
    Args:
        applicant: User object containing email and name
        job: Job object with title and company
        status: Current application status (UNDER_REVIEW, INTERVIEW, REJECTED, HIRED)
        feedback: Optional feedback from recruiter
    """
    subject = f"Application Status Update: {job.title} at {job.company}"
    
    text = render_template(
        'email/application_status.txt',
        applicant=applicant,
        job=job,
        status=status,
        feedback=feedback
    )
    
    html = render_template(
        'email/application_status.html',
        applicant=applicant,
        job=job,
        status=status,
        feedback=feedback,
        now=datetime.utcnow(),
        email_address=applicant.email
    )
    
    msg = Message(
        subject=subject,
        recipients=[applicant.email],
        body=text,
        html=html
    )
    
    mail.send(msg)

def send_new_application_notification(recruiter, applicant, job):
    """
    Send notification to recruiters when a new application is submitted
    
    Args:
        recruiter: Recruiter user object with email
        applicant: Applicant user object with name
        job: Job object with title
    """
    subject = f"New Application for {job.title}"
    
    text = f"""
    Hello {recruiter.name},
    
    A new application has been submitted for {job.title}.
    
    Applicant: {applicant.name}
    Applied on: {applicant.application.created_at}
    
    You can review this application by visiting your dashboard:
    {app.config['BASE_URL']}/dashboard/applications
    
    Best regards,
    Job Portal Team
    """
    
    html = render_template(
        'email/new_application_notification.html',
        recruiter=recruiter,
        applicant=applicant,
        job=job,
        now=datetime.utcnow()
    )
    
    msg = Message(
        subject=subject,
        recipients=[recruiter.email],
        body=text,
        html=html
    )
    
    mail.send(msg) 