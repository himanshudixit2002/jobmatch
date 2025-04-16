import os
import sys
import random
import string
import uuid
import argparse
from datetime import datetime, timedelta
from faker import Faker
from werkzeug.security import generate_password_hash
from tqdm import tqdm
import google.generativeai as genai
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.getcwd()))

# Import models
from app import create_app
from app.models.models import db, User, Skill, Job, Application

# Load environment variables
load_dotenv()

# Get Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in environment variables")
    print("Please create a .env file with your Gemini API key: GEMINI_API_KEY=your_api_key_here")
    sys.exit(1)

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Create Flask app context
app = create_app()
app_context = app.app_context()
app_context.push()

# Initialize faker with Indian locale
fake = Faker(['en_IN'])

# Track used emails to avoid duplicates
used_emails = set()

# Constants for Indian-specific data
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

INDIAN_NAMES_MALE = [
    'Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun', 'Reyansh', 'Ayaan', 'Atharva', 'Krishna', 'Ishaan',
    'Shaurya', 'Advik', 'Rudra', 'Pranav', 'Advaith', 'Kabir', 'Dhruv', 'Yuvaan', 'Virat', 'Amit',
    'Rajesh', 'Vikram', 'Suresh', 'Rohit', 'Nikhil', 'Anil', 'Vijay', 'Ajay', 'Rahul', 'Sagar',
    'Kunal', 'Gaurav', 'Karan', 'Sanjay', 'Varun', 'Naveen', 'Vishal', 'Deepak', 'Vinay', 'Ashish',
    'Siddharth', 'Rohan', 'Sahil', 'Arnav', 'Dev', 'Jayant', 'Tejas', 'Anand', 'Akshay', 'Mihir'
]

INDIAN_NAMES_FEMALE = [
    'Aadhya', 'Saanvi', 'Aaradhya', 'Ananya', 'Pari', 'Aanya', 'Myra', 'Siya', 'Ahana', 'Avni',
    'Diya', 'Kavya', 'Anvi', 'Sara', 'Divya', 'Mahira', 'Misha', 'Riddhima', 'Ishita', 'Ira',
    'Priya', 'Neha', 'Shreya', 'Anjali', 'Pooja', 'Meera', 'Tanvi', 'Sneha', 'Riya', 'Swati',
    'Kavita', 'Aishwarya', 'Deepika', 'Isha', 'Ritika', 'Jaya', 'Tanuja', 'Nisha', 'Sonam', 'Ruchi',
    'Shivani', 'Mansi', 'Kirti', 'Pallavi', 'Tanu', 'Aruna', 'Megha', 'Jyoti', 'Kanika', 'Ambika'
]

INDIAN_LAST_NAMES = [
    'Sharma', 'Patel', 'Singh', 'Verma', 'Gupta', 'Joshi', 'Kumar', 'Rao', 'Naidu', 'Shah',
    'Reddy', 'Nair', 'Agarwal', 'Mehta', 'Chauhan', 'Kaur', 'Chowdhury', 'Das', 'Jain', 'Bose',
    'Chatterjee', 'Kapoor', 'Khanna', 'Iyer', 'Banerjee', 'Arora', 'Malhotra', 'Roy', 'Sengupta', 'Desai',
    'Bhat', 'Pillai', 'Mukherjee', 'Menon', 'Mishra', 'Trivedi', 'Dubey', 'Gowda', 'Thakur', 'Yadav',
    'Srivastava', 'Tiwari', 'Murthy', 'Patil', 'Gandhi', 'Lal', 'Shetty', 'Rana', 'Goswami', 'Varma'
]

