import os
import sys
import random
import datetime
from faker import Faker
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.getcwd()))

# Import models
from app.models.models import db, User, Skill

# Initialize faker with Indian locale
fake = Faker(['en_IN'])

# Indian-specific data
INDIAN_DOMAINS = [
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'rediffmail.com',
    'ymail.com', 'tcs.com', 'infosys.com', 'wipro.com', 'hcl.com', 'cognizant.com'
]

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

STARTUP_COMPANIES = [
    'TechEvolve Solutions', 'DigiSmart Technologies', 'CloudNexus Innovations', 'CodeVerse Solutions',
    'DataMatrix Analytics', 'Fintech Pioneers', 'EdTech Brilliance', 'MedTech Innovations',
    'EcoSmart Solutions', 'AgriTech Ventures', 'RetailEdge Solutions', 'TravelTech Connect',
    'Foodie Tech', 'UrbanMobility Solutions', 'SpaceTech Innovations', 'CreativeTech Solutions',
    'SocialConnect Platforms', 'GamingVerse Studios', 'CyberShield Technologies', 'BlockchainFlow Solutions',
    'AIMatrix Innovations', 'ARVision Technologies', 'RoboticsEdge Solutions', 'IoTConnect Platforms',
    'Quantum Compute Solutions', 'VirtualReality Immersions', 'BigDataHub Analytics', 'CryptoSecure Technologies'
]

INDIAN_COLLEGES = [
    'Indian Institute of Technology, Bombay', 'Indian Institute of Technology, Delhi', 
    'Indian Institute of Technology, Kanpur', 'Indian Institute of Technology, Madras',
    'Indian Institute of Technology, Kharagpur', 'Indian Institute of Technology, Roorkee',
    'Indian Institute of Technology, Guwahati', 'Indian Institute of Science, Bangalore',
    'Birla Institute of Technology and Science, Pilani', 'National Institute of Technology, Trichy',
    'National Institute of Technology, Warangal', 'National Institute of Technology, Surathkal',
    'Delhi University', 'Mumbai University', 'Calcutta University', 'Jadavpur University',
    'Anna University', 'Osmania University', 'Punjab University', 'Bangalore University',
    'Amity University', 'Manipal University', 'VIT University', 'SRM University',
    'Symbiosis International University', 'KIIT University', 'Lovely Professional University',
    'Christ University', 'Chandigarh University', 'Aligarh Muslim University'
]

INDIAN_DEGREES = [
    'B.Tech', 'B.E.', 'B.Sc', 'B.Com', 'BBA', 'BCA', 'M.Tech', 'M.E.', 'MCA', 'MBA',
    'M.Sc', 'M.Com', 'Ph.D', 'Diploma'
]

INDIAN_CITIES = [
    'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad',
    'Jaipur', 'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam',
    'Patna', 'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik', 'Faridabad', 'Meerut',
    'Rajkot', 'Varanasi', 'Srinagar', 'Aurangabad', 'Dhanbad', 'Amritsar', 'Allahabad',
    'Ranchi', 'Coimbatore', 'Jabalpur', 'Gwalior', 'Vijayawada', 'Jodhpur', 'Madurai',
    'Raipur', 'Kota', 'Chandigarh', 'Guwahati', 'Solapur', 'Hubli', 'Dharwad', 'Mysore',
    'Noida', 'Gurgaon'
]

RECRUITER_TITLES = [
    'HR Manager', 'Talent Acquisition Specialist', 'Technical Recruiter', 'HR Executive',
    'Human Resources Director', 'Recruiting Manager', 'Talent Management Specialist',
    'HR Business Partner', 'Senior Recruiter', 'Staffing Coordinator', 'People Operations Manager',
    'Senior HR Executive', 'HR Generalist', 'HR Consultant', 'Talent Acquisition Lead',
    'Head of Talent Acquisition', 'Recruitment Specialist', 'Human Capital Manager',
    'VP of Human Resources', 'Technical Hiring Manager', 'Chief People Officer',
    'Recruitment Coordinator', 'HR Specialist', 'Hiring Manager'
]

