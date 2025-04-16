"""
Simple database initialization script without depending on all modules
"""
import os
from app import create_app
from app.models.models import db, User, Skill, Job, Application

# Create the Flask app with its context
app = create_app()
app_context = app.app_context()
app_context.push()

def init_db():
    try:
        print("Creating database tables...")
        db.create_all()
        
        # Only create sample data if there are no users yet
        if User.query.count() == 0:
            print("Creating initial sample data...")
            
            # Create some basic skills
            skills = [
                'Python', 'JavaScript', 'React', 'SQL'
            ]
            
            for skill_name in skills:
                skill = Skill(name=skill_name)
                db.session.add(skill)
            
            db.session.commit()
            print("Basic skills created.")
            
            # Create a sample recruiter and applicant
            recruiter = User(
                name='John Recruiter',
                email='recruiter@example.com',
                user_type='recruiter',
                company='Example Corp'
            )
            recruiter.set_password('password')
            
            applicant = User(
                name='Jane Applicant',
                email='applicant@example.com',
                user_type='applicant',
                experience=3
            )
            applicant.set_password('password')
            
            db.session.add_all([recruiter, applicant])
            db.session.commit()
            print("Sample users created.")
            
            # Create a sample job
            python_skill = Skill.query.filter_by(name='Python').first()
            sql_skill = Skill.query.filter_by(name='SQL').first()
            
            job = Job(
                title='Python Developer',
                description='Entry-level Python developer position',
                location='Remote',
                recruiter_id=recruiter.id
            )
            job.skills.extend([python_skill, sql_skill])
            
            db.session.add(job)
            db.session.commit()
            print("Sample job created.")
            
            print("Database initialized successfully!")
        else:
            print("Database already contains data. Skipping sample data creation.")
    
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
    finally:
        app_context.pop()

if __name__ == "__main__":
    init_db() 