from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin
import uuid

# Association tables for many-to-many relationships
user_skills = db.Table('user_skills',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'), primary_key=True)
)

job_skills = db.Table('job_skills',
    db.Column('job_id', db.Integer, db.ForeignKey('jobs.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'applicant' or 'recruiter'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    profile_completed = db.Column(db.Boolean, default=False)
    
    # Applicant specific fields
    resume = db.Column(db.Text, nullable=True)
    experience = db.Column(db.Integer, nullable=True)  # In years
    education = db.Column(db.String(120), nullable=True)
    
    # Recruiter specific fields
    company = db.Column(db.String(120), nullable=True)
    position = db.Column(db.String(80), nullable=True)
    
    # Relationships
    skills = db.relationship('Skill', secondary=user_skills, backref=db.backref('users', lazy='dynamic'))
    jobs = db.relationship('Job', backref='recruiter', lazy=True)
    applications = db.relationship('Application', back_populates='applicant', lazy=True, foreign_keys='Application.applicant_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_recruiter(self):
        return self.user_type == 'recruiter'
    
    def is_applicant(self):
        return self.user_type == 'applicant'
    
    def __repr__(self):
        return f'<User {self.name}>'

class Skill(db.Model):
    __tablename__ = 'skills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<Skill {self.name}>'

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(120), nullable=False)
    salary = db.Column(db.String(80), nullable=True)
    experience_required = db.Column(db.Integer, default=0)  # In years
    recruiter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    skills = db.relationship('Skill', secondary=job_skills, backref=db.backref('jobs', lazy='dynamic'))
    applications = db.relationship('Application', back_populates='job', lazy=True, foreign_keys='Application.job_id')
    
    def match_score(self, user):
        """Calculate a match score between job and applicant"""
        if not user.is_applicant():
            return 0
            
        # Calculate score based on skills match
        job_skills_set = {skill.id for skill in self.skills}
        user_skills_set = {skill.id for skill in user.skills}
        
        common_skills = job_skills_set.intersection(user_skills_set)
        total_job_skills = len(job_skills_set)
        
        # Skill match percentage
        skill_score = len(common_skills) / total_job_skills * 100 if total_job_skills > 0 else 0
        
        # Experience match
        exp_score = 0
        if self.experience_required <= user.experience:
            exp_score = 100
        elif user.experience > 0:
            exp_score = (user.experience / self.experience_required) * 100
            
        # Calculate final score (skills are weighted more)
        final_score = (skill_score * 0.7) + (exp_score * 0.3)
        return round(final_score, 2)
    
    def __repr__(self):
        return f'<Job {self.title}>'

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, interviewed, offered, rejected, accepted, withdrawn
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cover_letter = db.Column(db.Text, nullable=True)
    match_score = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)  # For feedback and recruiter notes
    
    # Relationships
    job = db.relationship('Job', back_populates='applications', foreign_keys=[job_id])
    applicant = db.relationship('User', back_populates='applications', foreign_keys=[applicant_id])
    
    @staticmethod
    def get_status_message(status):
        """Get default message for a given application status"""
        status_messages = {
            'pending': 'Your application is pending review by the hiring team. We will notify you of any updates.',
            'reviewed': 'Your application has been reviewed by our hiring team. They found your profile interesting and have moved your application to the next stage.',
            'interviewed': 'Congratulations! You have been selected for an interview. You will receive further communication about the interview details soon.',
            'offered': 'Congratulations! We are pleased to inform you that you have been offered the position. Please log in to your account to view and respond to the offer.',
            'rejected': 'Thank you for your interest in the position. After careful consideration, we have decided to move forward with other candidates whose qualifications more closely match our current needs.',
            'accepted': 'Congratulations! You have accepted our job offer. We are excited to have you join our team. You will receive further information about your onboarding process soon.',
            'withdrawn': 'Your application has been marked as withdrawn. If you believe this is an error, please contact our support team.'
        }
        return status_messages.get(status, 'Your application status has been updated.')
    
    @staticmethod
    def get_valid_statuses():
        """Get list of valid application statuses"""
        return ['pending', 'reviewed', 'interviewed', 'offered', 'accepted', 'rejected', 'withdrawn']
    
    def __repr__(self):
        return f'<Application {self.id}>'

class RecruiterNote(db.Model):
    __tablename__ = 'recruiter_notes'
    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recruiter = db.relationship('User', foreign_keys=[recruiter_id], backref='recruiter_notes')
    applicant = db.relationship('User', foreign_keys=[applicant_id], backref='applicant_notes')
    
    def __repr__(self):
        return f'<RecruiterNote {self.id}>'

class Interview(db.Model):
    """Model for job interviews between recruiters and applicants"""
    __tablename__ = 'interviews'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, rescheduled
    interview_type = db.Column(db.String(20), nullable=False)  # in_person, phone, video
    location = db.Column(db.String(255), nullable=True)  # For in-person interviews
    video_link = db.Column(db.String(255), nullable=True)  # For video interviews
    notes = db.Column(db.Text, nullable=True)
    cancellation_reason = db.Column(db.Text, nullable=True)  # If interview is cancelled
    
    # Define relationships
    job = db.relationship('Job', backref=db.backref('interviews', lazy=True))
    recruiter = db.relationship('User', foreign_keys=[recruiter_id], backref=db.backref('interviews_as_recruiter', lazy=True))
    applicant = db.relationship('User', foreign_keys=[applicant_id], backref=db.backref('interviews_as_applicant', lazy=True))
    
    def __repr__(self):
        return f'<Interview {self.id}: {self.job_id}, {self.applicant_id}>'
        
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'recruiter_id': self.recruiter_id,
            'applicant_id': self.applicant_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'status': self.status,
            'interview_type': self.interview_type,
            'location': self.location,
            'video_link': self.video_link,
            'notes': self.notes
        }

class ChatMessage(db.Model):
    """Model for storing chat conversations"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for guest users
    session_id = db.Column(db.String(100), nullable=False)  # To group conversations
    message = db.Column(db.Text, nullable=False)
    is_bot = db.Column(db.Boolean, default=False)  # True for bot messages, False for user messages
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    context = db.Column(db.JSON, nullable=True)  # For storing conversation context
    
    # Relationship
    user = db.relationship('User', backref=db.backref('chat_messages', lazy=True))
    
    def __repr__(self):
        return f'<ChatMessage {self.id}: {"Bot" if self.is_bot else "User"}>'
    
    def serialize(self):
        """Return message in serializable format"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'message': self.message,
            'is_bot': self.is_bot,
            'created_at': self.created_at.isoformat(),
            'context': self.context
        }