INDIAN_STARTUPS = [
    'Zepto', 'Razorpay', 'CRED', 'PhonePe', 'Groww', 'Meesho', 'Ola Electric', 'Swiggy', 'Zomato', 'Dream11',
    'UpGrad', 'BharatPe', 'Unacademy', 'Byju\'s', 'Urban Company', 'Lenskart', 'CoinDCX', 'CoinSwitch Kuber', 'ShareChat', 'Delhivery',
    'CarDekho', 'BillDesk', 'Ather Energy', 'Zeta', 'Dunzo', 'boAt', 'EaseMyTrip', 'Cars24', 'Pine Labs', 'DailyHunt',
    'Curefit', 'Vedantu', 'Nykaa', 'Paytm', 'OYO Rooms', 'Snapdeal', 'Policybazaar', 'BigBasket', 'FirstCry', 'MamaEarth',
    'Pharmeasy', 'BlackBuck', 'MPL', 'Moglix', 'InMobi', 'Zoho', 'Freshworks', 'Postman', 'Icertis', 'Druva'
]

INDIAN_COLLEGES = [
    'Indian Institute of Technology (IIT) Bombay', 'Indian Institute of Technology (IIT) Delhi', 'Indian Institute of Technology (IIT) Kanpur', 
    'Indian Institute of Technology (IIT) Madras', 'Indian Institute of Technology (IIT) Kharagpur', 'Indian Institute of Technology (IIT) Roorkee',
    'Indian Institute of Science (IISc) Bangalore', 'National Institute of Technology (NIT) Tiruchirappalli', 'National Institute of Technology (NIT) Warangal',
    'National Institute of Technology (NIT) Surathkal', 'Birla Institute of Technology and Science (BITS) Pilani', 'Delhi Technological University (DTU)',
    'Vellore Institute of Technology (VIT)', 'Manipal Institute of Technology', 'SRM Institute of Science and Technology', 'College of Engineering, Pune (COEP)',
    'PSG College of Technology', 'Jadavpur University', 'Indian Statistical Institute (ISI) Kolkata', 'Anna University Chennai',
    'University of Delhi', 'Jamia Millia Islamia', 'Banaras Hindu University (BHU)', 'Aligarh Muslim University (AMU)',
    'Mumbai University', 'Savitribai Phule Pune University', 'Punjab Engineering College (PEC)', 'The LNM Institute of Information Technology',
    'International Institute of Information Technology (IIIT) Hyderabad', 'International Institute of Information Technology (IIIT) Bangalore'
]

DEGREES = [
    'B.Tech Computer Science', 'B.Tech Electronics', 'B.Tech Electrical', 'B.Tech Mechanical', 'B.Tech Civil',
    'B.Tech Information Technology', 'B.Tech Chemical Engineering', 'B.Sc Computer Science', 'B.Sc Information Technology',
    'B.Sc Mathematics', 'B.Sc Physics', 'B.Sc Electronics', 'BCA', 'BBA', 'B.Com',
    'M.Tech Computer Science', 'M.Tech Electronics', 'M.Tech Electrical', 'M.Tech Information Technology',
    'M.Sc Computer Science', 'M.Sc Information Technology', 'M.Sc Mathematics', 'M.Sc Physics', 'MCA', 'MBA',
    'PhD Computer Science', 'PhD Electronics', 'PhD Data Science', 'PhD Artificial Intelligence'
]

RECRUITER_POSITIONS = [
    'HR Manager', 'Talent Acquisition Specialist', 'HR Director', 'Recruitment Coordinator',
    'Technical Recruiter', 'Senior Recruiter', 'HR Business Partner', 'Recruitment Manager',
    'HR Executive', 'Talent Acquisition Manager', 'HR Specialist', 'Human Resources Lead',
    'Talent Scout', 'People Operations Manager', 'Recruitment Lead', 'HR Generalist',
    'Talent Acquisition Lead', 'Senior HR Manager', 'Chief Human Resources Officer (CHRO)',
    'VP of Human Resources', 'Director of Talent Acquisition', 'Head of Recruitment'
]

