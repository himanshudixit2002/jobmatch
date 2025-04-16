import os
import sys
import random
import string
import argparse
from datetime import datetime, timedelta
from faker import Faker
from werkzeug.security import generate_password_hash
from tqdm import tqdm

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.getcwd()))

# Import models
from app import create_app
from app.models.models import db, User, Skill, Job, Application

# Create Flask app context
app = create_app()
app_context = app.app_context()
app_context.push()

# Initialize faker
fake = Faker()

# Constants
INDIAN_COMPANIES = [
    'Tata Consultancy Services', 'Infosys', 'Wipro', 'HCL Technologies', 'Tech Mahindra',
    'Cognizant', 'Larsen & Toubro Infotech', 'Mindtree', 'Mphasis', 'Hexaware Technologies',
    'Reliance Industries', 'HDFC Bank', 'ICICI Bank', 'State Bank of India', 'Bharti Airtel',
    'Mahindra & Mahindra', 'Hindustan Unilever', 'ITC Limited', 'Bajaj Auto', 'Hero MotoCorp',
    'Zomato', 'Swiggy', 'Flipkart', 'Myntra', 'Nykaa', 'Ola', 'Paytm', 'BYJU\'S', 'Freshworks',
    'Razorpay', 'Zerodha', 'Dream11', 'CRED', 'Groww', 'Meesho', 'Unacademy', 'upGrad',
    'PhonePe', 'BigBasket', 'Urban Company', 'PolicyBazaar', 'CarDekho', 'Healthkart',
    'Mamaearth', 'boAt', 'Vedantu', 'Jio Platforms', 'Snapdeal', 'InMobi', 'MakeMyTrip'
]

INDIAN_COLLEGES = [
    'Indian Institute of Technology, Delhi', 'Indian Institute of Technology, Bombay',
    'Indian Institute of Technology, Madras', 'Indian Institute of Technology, Kanpur',
    'Indian Institute of Technology, Kharagpur', 'Indian Institute of Technology, Roorkee',
    'Indian Institute of Technology, Guwahati', 'Indian Institute of Technology, Hyderabad',
    'Indian Institute of Science, Bangalore', 'Birla Institute of Technology and Science, Pilani',
    'National Institute of Technology, Tiruchirappalli', 'National Institute of Technology, Surathkal',
    'Delhi Technological University', 'College of Engineering, Pune', 'PSG College of Technology',
    'Vellore Institute of Technology', 'SRM Institute of Science and Technology',
    'Manipal Institute of Technology', 'Thapar Institute of Engineering and Technology',
    'Jadavpur University', 'Anna University'
]

GLOBAL_COMPANIES = [
    'Google', 'Microsoft', 'Apple', 'Amazon', 'Facebook', 'Netflix', 'IBM', 'Intel', 'Oracle',
    'Salesforce', 'Adobe', 'Cisco', 'Dell', 'HP', 'Twitter', 'Uber', 'Airbnb', 'Slack',
    'Spotify', 'LinkedIn', 'Dropbox', 'Square', 'Zoom', 'PayPal', 'eBay', 'Tesla', 'Nvidia',
    'AMD', 'Qualcomm', 'SAP', 'Accenture', 'Deloitte', 'PwC', 'EY', 'KPMG', 'McKinsey',
    'BCG', 'Bain', 'Goldman Sachs', 'JPMorgan Chase', 'Morgan Stanley', 'Bank of America',
    'Citigroup', 'Wells Fargo', 'Capital One', 'Mastercard', 'Visa', 'American Express'
]

GLOBAL_COLLEGES = [
    'Harvard University', 'Stanford University', 'Massachusetts Institute of Technology',
    'California Institute of Technology', 'University of Oxford', 'University of Cambridge',
    'ETH Zurich', 'University of California, Berkeley', 'Imperial College London',
    'University of Chicago', 'Princeton University', 'Cornell University', 'Yale University',
    'Columbia University', 'University of Michigan', 'University of Toronto', 'University of Tokyo',
    'Peking University', 'National University of Singapore', 'University of Melbourne',
    'University of Sydney', 'McGill University', 'University of British Columbia'
]

DEGREES = ['Bachelor of Engineering', 'Bachelor of Technology', 'Master of Technology', 
           'Master of Computer Applications', 'Bachelor of Computer Applications', 
           'Master of Science in Computer Science', 'PhD in Computer Science', 
           'Bachelor of Science in Information Technology']

RECRUITER_POSITIONS = ['HR Manager', 'Talent Acquisition Specialist', 'Recruitment Coordinator', 
                      'Senior Recruiter', 'HR Business Partner', 'Technical Recruiter', 
                      'HR Director', 'Staffing Coordinator', 'Hiring Manager']

JOB_TITLES = ['Software Engineer', 'Senior Software Engineer', 'Full Stack Developer', 
              'Frontend Developer', 'Backend Developer', 'DevOps Engineer', 'Data Scientist', 
              'Machine Learning Engineer', 'Cloud Architect', 'Systems Architect', 'Database Administrator', 'Network Engineer',
              'Product Manager', 'UI/UX Designer', 'QA Engineer', 'Test Automation Engineer',
              'Mobile Developer', 'Android Developer', 'iOS Developer', 'Site Reliability Engineer',
              'Security Engineer', 'Blockchain Developer', 'Game Developer', 'Technical Writer']

