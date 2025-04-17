from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import JSONB

# Association table for many-to-many relationship between interviews and interviewers
interview_interviewers = db.Table('interview_interviewers',
    db.Column('interview_id', db.Integer, db.ForeignKey('interviews.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class Interview(db.Model):
    """Model for job interviews."""
    __tablename__ = 'interviews'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('job_applications.id'), nullable=False)
    
    # Interview details
    stage = db.Column(db.String(50), nullable=False)  # screening, technical, behavioral, etc.
    custom_stage = db.Column(db.String(100))  # Used when stage is 'custom'
    interview_type = db.Column(db.String(50), nullable=False)  # video, phone, in-person, technical
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False, default=60)  # in minutes
    status = db.Column(db.String(20), nullable=False, default='scheduled')  # scheduled, completed, cancelled, no_show
    
    # Type-specific fields
    video_platform = db.Column(db.String(50))  # For video interviews: zoom, teams, etc.
    video_link = db.Column(db.String(255))  # For video interviews: meeting URL
    phone_number = db.Column(db.String(20))  # For phone interviews
    who_calls = db.Column(db.String(20))  # For phone interviews: interviewer or candidate
    location = db.Column(db.String(255))  # For in-person interviews
    technical_details = db.Column(db.Text)  # For technical interviews: details about the assessment
    
    # Additional info
    notes = db.Column(db.Text)  # Interview notes visible to interviewers
    calendar_link = db.Column(db.String(255))  # Link to add to calendar
    
    # Status tracking fields
    completed_at = db.Column(db.DateTime)  # When feedback was submitted
    cancelled_at = db.Column(db.DateTime)  # When the interview was cancelled
    cancelled_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Who cancelled
    cancellation_reason = db.Column(db.Text)  # Why it was cancelled
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    job = db.relationship('Job', backref=db.backref('interviews', lazy='dynamic'))
    candidate = db.relationship('User', foreign_keys=[applicant_id], backref=db.backref('candidate_interviews', lazy='dynamic'))
    application = db.relationship('JobApplication', backref=db.backref('interviews', lazy='dynamic'))
    cancelled_by = db.relationship('User', foreign_keys=[cancelled_by_id])
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    interviewers = db.relationship('User', secondary=interview_interviewers, 
                                  backref=db.backref('interviewer_interviews', lazy='dynamic'))
    feedback = db.relationship('InterviewFeedback', backref='interview', uselist=False)
    
    @property
    def end_time(self):
        """Calculate the end time based on duration."""
        return self.scheduled_at + timedelta(minutes=self.duration)
    
    @property
    def interviewer_ids(self):
        """Return list of interviewer IDs for easier template access."""
        return [interviewer.id for interviewer in self.interviewers]
    
    @property
    def is_upcoming(self):
        """Check if the interview is upcoming (scheduled and in the future)."""
        return self.status == 'scheduled' and self.scheduled_at > datetime.utcnow()
    
    @property
    def is_past_due(self):
        """Check if the interview time has passed but it's still marked as scheduled."""
        return self.status == 'scheduled' and self.scheduled_at < datetime.utcnow()
    
    @property
    def needs_feedback(self):
        """Check if the interview needs feedback (completed without feedback)."""
        return self.status == 'completed' and not self.feedback
    
    def __repr__(self):
        return f'<Interview {self.id}: {self.job.title}, {self.candidate.name}, {self.scheduled_at}>'


class InterviewFeedback(db.Model):
    """Model for interview feedback provided by interviewers."""
    __tablename__ = 'interview_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id'), nullable=False)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Basic feedback
    overall_rating = db.Column(db.Integer, nullable=False)  # 1-5 rating
    recommendation = db.Column(db.String(20), nullable=False)  # strong_yes, yes, maybe, no, strong_no
    strengths = db.Column(db.Text, nullable=False)
    areas_for_improvement = db.Column(db.Text, nullable=False)
    cultural_fit = db.Column(db.Text)
    additional_comments = db.Column(db.Text)
    
    # Advanced feedback
    skills_assessment = db.Column(JSONB)  # JSON array of skill assessments
    
    # Status and visibility
    is_draft = db.Column(db.Boolean, default=False)
    is_private = db.Column(db.Boolean, default=False)  # If true, only visible to recruiters/managers
    
    # Timestamps
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    submitted_by = db.relationship('User', backref=db.backref('interview_feedback', lazy='dynamic'))
    
    def __repr__(self):
        return f'<InterviewFeedback {self.id}: Interview {self.interview_id}, Rating {self.overall_rating}/5>' 