JOB_TITLES = [
    'Software Engineer', 'Senior Software Engineer', 'Full Stack Developer', 'Frontend Developer', 
    'Backend Developer', 'Mobile App Developer', 'DevOps Engineer', 'Data Scientist', 
    'Machine Learning Engineer', 'AI Engineer', 'Data Engineer', 'Cloud Engineer', 
    'System Architect', 'Technical Lead', 'Engineering Manager', 'QA Engineer', 
    'Test Automation Engineer', 'UI/UX Designer', 'Product Manager', 'Project Manager', 
    'Blockchain Developer', 'Security Engineer', 'Network Engineer', 'Database Administrator', 
    'Business Analyst', 'Technical Support Engineer', 'SRE Engineer', 'Game Developer',
    'AR/VR Developer', 'IoT Developer', 'Embedded Systems Engineer', 'Technical Writer'
]

INDIAN_CITIES = [
    'Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad', 
    'Jaipur', 'Lucknow', 'Noida', 'Gurgaon', 'Chandigarh', 'Kochi', 'Coimbatore', 'Indore', 
    'Nagpur', 'Bhubaneswar', 'Visakhapatnam', 'Thiruvananthapuram', 'Vadodara', 'Surat'
]

TECH_SKILLS = [
    'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Ruby', 'Swift', 'Kotlin', 'TypeScript',
    'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring Boot', 'Express.js', 'Laravel',
    'TensorFlow', 'PyTorch', 'Keras', 'Pandas', 'NumPy', 'Scikit-learn', 'NLTK', 'OpenCV',
    'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'Terraform', 'Jenkins', 'CircleCI',
    'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'ElasticSearch', 'Cassandra', 'DynamoDB',
    'Git', 'Jira', 'Agile', 'Scrum', 'DevOps', 'CI/CD', 'REST API', 'GraphQL', 'gRPC',
    'React Native', 'Flutter', 'Android', 'iOS', 'Selenium', 'JUnit', 'Jest', 'Cypress',
    'Linux', 'Bash', 'PowerShell', 'Nginx', 'Apache', 'Blockchain', 'Smart Contracts', 'Hadoop',
    'Spark', 'Kafka', 'RabbitMQ', 'Microservices', 'Serverless', 'WebSockets', 'PWA'
]

JOB_BENEFITS = [
    'Health Insurance', 'Life Insurance', 'Dental Insurance', 'Vision Insurance',
    'Retirement Plan', 'Flexible Work Hours', 'Remote Work Options', 'Paid Time Off',
    'Parental Leave', 'Professional Development', 'Tuition Reimbursement', 'Gym Membership',
    'Wellness Programs', 'Mental Health Support', 'Stock Options', 'Performance Bonuses',
    'Referral Bonuses', 'Relocation Assistance', 'Company Retreats', 'Team Outings',
    'Free Meals', 'Snacks and Beverages', 'Game Room', 'Child Care Benefits',
    'Transportation Allowance', 'Internet Allowance', 'Cell Phone Allowance', 'Home Office Stipend'
]

# Utility functions
def generate_indian_name():
    """Generate a realistic Indian name with gender balance."""
    gender = random.choice(['male', 'female'])
    
    if gender == 'male':
        first_name = random.choice(INDIAN_NAMES_MALE)
    else:
        first_name = random.choice(INDIAN_NAMES_FEMALE)
        
    last_name = random.choice(INDIAN_LAST_NAMES)
    
    return f"{first_name} {last_name}", gender

def bullet_points(items):
    """Convert a list of items into bullet points."""
    return "\n".join([f"• {item}" for item in items])