INDIAN_CITIES = ['Bangalore', 'Mumbai', 'Delhi', 'Hyderabad', 'Chennai', 'Pune', 
                'Kolkata', 'Ahmedabad', 'Gurgaon', 'Noida', 'Jaipur', 'Kochi', 
                'Indore', 'Coimbatore', 'Chandigarh', 'Trivandrum', 'Bhubaneswar']

GLOBAL_CITIES = ['San Francisco', 'New York', 'London', 'Berlin', 'Toronto', 'Sydney',
                'Singapore', 'Tokyo', 'Paris', 'Amsterdam', 'Seattle', 'Austin',
                'Boston', 'Chicago', 'Dublin', 'Zurich', 'Tel Aviv', 'Helsinki']

TECH_SKILLS = ['Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin',
              'TypeScript', 'Go', 'Rust', 'Scala', 'R', 'Dart', 'HTML', 'CSS', 'SQL',
              'Node.js', 'React', 'Angular', 'Vue.js', 'Django', 'Flask', 'Spring Boot',
              'ASP.NET', 'Ruby on Rails', '.NET Core', 'Express.js', 'Laravel',
              'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'NumPy', 'Docker',
              'Kubernetes', 'AWS', 'Azure', 'GCP', 'Git', 'Jenkins', 'GraphQL',
              'Redux', 'RESTful API', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis', 'Elasticsearch']

JOB_BENEFITS = ['Health insurance', 'Dental insurance', 'Vision insurance', 'Life insurance',
               'Retirement plan', 'Paid time off', 'Flexible work hours', 'Remote work options',
               'Professional development budget', 'Gym membership', 'Free meals', 'Transportation benefits',
               'Parental leave', 'Tuition reimbursement', 'Employee stock options', 'Performance bonuses',
               'Wellness programs', 'Company events', 'Childcare assistance', 'Mental health resources']

# Utility functions
def generate_password():
    """Generate a random password."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))

def create_skills():
    """Create skills in the database."""
    print("Creating skills...")
    db.session.query(Skill).delete()
    
    for skill_name in tqdm(TECH_SKILLS):
        skill = Skill(name=skill_name)
        db.session.add(skill)
    
    db.session.commit()
    return Skill.query.all()

def create_recruiter_accounts(count, is_indian=True):
    """Create recruiter accounts."""
    print(f"Creating {count} recruiter accounts...")
    
    if is_indian:
        faker = Faker(['en_IN'])
        companies = INDIAN_COMPANIES
        cities = INDIAN_CITIES
    else:
        faker = Faker()
        companies = GLOBAL_COMPANIES
        cities = GLOBAL_CITIES
    
    recruiters = []
    for _ in tqdm(range(count)):
        name = faker.name()
        email = f"{name.lower().replace(' ', '.')}@{faker.domain_name()}"
        
        recruiter = User(
            name=name,
            email=email,
            user_type='recruiter',
            company=random.choice(companies),
            position=random.choice(RECRUITER_POSITIONS),
            created_at=faker.date_time_between(start_date='-90d', end_date='now'),
            profile_completed=True
        )
        recruiter.set_password(generate_password())
        db.session.add(recruiter)
        recruiters.append(recruiter)
    
    db.session.commit()
    return recruiters

def create_applicant_accounts(count, skills, is_indian=True):
    """Create applicant accounts."""
    print(f"Creating {count} applicant accounts...")
    
    if is_indian:
        faker = Faker(['en_IN'])
        colleges = INDIAN_COLLEGES
        cities = INDIAN_CITIES
    else:
        faker = Faker()
        colleges = GLOBAL_COLLEGES
        cities = GLOBAL_CITIES
    
    applicants = []
    for _ in tqdm(range(count)):
        name = faker.name()
        email = f"{name.lower().replace(' ', '.')}@{faker.domain_name()}"
        
        experience_years = random.randint(0, 15)
        education = random.choice(DEGREES)
        college = random.choice(colleges)
        
        applicant = User(
            name=name,
            email=email,
            user_type='applicant',
            experience=experience_years,
            education=f"{education}, {college}",
            created_at=faker.date_time_between(start_date='-90d', end_date='now'),
            profile_completed=True,
            resume=faker.text(max_nb_chars=2000) if random.random() > 0.2 else None
        )
        applicant.set_password(generate_password())
        
        # Add random skills (between 3 and 8)
        num_skills = random.randint(3, min(8, len(skills)))
        selected_skills = random.sample(skills, num_skills)
        applicant.skills.extend(selected_skills)
        
        db.session.add(applicant)
        applicants.append(applicant)
    
    db.session.commit()
    return applicants

def create_job_postings(count, recruiters, skills, is_indian=True):
    """Create job postings."""
    print(f"Creating {count} job postings...")
    
    if is_indian:
        faker = Faker(['en_IN'])
        cities = INDIAN_CITIES
    else:
        faker = Faker()
        cities = GLOBAL_CITIES
    
    jobs = []
    for _ in tqdm(range(count)):
        recruiter = random.choice(recruiters)
        title = random.choice(JOB_TITLES)
        
        # Random date within the last 30 days
        post_date = faker.date_time_between(start_date='-30d', end_date='now')
        
        # Random requirement of 0-10 years experience
        experience_required = random.randint(0, 10)
        
        # Random salary range with higher ranges for more experience
        min_salary = 400000 + (experience_required * 100000) + random.randint(0, 200000)
        max_salary = min_salary + random.randint(200000, 800000)
        
        job = Job(
            title=title,
            location=random.choice(cities),
            description=bullet_points(faker),
            salary=f"₹{min_salary//100000} - ₹{max_salary//100000} LPA",
            experience_required=experience_required,
            recruiter_id=recruiter.id,
            created_at=post_date,
            is_active=True
        )
        
        # Add random skills (between 3 and 6)
        num_skills = random.randint(3, min(6, len(skills)))
        selected_skills = random.sample(skills, num_skills)
        job.skills.extend(selected_skills)
        
        db.session.add(job)
        jobs.append(job)
    
    db.session.commit()
    return jobs

def bullet_points(faker):
    """Generate bullet points for job descriptions or requirements."""
    num_points = random.randint(4, 8)
    return '\n'.join([f"• {faker.sentence()}" for _ in range(num_points)])

def create_applications(applicants, jobs):
    """Create job applications."""
    print("Creating job applications...")
    
    # Each applicant applies to 3-10 jobs
    for applicant in tqdm(applicants):
        num_applications = random.randint(3, min(10, len(jobs)))
        selected_jobs = random.sample(jobs, num_applications)
        
        for job in selected_jobs:
            # Check if applicant has at least one matching skill with the job
            applicant_skill_ids = [skill.id for skill in applicant.skills]
            job_skill_ids = [skill.id for skill in job.skills]
            
            if not set(applicant_skill_ids).intersection(set(job_skill_ids)):
                continue
            
            # Random application date between job posting date and now
            application_date = fake.date_time_between(
                start_date=job.created_at,
                end_date=min(job.created_at + timedelta(days=30), datetime.utcnow())
            )
            
            # Random status weighted towards 'pending'
            status = random.choices(
                ['pending', 'reviewed', 'interviewed', 'offered', 'rejected', 'accepted', 'withdrawn'],
                weights=[0.5, 0.2, 0.1, 0.05, 0.1, 0.03, 0.02],
                k=1
            )[0]
            
            application = Application(
                job_id=job.id,
                applicant_id=applicant.id,
                created_at=application_date,
                status=status,
                cover_letter=fake.text() if random.random() > 0.3 else None,
                match_score=job.match_score(applicant)
            )
            
            db.session.add(application)
    
    db.session.commit()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate demo data for JobMatch application')
    parser.add_argument('--region', choices=['indian', 'global'], default='indian',
                      help='Region-specific data to generate (default: indian)')
    parser.add_argument('--recruiters', type=int, default=500,
                      help='Number of recruiter accounts to create (default: 500)')
    parser.add_argument('--applicants', type=int, default=1000,
                      help='Number of applicant accounts to create (default: 1000)')
    parser.add_argument('--jobs', type=int, default=800,
                      help='Number of job postings to create (default: 800)')
    return parser.parse_args()

def main():
    """Main function to generate data."""
    args = parse_arguments()
    is_indian = args.region == 'indian'
    
    # Set region-specific Faker
    global fake
    if is_indian:
        fake = Faker(['en_IN'])
        print("Generating Indian-specific demo data...")
    else:
        fake = Faker()
        print("Generating global demo data...")
    
    # Clear existing data
    print("Clearing existing data...")
    Application.query.delete()
    Job.query.delete()
    
    # Clear the user_skills association table
    db.session.execute(db.Table('user_skills', db.metadata).delete())
    db.session.execute(db.Table('job_skills', db.metadata).delete())
    
    User.query.delete()
    Skill.query.delete()
    db.session.commit()
    
    # Create new data
    all_skills = create_skills()
    recruiters = create_recruiter_accounts(args.recruiters, is_indian)
    applicants = create_applicant_accounts(args.applicants, all_skills, is_indian)
    jobs = create_job_postings(args.jobs, recruiters, all_skills, is_indian)
    create_applications(applicants, jobs)
    
    print(f"\nSuccessfully created:")
    print(f"- {len(all_skills)} skills")
    print(f"- {len(recruiters)} recruiter accounts")
    print(f"- {len(applicants)} applicant accounts")
    print(f"- {len(jobs)} job postings")
    print(f"- {Application.query.count()} job applications")
    
    if is_indian:
        print("\nIndian-specific demo data has been generated!")
    else:
        print("\nGlobal demo data has been generated!")

if __name__ == "__main__":
    main() 