TECH_SKILLS = [
    'Python', 'Java', 'JavaScript', 'C++', 'C#', 'PHP', 'Ruby', 'Swift', 'Go', 'Rust',
    'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring Boot', 'Express.js',
    'Laravel', 'Ruby on Rails', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'Google Cloud',
    'MongoDB', 'MySQL', 'PostgreSQL', 'Oracle', 'SQL Server', 'Redis', 'Cassandra',
    'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'NumPy', 'Hadoop', 'Spark',
    'Git', 'Jenkins', 'CI/CD', 'Selenium', 'Jest', 'Mocha', 'JUnit', 'Flutter',
    'React Native', 'Kotlin', 'SwiftUI', 'TypeScript', 'GraphQL', 'REST API', 'gRPC',
    'Linux', 'Unix', 'Bash', 'PowerShell', 'Excel VBA', 'Power BI', 'Tableau',
    'Data Analysis', 'Data Science', 'Machine Learning', 'Deep Learning', 'NLP',
    'Computer Vision', 'Big Data', 'IoT', 'Blockchain', 'DevOps', 'Agile', 'Scrum'
]

JOB_TITLES = [
    'Software Engineer', 'Data Scientist', 'Frontend Developer', 'Backend Developer',
    'Full Stack Developer', 'DevOps Engineer', 'Machine Learning Engineer', 'AI Specialist',
    'Cloud Architect', 'Database Administrator', 'Mobile App Developer', 'UI/UX Designer',
    'QA Engineer', 'Test Automation Engineer', 'Product Manager', 'Project Manager',
    'Cybersecurity Analyst', 'Network Engineer', 'System Administrator', 'Business Analyst',
    'Data Analyst', 'Blockchain Developer', 'Game Developer', 'AR/VR Developer',
    'Technical Support Engineer', 'IT Manager', 'CTO', 'CIO', 'Technical Writer',
    'Embedded Systems Engineer', 'IoT Developer', 'Robotics Engineer'
]

def random_indian_name():
    """Generate a realistic Indian name."""
    gender = random.choice(['male', 'female'])
    
    if gender == 'male':
        first_names = [
            'Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun', 'Reyansh', 'Ayaan', 'Atharva',
            'Ishaan', 'Shaurya', 'Advait', 'Rudra', 'Krishna', 'Kabir', 'Aryan', 'Dhruv',
            'Pranav', 'Yash', 'Arnav', 'Aayan', 'Rajveer', 'Krish', 'Abhiram', 'Rayan',
            'Siddharth', 'Virat', 'Rohan', 'Parth', 'Vikram', 'Sahil', 'Nikhil', 'Rahul',
            'Varun', 'Dev', 'Anish', 'Aryan', 'Karan', 'Lakshay', 'Abhay', 'Veer'
        ]
        
        last_names = [
            'Sharma', 'Singh', 'Kumar', 'Patel', 'Rao', 'Joshi', 'Malhotra', 'Gupta',
            'Kapur', 'Mehra', 'Reddy', 'Nair', 'Menon', 'Verma', 'Agarwal', 'Mishra',
            'Choudhary', 'Yadav', 'Iyer', 'Banerjee', 'Chakraborty', 'Mukherjee', 'Roy',
            'Das', 'Chatterjee', 'Bose', 'Sen', 'Desai', 'Shah', 'Mehta', 'Patil', 'Jain',
            'Bajaj', 'Mahajan', 'Khanna', 'Trivedi', 'Dubey', 'Bhatia', 'Sinha', 'Saxena'
        ]
    else:
        first_names = [
            'Aanya', 'Aadhya', 'Aaradhya', 'Saanvi', 'Ananya', 'Pari', 'Shreya', 'Diya',
            'Angel', 'Riya', 'Siya', 'Avni', 'Kiara', 'Myra', 'Sara', 'Ishita', 'Saisha',
            'Divya', 'Shanaya', 'Trisha', 'Navya', 'Kyra', 'Krisha', 'Ira', 'Kavya',
            'Khushi', 'Prisha', 'Riddhi', 'Nisha', 'Meera', 'Jhanvi', 'Tanvi', 'Neha',
            'Sneha', 'Pooja', 'Swati', 'Aishwarya', 'Anjali', 'Priya', 'Anushka'
        ]
        
        last_names = [
            'Sharma', 'Singh', 'Kumar', 'Patel', 'Rao', 'Joshi', 'Malhotra', 'Gupta',
            'Kapur', 'Mehra', 'Reddy', 'Nair', 'Menon', 'Verma', 'Agarwal', 'Mishra',
            'Choudhary', 'Yadav', 'Iyer', 'Banerjee', 'Chakraborty', 'Mukherjee', 'Roy',
            'Das', 'Chatterjee', 'Bose', 'Sen', 'Desai', 'Shah', 'Mehta', 'Patil', 'Jain',
            'Bajaj', 'Mahajan', 'Khanna', 'Trivedi', 'Dubey', 'Bhatia', 'Sinha', 'Saxena'
        ]
    
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def random_indian_email(name):
    """Generate an email based on an Indian name."""
    name_parts = name.lower().replace(' ', '.')
    
    # Various email formats
    formats = [
        f"{name_parts}@{random.choice(INDIAN_DOMAINS)}",
        f"{name_parts.split('.')[0]}{random.choice(['', '.', '_'])}{name_parts.split('.')[1][0]}@{random.choice(INDIAN_DOMAINS)}",
        f"{name_parts.split('.')[0]}{random.randint(1, 9999)}@{random.choice(INDIAN_DOMAINS)}",
        f"{name_parts.split('.')[0][0]}{name_parts.split('.')[1]}@{random.choice(INDIAN_DOMAINS)}"
    ]
    
    return random.choice(formats)