def generate_password():
    """Generate a random password."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))

def generate_unique_email(name):
    """Generate a unique email based on an Indian name."""
    global used_emails
    
    # Try a few times with simple formats
    for _ in range(3):
        name_parts = name.lower().replace(' ', '.')
        domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'rediffmail.com']
        
        email_formats = [
            f"{name_parts}@{random.choice(domains)}",
            f"{name_parts.split('.')[0]}@{random.choice(domains)}",
            f"{name_parts.split('.')[0]}.{name_parts.split('.')[1][0]}@{random.choice(domains)}",
            f"{name_parts.split('.')[0]}{random.randint(1, 9999)}@{random.choice(domains)}"
        ]
        
        email = random.choice(email_formats)
        if email not in used_emails:
            used_emails.add(email)
            return email
    
    # If we couldn't generate a unique email with the formats above, add a UUID
    name_part = name.lower().replace(' ', '.').split('.')[0]
    domain = random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'rediffmail.com'])
    unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars of a UUID for uniqueness
    
    email = f"{name_part}.{unique_id}@{domain}"
    used_emails.add(email)
    return email

def generate_resume_with_gemini(name, skills, education, experience_years, job_title, city):
    """Generate a realistic resume using Gemini API."""
    try:
        # Configure the model
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Create the prompt
        prompt = f"""
        Create a professional and realistic resume for a tech professional in India with the following details:
        
        Name: {name}
        Current Job Title: {job_title}
        Years of Experience: {experience_years}
        Education: {education}
        Location: {city}, India
        Technical Skills: {', '.join(skills)}
        
        Format the resume with the following sections:
        1. Professional Summary (brief and impactful)
        2. Skills (technical and soft skills)
        3. Work Experience (with 2-3 relevant past positions at Indian companies)
        4. Education
        5. Certifications (if applicable)
        
        Make it specific to the Indian job market and tech industry. Keep it concise but comprehensive.
        """
        
        # Generate the resume
        response = model.generate_content(prompt)
        
        # Extract and return the resume text
        resume = response.text
        return resume
    
    except Exception as e:
        print(f"Error generating resume with Gemini API: {str(e)}")
        
        # Fallback to a basic resume template if Gemini fails
        return f"""
# RESUME: {name}
Location: {city}, India

## PROFESSIONAL SUMMARY
{job_title} with {experience_years} years of experience specializing in {', '.join(random.sample(skills, min(3, len(skills))))}.

## SKILLS
{', '.join(skills)}

## EDUCATION
{education}

## WORK EXPERIENCE
{random.choice(INDIAN_COMPANIES + INDIAN_STARTUPS)}
{job_title}
{datetime.now().year - experience_years} - Present

