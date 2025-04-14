from icalendar import Calendar, Event, vCalAddress, vText
from datetime import datetime
from pytz import timezone
import os
import uuid

def generate_calendar_invite(interview, saved_path=None):
    """
    Generate an .ics file for an interview.
    
    Args:
        interview: The Interview object containing all details
        saved_path: Optional path to save the .ics file to disk
        
    Returns:
        The .ics file as a string, and the path if saved to disk
    """
    # Create a new calendar
    cal = Calendar()
    
    # Set calendar properties
    cal.add('prodid', '-//JobMatch//jobmatch.com//')
    cal.add('version', '2.0')
    cal.add('method', 'REQUEST')
    
    # Create an event
    event = Event()
    
    # Set event properties
    event.add('summary', f"{interview.stage.capitalize()} Interview: {interview.job.title}")
    event.add('dtstart', interview.scheduled_at)
    event.add('dtend', interview.end_time)
    event.add('dtstamp', datetime.utcnow())
    event['uid'] = str(uuid.uuid4())
    
    # Add interview details to description
    description = f"""
    Job Title: {interview.job.title}
    Company: {interview.job.recruiter.company}
    Stage: {interview.stage.capitalize()}
    Type: {interview.interview_type.capitalize()}
    """
    
    # Add type-specific details
    if interview.interview_type == 'video':
        description += f"\nVideo Platform: {interview.video_platform}"
        if interview.video_link:
            description += f"\nVideo Link: {interview.video_link}"
    elif interview.interview_type == 'phone':
        if interview.phone_number:
            description += f"\nPhone Number: {interview.phone_number}"
        if interview.who_calls:
            description += f"\nWho Calls: {interview.who_calls.capitalize()}"
    elif interview.interview_type == 'in-person':
        if interview.location:
            description += f"\nLocation: {interview.location}"
    
    # Add interviewers
    if interview.interviewers:
        interviewers = ", ".join([interviewer.name for interviewer in interview.interviewers])
        description += f"\n\nInterviewer(s): {interviewers}"
    
    # Add any interview notes
    if interview.notes:
        description += f"\n\nAdditional Notes:\n{interview.notes}"
    
    event.add('description', description)
    
    # Set location or URL based on interview type
    if interview.interview_type == 'in-person' and interview.location:
        event.add('location', interview.location)
    elif interview.interview_type == 'video' and interview.video_link:
        event.add('location', interview.video_link)
        event.add('url', interview.video_link)
        
    # Add participants
    organizer = vCalAddress(f'MAILTO:{interview.created_by.email}')
    organizer.params['cn'] = vText(interview.created_by.name)
    organizer.params['role'] = vText('CHAIR')
    event.add('organizer', organizer)
    
    # Add attendees
    # Candidate
    attendee = vCalAddress(f'MAILTO:{interview.candidate.email}')
    attendee.params['cn'] = vText(interview.candidate.name)
    attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
    event.add('attendee', attendee)
    
    # Interviewers
    for interviewer in interview.interviewers:
        attendee = vCalAddress(f'MAILTO:{interviewer.email}')
        attendee.params['cn'] = vText(interviewer.name)
        attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
        event.add('attendee', attendee)
    
    # Add reminders (alerts)
    # 1 day before
    event.add('valarm', {
        'action': 'DISPLAY',
        'description': f"Reminder: {interview.stage.capitalize()} Interview for {interview.job.title}",
        'trigger': '-P1D'  # 1 day before
    })
    # 1 hour before
    event.add('valarm', {
        'action': 'DISPLAY',
        'description': f"Reminder: {interview.stage.capitalize()} Interview for {interview.job.title}",
        'trigger': '-PT1H'  # 1 hour before
    })
    
    # Add the event to the calendar
    cal.add_component(event)
    
    # Convert to string
    ics_content = cal.to_ical()
    
    # Save to file if path provided
    if saved_path:
        dirname = os.path.dirname(saved_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        
        with open(saved_path, 'wb') as f:
            f.write(ics_content)
            
        # Update the interview object with the calendar path
        interview.calendar_link = saved_path
        
        return ics_content, saved_path
    
    return ics_content 