class ChatbotIntent(db.Model):
    """Model for chatbot predefined intents and responses"""
    __tablename__ = 'chatbot_intents'
    
    id = db.Column(db.Integer, primary_key=True)
    intent_name = db.Column(db.String(100), unique=True, nullable=False)
    keywords = db.Column(db.JSON, nullable=False)  # Array of keywords that trigger this intent
    response_template = db.Column(db.Text, nullable=False)  # Can include variables with {var_name} syntax
    follow_up_questions = db.Column(db.JSON, nullable=True)  # Potential follow-up questions to show
    
    def __repr__(self):
        return f'<ChatbotIntent {self.intent_name}>'
    
    def serialize(self):
        """Return intent in serializable format"""
        return {
            'id': self.id,
            'intent_name': self.intent_name,
            'keywords': self.keywords,
            'response_template': self.response_template,
            'follow_up_questions': self.follow_up_questions
        }

class UserChatPreference(db.Model):
    """Model for storing user chatbot preferences"""
    __tablename__ = 'user_chat_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    auto_suggestions = db.Column(db.Boolean, default=True)
    chat_history_enabled = db.Column(db.Boolean, default=True)
    notification_enabled = db.Column(db.Boolean, default=True)
    theme = db.Column(db.String(20), default='light')  # light or dark
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('chat_preference', uselist=False, lazy=True))
    
    def __repr__(self):
        return f'<UserChatPreference {self.user_id}>'
    
    def serialize(self):
        """Return preferences in serializable format"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'auto_suggestions': self.auto_suggestions,
            'chat_history_enabled': self.chat_history_enabled,
            'notification_enabled': self.notification_enabled,
            'theme': self.theme
        } 