{random.choice(INDIAN_COMPANIES + INDIAN_STARTUPS)}
{random.choice(JOB_TITLES)}
{datetime.now().year - experience_years - 2} - {datetime.now().year - experience_years}
"""

def clear_existing_data():
    """Clear all existing user and job data from the database."""
    print("Clearing existing data...")
    
    # Delete all applications
    Application.query.delete()
    
    # Delete all jobs
    Job.query.delete()
    
    # Clear the association tables
    db.session.execute(db.Table('user_skills', db.metadata).delete())
    db.session.execute(db.Table('job_skills', db.metadata).delete())
    
    # Delete all users and skills
    User.query.delete()
    Skill.query.delete()
    
    # Commit the changes
    db.session.commit()
    print("All existing data cleared successfully.")

def create_skills():
    """Create skills in the database."""
    print("Creating skills...")
    
    for skill_name in tqdm(TECH_SKILLS):
        skill = Skill(name=skill_name)
        db.session.add(skill)
    
    db.session.commit()
    return Skill.query.all()

def create_recruiter_accounts(count):
    """Create recruiter accounts for Indian companies."""
    print(f"Creating {count} recruiter accounts...")
    
    recruiters = []
    for i in tqdm(range(count)):
        company = random.choice(INDIAN_COMPANIES + INDIAN_STARTUPS)
        position = random.choice(RECRUITER_POSITIONS)
        name = fake.name()
        email = f"recruiter_{i}@{company.lower().replace(' ', '')}.com"
        
        recruiter = User(
            name=name,
            email=email,
            user_type='recruiter',
            company=company,
            position=position,
            created_at=fake.date_time_between(start_date='-180d', end_date='now'),
            profile_completed=True
        )
        recruiter.set_password(generate_password())
        
        db.session.add(recruiter)
        recruiters.append(recruiter)
        
        # Commit in batches to avoid memory issues
        if (i + 1) % 100 == 0:
            db.session.commit()
            print(f"  - {i + 1} recruiter accounts created...")
    
    db.session.commit()
    return recruiters

def create_applicant_accounts(count, skills):
    """Create applicant accounts with AI-generated resumes."""
    print(f"Creating {count} applicant accounts...")
    
    applicants = []
    for i in tqdm(range(count)):
        name = fake.name()
        email = f"applicant_{i}@example.com"
        experience_years = random.randint(0, 15)
        
        # Random education
        college = random.choice(INDIAN_COLLEGES)
        degree = random.choice(DEGREES)
        education = f"{degree}, {college}"
        city = random.choice(INDIAN_CITIES)
        
        # Select random skills
        num_skills = random.randint(4, min(12, len(skills)))
        selected_skills = random.sample(skills, num_skills)
        selected_skill_names = [skill.name for skill in selected_skills]
        
        # Choose a job title appropriate for experience level
        if experience_years < 2:
            possible_titles = [title for title in JOB_TITLES if not (title.startswith('Senior') or 'Architect' in title or 'Lead' in title)]
        elif experience_years < 5:
            possible_titles = [title for title in JOB_TITLES if not ('Architect' in title)]
        else:
            possible_titles = JOB_TITLES
            
        job_title = random.choice(possible_titles)
        
        # Generate resume using Gemini API (or fallback to template)
        if i < 100:  # Only use Gemini API for the first 100 applicants to avoid rate limiting
            resume = generate_resume_with_gemini(
                name=name,
                skills=selected_skill_names,
                education=education,
                experience_years=experience_years,
                job_title=job_title,
                city=city
            )
        else:
            # Use template for the rest
            resume = generate_resume_template(
                name=name,
                skills=selected_skill_names,
                education=education,
                experience_years=experience_years,
                job_title=job_title,
                city=city
            )
        
        applicant = User(
            name=name,
            email=email,
            user_type='applicant',
            experience=experience_years,
            education=education,
            created_at=fake.date_time_between(start_date='-180d', end_date='now'),
            profile_completed=True,
            resume=resume
        )
        applicant.set_password(generate_password())
        
        # Add skills
        applicant.skills.extend(selected_skills)
        
        db.session.add(applicant)
        applicants.append(applicant)
        
        # Commit in batches to avoid memory issues
        if (i + 1) % 100 == 0:
            db.session.commit()
            print(f"  - {i + 1} applicant accounts created...")
    
    db.session.commit()
    return applicants

def generate_resume_template(name, skills, education, experience_years, job_title, city):
    """Generate a resume using a template."""
    companies = INDIAN_COMPANIES + INDIAN_STARTUPS
    
    # Generate work experience entries
    work_experience = ""
    current_year = datetime.now().year
    
    # Current job
    current_company = random.choice(companies)
    current_start_year = current_year - experience_years
    work_experience += f"""
### {current_company}
**{job_title}**  
*{current_start_year} - Present*

- {random.choice(["Developed", "Implemented", "Created", "Built", "Designed", "Architected"])} {random.choice(["scalable applications", "robust systems", "efficient solutions", "innovative features", "high-performance services"])} using {', '.join(random.sample(skills, min(3, len(skills))))}
- {random.choice(["Led", "Managed", "Coordinated", "Supervised", "Mentored"])} a team of {random.randint(2, 8)} {random.choice(["developers", "engineers", "professionals", "team members"])} to {random.choice(["deliver projects on time", "implement new features", "resolve complex issues", "improve system performance", "enhance user experience"])}
- {random.choice(["Collaborated", "Worked", "Partnered"])} with cross-functional teams to {random.choice(["define requirements", "design solutions", "implement new features", "resolve technical challenges", "improve development processes"])}
"""
    
    # Previous jobs (if experienced enough)
    if experience_years > 2:
        prev_company = random.choice([c for c in companies if c != current_company])
        prev_job = random.choice([t for t in JOB_TITLES if t != job_title])
        prev_end_year = current_start_year
        prev_start_year = prev_end_year - min(3, experience_years - 1)
        
        work_experience += f"""