def random_education():
    """Generate a random Indian education background."""
    degree = random.choice(INDIAN_DEGREES)
    college = random.choice(INDIAN_COLLEGES)
    
    if degree in ['B.Tech', 'B.E.', 'M.Tech', 'M.E.']:
        field = random.choice([
            'Computer Science', 'Information Technology', 'Electronics', 
            'Electrical', 'Mechanical', 'Civil', 'Chemical', 'Biotechnology'
        ])
    elif degree in ['B.Sc', 'M.Sc']:
        field = random.choice([
            'Computer Science', 'Mathematics', 'Physics', 'Chemistry', 
            'Statistics', 'Economics', 'Biology', 'Biotechnology'
        ])
    elif degree in ['BCA', 'MCA']:
        field = 'Computer Applications'
    elif degree in ['BBA', 'MBA']:
        field = random.choice([
            'Finance', 'Marketing', 'HR', 'Operations', 
            'International Business', 'IT Management'
        ])
    else:
        field = random.choice([
            'Finance', 'Marketing', 'Computer Science', 'Accounting',
            'Economics', 'Business Administration'
        ])
    
    return f"{degree} in {field}, {college}"

def generate_random_resume(name, skills, education, experience_years, job_title):
    """Generate a realistic resume for a job seeker."""
    resume = f"""
RESUME: {name}
----------------------------------------------
Contact: {random_indian_email(name)}
Location: {random.choice(INDIAN_CITIES)}, India

PROFESSIONAL SUMMARY
----------------------------------------------
Experienced {job_title} with {experience_years} years of expertise in {", ".join(random.sample(skills, min(3, len(skills))))}. Passionate about {random.choice(["developing scalable applications", "solving complex problems", "creating intuitive user experiences", "optimizing system performance", "building robust infrastructure", "designing innovative solutions"])}.

EDUCATION
----------------------------------------------
{education}

SKILLS
----------------------------------------------
{", ".join(skills)}

EXPERIENCE
----------------------------------------------
"""
    
    # Generate work experience
    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month
    
    # Distribute experience across jobs
    remaining_experience = experience_years
    num_jobs = min(random.randint(1, 3), experience_years)
    
    for i in range(num_jobs):
        company = random.choice(INDIAN_COMPANIES + STARTUP_COMPANIES)
        job_duration = min(remaining_experience, random.randint(1, 4))
        remaining_experience -= job_duration
        
        end_year = current_year - (0 if i == 0 and random.random() > 0.2 else sum(range(i + 1)))
        end_month = current_month if end_year == current_year else random.randint(1, 12)
        
        start_year = end_year - job_duration
        start_month = random.randint(1, 12)
        
        if start_year == end_year:
            start_month = min(start_month, end_month - 1)
        
        job_title_text = job_title if i == 0 else random.choice(JOB_TITLES)
        
        resume += f"""
{company}, {random.choice(INDIAN_CITIES)}, India
{job_title_text}
{start_month}/{start_year} - {"Present" if i == 0 and end_year == current_year else f"{end_month}/{end_year}"}

• {random.choice(["Developed", "Designed", "Implemented", "Created", "Built", "Architected"])} {random.choice(["web applications", "mobile solutions", "backend services", "database systems", "cloud infrastructure", "enterprise software"])} using {", ".join(random.sample(skills, min(2, len(skills))))}
• {random.choice(["Led", "Managed", "Coordinated", "Supervised", "Directed"])} a team of {random.randint(2, 10)} {random.choice(["developers", "engineers", "programmers", "technical staff", "professionals"])}
• {random.choice(["Reduced", "Optimized", "Improved", "Enhanced", "Accelerated"])} {random.choice(["system performance", "application speed", "process efficiency", "user experience", "code quality"])} by {random.randint(15, 50)}%
"""
    
    return resume

