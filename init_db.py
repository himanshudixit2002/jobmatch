import os
from app import create_app
from app.models.models import User, Skill, Job, Application
from app.extensions import db

# Create the Flask app with its context
app = create_app()

with app.app_context():
    # Initialize the database
    db.drop_all()  # Drop all existing tables
    db.create_all()  # Create all tables

    print("Creating initial data...")

    # Create initial skills
    skills = [
        'Python', 'JavaScript', 'React', 'Angular', 'Vue.js',
        'Node.js', 'Flask', 'Django', 'SQL', 'NoSQL', 'MongoDB',
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
        'Machine Learning', 'Data Science', 'Artificial Intelligence',
        'DevOps', 'CI/CD', 'Testing', 'REST API', 'HTML', 'CSS'
    ]

    for skill_name in skills:
        skill = Skill(name=skill_name)
        db.session.add(skill)

    db.session.commit()
    print("Skills created...")

    # Create some demo recruiters
    recruiter1 = User(
        name='John Smith',
        email='recruiter1@example.com',
        user_type='recruiter',
        company='Tech Solutions Inc.',
        position='Senior Recruiter'
    )
    recruiter1.set_password('password')

    recruiter2 = User(
        name='Emily Johnson',
        email='recruiter2@example.com',
        user_type='recruiter',
        company='Innovative Systems',
        position='HR Manager'
    )
    recruiter2.set_password('password')

    # Create some demo applicants
    applicant1 = User(
        name='Michael Brown',
        email='applicant1@example.com',
        user_type='applicant',
        experience=5,
        education='Bachelor of Computer Science'
    )
    applicant1.set_password('password')

    applicant2 = User(
        name='Sarah Wilson',
        email='applicant2@example.com',
        user_type='applicant',
        experience=3,
        education='Master of Information Technology'
    )
    applicant2.set_password('password')

    applicant3 = User(
        name='David Lee',
        email='applicant3@example.com',
        user_type='applicant',
        experience=1,
        education='Bachelor of Software Engineering'
    )
    applicant3.set_password('password')

    # Add users to session
    db.session.add_all([recruiter1, recruiter2, applicant1, applicant2, applicant3])
    db.session.commit()
    print("Users created...")

    # Assign skills to applicants
    python_skill = Skill.query.filter_by(name='Python').first()
    js_skill = Skill.query.filter_by(name='JavaScript').first()
    react_skill = Skill.query.filter_by(name='React').first()
    flask_skill = Skill.query.filter_by(name='Flask').first()
    sql_skill = Skill.query.filter_by(name='SQL').first()
    aws_skill = Skill.query.filter_by(name='AWS').first()
    ml_skill = Skill.query.filter_by(name='Machine Learning').first()
    css_skill = Skill.query.filter_by(name='CSS').first()
    html_skill = Skill.query.filter_by(name='HTML').first()

    applicant1.skills.extend([python_skill, flask_skill, sql_skill, ml_skill])
    applicant2.skills.extend([js_skill, react_skill, html_skill, css_skill])
    applicant3.skills.extend([python_skill, js_skill, aws_skill])
    db.session.commit()
    print("Skills assigned to users...")

    # Create some job postings
    job1 = Job(
        title='Python Developer',
        description='''We're looking for a Python developer to join our backend team. 
        You will be responsible for developing and maintaining our core services.
        
        Requirements:
        - Strong understanding of Python
        - Experience with Flask or similar frameworks
        - Knowledge of SQL databases
        - Experience with API development
        ''',
        location='New York, NY',
        salary='$90,000 - $120,000',
        experience_required=3,
        recruiter_id=recruiter1.id
    )
    job1.skills.extend([python_skill, flask_skill, sql_skill])

    job2 = Job(
        title='Frontend Developer',
        description='''We are seeking a talented Frontend Developer to create amazing user experiences.
        
        Responsibilities:
        - Develop responsive web applications
        - Work with designers to implement UI/UX
        - Optimize applications for performance
        
        Requirements:
        - Experience with JavaScript and modern frameworks
        - Proficiency in HTML/CSS
        - Understanding of responsive design principles
        ''',
        location='Remote',
        salary='$85,000 - $105,000',
        experience_required=2,
        recruiter_id=recruiter2.id
    )
    job2.skills.extend([js_skill, react_skill, html_skill, css_skill])

    job3 = Job(
        title='Data Scientist',
        description='''Join our data team to develop machine learning models and analyze complex datasets.
        
        Responsibilities:
        - Build and optimize machine learning models
        - Work with large datasets to extract insights
        - Collaborate with cross-functional teams
        
        Requirements:
        - Experience with Python and data science libraries
        - Understanding of machine learning algorithms
        - Knowledge of SQL and data processing
        ''',
        location='San Francisco, CA',
        salary='$110,000 - $140,000',
        experience_required=4,
        recruiter_id=recruiter1.id
    )
    job3.skills.extend([python_skill, ml_skill, sql_skill])

    # Add jobs to session
    db.session.add_all([job1, job2, job3])
    db.session.commit()
    print("Jobs created...")

    # Create some applications
    application1 = Application(
        job_id=job1.id,
        applicant_id=applicant1.id,
        cover_letter='''I am excited to apply for the Python Developer position. With 5 years of experience building backend services using Python and Flask, I believe I would be a great fit for your team.''',
        match_score=job1.match_score(applicant1)
    )

    application2 = Application(
        job_id=job2.id,
        applicant_id=applicant2.id,
        cover_letter='''I have been working with React and modern JavaScript for the past 3 years and would love to bring my frontend skills to your team.''',
        match_score=job2.match_score(applicant2)
    )

    # Add applications to session
    db.session.add_all([application1, application2])
    db.session.commit()
    print("Applications created...")

    print('Database initialized with sample data!') 