### {prev_company}
**{prev_job}**  
*{prev_start_year} - {prev_end_year}*

- {random.choice(["Developed", "Implemented", "Maintained", "Enhanced", "Optimized"])} {random.choice(["applications", "systems", "solutions", "software", "platforms"])} using {', '.join(random.sample(skills, min(2, len(skills))))}
- {random.choice(["Improved", "Optimized", "Enhanced", "Accelerated", "Streamlined"])} {random.choice(["system performance", "application responsiveness", "code quality", "user experience", "developer workflow"])} by {random.randint(15, 40)}%
- {random.choice(["Resolved", "Fixed", "Addressed", "Troubleshot"])} complex technical issues to {random.choice(["ensure system stability", "improve user satisfaction", "maintain service quality", "reduce downtime", "enhance product reliability"])}
"""
    
    # Create complete resume
    return f"""
# {name}
*{job_title} with {experience_years} years of experience*  
{city}, India | {random.choice(["", "+91-", "+91 "])}{random.randint(7000000000, 9999999999)}

## PROFESSIONAL SUMMARY
{random.choice([
    f"Experienced {job_title} with {experience_years}+ years of expertise in {', '.join(random.sample(skills, min(3, len(skills))))}.",
    f"Dedicated {job_title} with a proven track record of {experience_years} years in developing {random.choice(['innovative', 'scalable', 'robust', 'efficient', 'cutting-edge'])} solutions.",
    f"Results-oriented {job_title} with {experience_years} years of experience specializing in {', '.join(random.sample(skills, min(2, len(skills))))} and {random.choice(['problem-solving', 'system design', 'software architecture', 'technical leadership', 'performance optimization'])}."
])} {random.choice([
    f"Passionate about {random.choice(['delivering high-quality code', 'solving complex problems', 'creating elegant solutions', 'optimizing performance', 'improving user experience'])}.",
    f"Skilled in {random.choice(['agile methodologies', 'team collaboration', 'technical communication', 'project management', 'continuous integration'])} and {random.choice(['test-driven development', 'clean code practices', 'mentoring junior developers', 'cross-functional collaboration', 'rapid prototyping'])}.",
    f"Committed to {random.choice(['staying current with emerging technologies', 'continuous learning', 'delivering business value', 'maintaining code quality', 'meeting project deadlines'])}."
])}

## SKILLS
**Technical Skills:** {', '.join(skills)}

**Soft Skills:** {', '.join(random.sample(['Team Collaboration', 'Communication', 'Problem Solving', 'Time Management', 'Leadership', 'Critical Thinking', 'Adaptability', 'Creativity', 'Attention to Detail'], 4))}

## WORK EXPERIENCE
{work_experience}

## EDUCATION
**{education}**  
*{current_year - random.randint(experience_years + 1, experience_years + 5)} - {current_year - experience_years}*

