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

def send_interview_invitation(interview):
    """Send interview invitation to candidate"""
    job = interview.job
    candidate = interview.candidate
    
    subject = f"Interview Invitation: {job.title}"
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    recipients = [candidate.email]
    
    # Get formatted date and time
    formatted_date = interview.scheduled_at.strftime('%A, %B %d, %Y')
    formatted_time = interview.scheduled_at.strftime('%I:%M %p')
    
    text_body = render_template('email/interview_invitation.txt',
                               interview=interview,
                               job=job,
                               candidate=candidate,
                               formatted_date=formatted_date,
                               formatted_time=formatted_time)
    
    html_body = render_template('email/interview_invitation.html',
                               interview=interview,
                               job=job,
                               candidate=candidate,
                               formatted_date=formatted_date,
                               formatted_time=formatted_time)
    
    # CC recruiters and interviewers
    cc_recipients = []
    for interviewer in interview.interviewers:
        cc_recipients.append(interviewer.email)
    
    msg = Message(subject, sender=sender, recipients=recipients, cc=cc_recipients)
    msg.body = text_body
    msg.html = html_body
    
    # If there's a calendar attachment, add it
    if interview.calendar_link:
        with current_app.open_resource(interview.calendar_link) as f:
            msg.attach("interview.ics", "text/calendar", f.read())
    
    # Send directly without using send_email helper since we need to attach files
    app = current_app._get_current_object()
    Thread(target=send_async_email, args=(app, msg)).start()
    return True

def send_interview_reminder(interview):
    """Send interview reminder to both candidate and interviewers"""
    job = interview.job
    candidate = interview.candidate
    
    # Get formatted date and time
    formatted_date = interview.scheduled_at.strftime('%A, %B %d, %Y')
    formatted_time = interview.scheduled_at.strftime('%I:%M %p')
    
    # Send to candidate
    subject = f"Reminder: Upcoming Interview for {job.title}"
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    
    # Candidate notification
    candidate_text = render_template('email/interview_reminder_candidate.txt',
                                  interview=interview,
                                  job=job,
                                  formatted_date=formatted_date,
                                  formatted_time=formatted_time)
    
    candidate_html = render_template('email/interview_reminder_candidate.html',
                                  interview=interview,
                                  job=job,
                                  formatted_date=formatted_date,
                                  formatted_time=formatted_time)
    
    send_email(subject, sender, [candidate.email], candidate_text, candidate_html)
    
    # Interviewers notification
    if interview.interviewers:
        interviewer_emails = [interviewer.email for interviewer in interview.interviewers]
        
        if interviewer_emails:
            subject = f"Reminder: You're conducting an interview for {job.title}"
            
            interviewer_text = render_template('email/interview_reminder_interviewer.txt',
                                         interview=interview,
                                         job=job,
                                         candidate=candidate,
                                         formatted_date=formatted_date,
                                         formatted_time=formatted_time)
            
            interviewer_html = render_template('email/interview_reminder_interviewer.html',
                                         interview=interview,
                                         job=job,
                                         candidate=candidate,
                                         formatted_date=formatted_date,
                                         formatted_time=formatted_time)
            
            send_email(subject, sender, interviewer_emails, interviewer_text, interviewer_html)
    
    return True

def send_interview_feedback_notification(feedback):
    """Send notification about interview feedback"""
    interview = feedback.interview
    job = interview.job
    candidate = interview.candidate
    submitted_by = feedback.submitted_by
    
    # Only notify the hiring manager/recruiter (not the candidate)
    subject = f"New Interview Feedback: {candidate.name} for {job.title}"
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    
    # Get the hiring manager (job creator)
    hiring_manager = job.recruiter
    recipients = [hiring_manager.email]
    
    # Add all other interviewers except the one who submitted feedback
    for interviewer in interview.interviewers:
        if interviewer.id != submitted_by.id and interviewer.id != hiring_manager.id:
            recipients.append(interviewer.email)
    
    # Remove duplicates
    recipients = list(set(recipients))
    
    text_body = render_template('email/interview_feedback_notification.txt',
                               feedback=feedback,
                               interview=interview,
                               job=job,
                               candidate=candidate,
                               submitted_by=submitted_by)
    
    html_body = render_template('email/interview_feedback_notification.html',
                               feedback=feedback,
                               interview=interview,
                               job=job,
                               candidate=candidate,
                               submitted_by=submitted_by)
    
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