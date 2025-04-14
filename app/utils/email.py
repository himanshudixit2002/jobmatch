from flask import current_app, render_template
from flask_mail import Message
from threading import Thread
from datetime import datetime
import os

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            from app import mail
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {str(e)}")

def send_email(subject, sender, recipients, text_body, html_body):
    """Send an email"""
    try:
        from app import mail
        app = current_app._get_current_object()
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        
        # Send asynchronously
        Thread(target=send_async_email, args=(app, msg)).start()
        return True
    except Exception as e:
        current_app.logger.error(f"Error preparing email: {str(e)}")
        return False

def send_application_notification(application):
    """Send notification to recruiter about new application"""
    job = application.job
    applicant = application.applicant
    recruiter = job.recruiter
    
    subject = f"New Application: {job.title}"
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    recipients = [recruiter.email]
    
    text_body = render_template('email/new_application.txt', 
                               job=job, 
                               applicant=applicant,
                               application=application)
    
    html_body = render_template('email/new_application.html', 
                               job=job, 
                               applicant=applicant,
                               application=application)
    
    return send_email(subject, sender, recipients, text_body, html_body)

def send_status_update(application):
    """Send status update email to applicant"""
    job = application.job
    applicant = application.applicant
    
    subject = f"Application Status Update: {job.title}"
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    recipients = [applicant.email]
    
    # Validate that application status is valid
    valid_statuses = application.get_valid_statuses()
    if application.status not in valid_statuses:
        current_app.logger.error(f"Invalid application status: {application.status}")
        application.status = 'pending'  # Set to default if invalid
    
    text_body = render_template('email/status_update.txt', 
                               job=job, 
                               application=application)
    
    html_body = render_template('email/status_update.html', 
                               job=job, 
                               application=application)
    
    return send_email(subject, sender, recipients, text_body, html_body)

def send_job_recommendations(user, jobs):
    """Send job recommendations to applicant"""
    subject = "Job Recommendations For You"
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    recipients = [user.email]
    
    text_body = render_template('email/job_recommendations.txt', 
                               user=user,
                               jobs=jobs,
                               date=datetime.utcnow())
    
    html_body = render_template('email/job_recommendations.html', 
                               user=user,
                               jobs=jobs,
                               date=datetime.utcnow())
    
    return send_email(subject, sender, recipients, text_body, html_body)

def send_test_email(recipient):
    """Send a test email to verify the email configuration"""
    subject = "JobMatch Email Test"
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    recipients = [recipient]
    
    text_body = """
    This is a test email from JobMatch system.
    
    If you're receiving this, the email system is configured correctly.
    
    Best regards,
    JobMatch Team
    """
    
    html_body = """
    <html>
        <body>
            <h1>JobMatch Email Test</h1>
            <p>This is a test email from JobMatch system.</p>
            <p>If you're receiving this, the email system is configured correctly.</p>
            <p>Best regards,<br>JobMatch Team</p>
        </body>
    </html>
    """
    
    return send_email(subject, sender, recipients, text_body, html_body) 