def create_database_connection():
    """Create a database connection."""
    # Assuming SQLite database is used
    database_uri = 'sqlite:///instance/jobmatch.db'
    engine = create_engine(database_uri)
    Session = sessionmaker(bind=engine)
    return Session(), engine

def initialize_skills(session):
    """Initialize skills in the database."""
    print("Initializing skills...")
    existing_skills = {skill.name: skill for skill in session.query(Skill).all()}
    
    for skill_name in TECH_SKILLS:
        if skill_name not in existing_skills:
            new_skill = Skill(name=skill_name)
            session.add(new_skill)
    
    session.commit()
    
    # Return updated skills
    return {skill.name: skill for skill in session.query(Skill).all()}

def generate_recruiter_data(num_recruiters, skills_dict, session):
    """Generate recruiter data and insert into database."""
    print(f"\nGenerating {num_recruiters} recruiters...")
    
    for _ in tqdm(range(num_recruiters)):
        # Generate basic recruiter data
        name = random_indian_name()
        email = random_indian_email(name)
        company = random.choice(INDIAN_COMPANIES + STARTUP_COMPANIES)
        position = random.choice(RECRUITER_TITLES)
        
        # Create recruiter
        recruiter = User(
            name=name,
            email=email,
            password_hash=generate_password_hash("Password@123"),
            user_type="recruiter",
            company=company,
            position=position,
            created_at=fake.date_time_between(start_date='-3y', end_date='now'),
            updated_at=fake.date_time_between(start_date='-1y', end_date='now')
        )
        
        # Add random skills (recruiters typically need fewer skills)
        recruiter_skills = random.sample(list(skills_dict.values()), random.randint(3, 10))
        recruiter.skills.extend(recruiter_skills)
        
        session.add(recruiter)
    
    # Commit after batch insertion for performance
    session.commit()
    print("Recruiters generated successfully.")

def generate_jobseeker_data(num_jobseekers, skills_dict, session):
    """Generate job seeker data and insert into database."""
    print(f"\nGenerating {num_jobseekers} job seekers...")
    
    for _ in tqdm(range(num_jobseekers)):
        # Generate basic job seeker data
        name = random_indian_name()
        email = random_indian_email(name)
        experience = random.randint(0, 15)
        education = random_education()
        
        # Choose a random set of skills
        num_skills = random.randint(5, 20)
        user_skills = random.sample(list(skills_dict.values()), num_skills)
        
        # Choose a random job title
        job_title = random.choice(JOB_TITLES)
        
        # Generate resume
        skill_names = [skill.name for skill in user_skills]
        resume = generate_random_resume(name, skill_names, education, experience, job_title)
        
        # Create job seeker
        jobseeker = User(
            name=name,
            email=email,
            password_hash=generate_password_hash("Password@123"),
            user_type="applicant",
            resume=resume,
            experience=experience,
            education=education,
            created_at=fake.date_time_between(start_date='-3y', end_date='now'),
            updated_at=fake.date_time_between(start_date='-1y', end_date='now')
        )
        
        # Add skills
        jobseeker.skills.extend(user_skills)
        
        session.add(jobseeker)
    
    # Commit after batch insertion for performance
    session.commit()
    print("Job seekers generated successfully.")

def main():
    """Main function to generate data."""
    print("Starting data generation...")
    
    # Connect to database
    session, engine = create_database_connection()
    
    try:
        # Initialize skills
        skills_dict = initialize_skills(session)
        
        # Generate recruiters
        generate_recruiter_data(500, skills_dict, session)
        
        # Generate job seekers
        generate_jobseeker_data(1000, skills_dict, session)
        
        print("\nData generation completed successfully!")
    except Exception as e:
        print(f"Error during data generation: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main() 