## CERTIFICATIONS
{random.choice([
    f"AWS Certified {random.choice(['Solutions Architect', 'Developer', 'SysOps Administrator', 'DevOps Engineer', 'Cloud Practitioner'])}",
    f"Microsoft Certified {random.choice(['Azure Developer', 'Azure Solutions Architect', 'DevOps Engineer', '.NET Developer', 'Data Scientist'])}",
    f"Google {random.choice(['Cloud Architect', 'Data Engineer', 'Professional Cloud Developer', 'Associate Cloud Engineer', 'Professional Machine Learning Engineer'])}",
    f"{random.choice(['Certified Kubernetes Administrator', 'Certified Jenkins Engineer', 'Docker Certified Associate', 'Certified Scrum Master', 'PMI Agile Certified Practitioner'])}",
    f"{random.choice(['Oracle Certified Professional', 'Cisco Certified Network Associate', 'CompTIA Security+', 'Certified Ethical Hacker', 'Salesforce Certified Developer'])}"
])}
"""

def create_job_postings(count, recruiters, skills):
    """Create job postings for Indian companies."""
    print(f"Creating {count} job postings...")
    
    jobs = []
    for _ in tqdm(range(count)):
        recruiter = random.choice(recruiters)
        title = random.choice(JOB_TITLES)
        city = random.choice(INDIAN_CITIES)
        
        # Random date within the last 30 days
        post_date = fake.date_time_between(start_date='-30d', end_date='now')
        
        # Experience required based on job title
        if 'Senior' in title or 'Architect' in title or 'Lead' in title:
            experience_required = random.randint(5, 12)
        elif 'Junior' in title or 'Associate' in title or 'Intern' in title:
            experience_required = random.randint(0, 2)
        else:
            experience_required = random.randint(2, 7)
        
        # Random salary range based on experience and job title
        base_salary = 400000  # 4 LPA base
        exp_factor = experience_required * 100000  # 1 LPA per year of experience
        title_factor = 0
        
        if 'Senior' in title or 'Architect' in title:
            title_factor = 500000  # Additional 5 LPA for senior roles
        elif 'Manager' in title or 'Lead' in title:
            title_factor = 300000  # Additional 3 LPA for management roles
            
        min_salary = base_salary + exp_factor + title_factor + random.randint(0, 200000)
        max_salary = min_salary + random.randint(200000, 800000)
        
        # Generate job description using bullet points
        description = f"""
# {title} at {recruiter.company}

## About the Role
We are looking for a {title} to join our team in {city}. The ideal candidate will have {experience_required}+ years of experience.

## Responsibilities
• Design, develop and maintain software applications and systems
• Write clean, efficient, and well-documented code
• Collaborate with cross-functional teams to define and implement solutions
• Troubleshoot and debug applications
• Participate in code reviews and ensure code quality
• Stay up-to-date with emerging trends and technologies

## Requirements
• {experience_required}+ years of experience in software development
• Proficiency in {', '.join(random.sample(TECH_SKILLS, 3))}
• Strong problem-solving abilities and attention to detail
• Excellent communication and teamwork skills
• {random.choice(['Bachelor\'s', 'Master\'s'])} degree in Computer Science or related field

