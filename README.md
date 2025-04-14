# Job Recruitment Platform

A web application that matches job applicants with recruiters based on skills and requirements.

## Features
- User registration (applicants and recruiters)
- Profile management with skills and experience
- Job posting for recruiters
- Automatic applicant recommendations for jobs
- Application tracking

## Setup

1. Install the dependencies:
```
pip install -r requirements.txt
```

2. Initialize the database:
```
python init_db.py
```

3. Run the application:
```
python run.py
```

4. Access the application at: http://localhost:5000

## User Types
- **Applicants**: Can create profiles, add skills, and view recommended jobs
- **Recruiters**: Can post jobs, view applicant recommendations, and manage applications 