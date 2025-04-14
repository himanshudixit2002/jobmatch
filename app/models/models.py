from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

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