## Benefits
• Competitive salary: ₹{min_salary//100000}-{max_salary//100000} LPA
• Health insurance for you and your family
• Flexible work arrangements
• Professional development opportunities
• {random.randint(15, 25)} days of paid time off
"""
        
        job = Job(
            title=title,
            location=city,
            description=description,
            salary=f"₹{min_salary//100000} - ₹{max_salary//100000} LPA",
            experience_required=experience_required,
            recruiter_id=recruiter.id,
            created_at=post_date,
            is_active=True
        )
        
        # Add random skills
        num_skills = random.randint(3, min(8, len(skills)))
        selected_skills = random.sample(skills, num_skills)
        job.skills.extend(selected_skills)
        
        db.session.add(job)
        jobs.append(job)
    
    db.session.commit()
    return jobs

def create_applications(applicants, jobs):
    """Create job applications with skill matching."""
    print("Creating job applications...")
    
    applications_count = 0
    
    # Each applicant applies to 2-8 jobs
    for applicant in tqdm(applicants):
        # Filter for jobs matching at least one of the applicant's skills
        applicant_skill_ids = {skill.id for skill in applicant.skills}
        matching_jobs = []
        
        for job in jobs:
            job_skill_ids = {skill.id for skill in job.skills}
            if applicant_skill_ids.intersection(job_skill_ids) and job.is_active:
                matching_jobs.append(job)
        
        # If no matching jobs, continue to next applicant
        if not matching_jobs:
            continue
            
        # Apply to 2-8 matching jobs
        num_applications = min(len(matching_jobs), random.randint(2, 8))
        selected_jobs = random.sample(matching_jobs, num_applications)
        
        for job in selected_jobs:
            # Calculate match score
            match_score = job.match_score(applicant)
            
            # Random application date between job posting date and now
            application_date = fake.date_time_between(
                start_date=job.created_at,
                end_date=min(job.created_at + timedelta(days=30), datetime.utcnow())
            )
            
            # Status weighted toward 'pending' but influenced by match score
            if match_score > 85:
                status_weights = [0.3, 0.3, 0.2, 0.1, 0.05, 0.03, 0.02]  # Better chance of progress
            elif match_score > 70:
                status_weights = [0.4, 0.25, 0.15, 0.08, 0.07, 0.03, 0.02]
            else:
                status_weights = [0.5, 0.2, 0.1, 0.05, 0.1, 0.03, 0.02]  # Default
                
            status = random.choices(
                ['pending', 'reviewed', 'interviewed', 'offered', 'rejected', 'accepted', 'withdrawn'],
                weights=status_weights,
                k=1
            )[0]
            
            # Generate a cover letter if it's not withdrawn
            cover_letter = None
            if status != 'withdrawn' and random.random() > 0.3:
                cover_letter = f"""
Dear Hiring Manager,

I am writing to express my interest in the {job.title} position at {job.recruiter.company}. With {applicant.experience} years of experience in the field, I believe I would be a valuable addition to your team.

{random.choice([
    "My background in software development has equipped me with the skills necessary to excel in this role.",
    "I am particularly excited about the opportunity to work with your team on innovative projects.",
    "I have been following your company's growth and am impressed by your commitment to excellence.",
    "My expertise in " + ", ".join(random.sample([skill.name for skill in applicant.skills], min(3, len(applicant.skills)))) + " aligns well with your requirements."
])}

{random.choice([
    "I am confident that my skills and experience make me a strong candidate for this position.",
    "I am eager to bring my technical expertise and collaborative approach to your team.",
    "I look forward to the opportunity to discuss how my background, skills and experience would benefit your organization.",
    "I am excited about the possibility of contributing to your team and growing professionally with your company."
])}

Thank you for considering my application.

Sincerely,
{applicant.name}
"""
            
            application = Application(
                job_id=job.id,
                applicant_id=applicant.id,
                created_at=application_date,
                status=status,
                cover_letter=cover_letter,
                match_score=match_score
            )
            
            db.session.add(application)
            applications_count += 1
            
        # Commit in batches
        if applications_count % 100 == 0:
            db.session.commit()
    
    db.session.commit()
    return applications_count

def main():
    """Main function to generate Indian-specific data."""
    parser = argparse.ArgumentParser(description='Generate Indian-specific data for JobMatch application')
    parser.add_argument('--recruiters', type=int, default=200, help='Number of recruiter accounts to create (default: 200)')
    parser.add_argument('--applicants', type=int, default=500, help='Number of applicant accounts to create (default: 500)')
    parser.add_argument('--jobs', type=int, default=300, help='Number of job postings to create (default: 300)')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for database commits (default: 100)')
    args = parser.parse_args()
    
    print("\n--- Generating Indian-specific Data with AI-generated Resumes ---\n")
    
    try:
        # Clear existing data
        clear_existing_data()
        
        # Create new data
        all_skills = create_skills()
        recruiters = create_recruiter_accounts(args.recruiters)
        applicants = create_applicant_accounts(args.applicants, all_skills)
        
        # Calculate reasonable number of jobs based on number of recruiters
        num_jobs = min(args.jobs, args.recruiters * 3)  # Maximum 3 jobs per recruiter on average
        jobs = create_job_postings(num_jobs, recruiters, all_skills)
        
        # Calculate reasonable number of applications
        application_count = create_applications(applicants, jobs)
        
        print("\nSuccessfully created:")
        print(f"- {len(all_skills)} technical skills")
        print(f"- {len(recruiters)} Indian recruiter accounts")
        print(f"- {len(applicants)} Indian job seeker accounts with AI-generated resumes")
        print(f"- {len(jobs)} job postings from Indian companies")
        print(f"- {application_count} job applications")
        
        print("\nIndian-specific data generation completed successfully!")
        
    except Exception as e:
        print(f"\nError during data generation: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        app_context.pop()

if __name__ == "__main__":
    main() 