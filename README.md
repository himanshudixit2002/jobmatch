# JobMatch - AI-Powered Recruitment Platform

JobMatch is a modern web application that connects job applicants with recruiters using an intelligent skill-matching algorithm. The platform analyzes skills, experience, and job requirements to create optimal matches for both job seekers and employers.

![JobMatch Screenshot](app/static/img/logo.png)

## Features

### For Job Seekers
- Create a professional profile with skills and experience
- Browse job listings with personalized match scores
- One-click job applications
- Interview scheduling and management
- Skill gap analysis and learning recommendations

### For Recruiters
- Post job openings with detailed requirements
- AI-powered candidate matching and ranking
- Application review and candidate tracking
- Interview scheduling with calendar integration
- Candidate feedback and hiring workflow

### Advanced Features
- **AI-Powered Skill Matching:** Semantic matching instead of simple keyword matching with synonym recognition
- **Skill Gap Analysis:** Identify missing skills required for specific roles
- **Interview Management:** Scheduling, feedback, and candidate evaluation
- **Job Market Insights:** Access trends in skills and demand

## Tech Stack
- **Backend:** Flask, SQLAlchemy, Python
- **Frontend:** Bootstrap, jQuery, HTML/CSS
- **Database:** SQLite (development), PostgreSQL (production)
- **Machine Learning:** scikit-learn, NLTK, spaCy

## Setup Instructions

### Prerequisites
- Python 3.8-3.12
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/jobmatch.git
   cd jobmatch
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database with sample data:
   ```
   python simple_init_db.py
   ```

5. Run the application:
   ```
   python run.py
   ```

6. Access the application in your browser at:
   ```
   http://127.0.0.1:5000
   ```

### Demo Data Generation

For more extensive testing or development purposes, you can generate larger sets of demo data with customizable options:

```
python generate_demo_data.py [options]
```

Options:
- `--region {indian,global}`: Generate region-specific data (default: indian)
- `--recruiters RECRUITERS`: Number of recruiter accounts to create (default: 500)
- `--applicants APPLICANTS`: Number of applicant accounts to create (default: 1000)
- `--jobs JOBS`: Number of job postings to create (default: 800)

Examples:
```bash
# Generate default dataset with Indian-specific data
python generate_demo_data.py

# Generate global data with custom quantities
python generate_demo_data.py --region global --recruiters 200 --applicants 500 --jobs 400
```

This script will populate the database with realistic user profiles, job listings, and applications, with either Indian or global data as specified.

### AI-Generated Indian Data

For highly realistic Indian-specific data with AI-generated resumes, you can use our specialized script:

```
python generate_indian_data.py [options]
```

This script uses Google's Gemini API to generate unique, realistic resumes for each applicant, making the demo data much more authentic. It focuses exclusively on the Indian job market with Indian names, companies, cities, and educational institutions.

Prerequisites:
1. Get a Google Gemini API key from https://ai.google.dev/
2. Add your API key to the `.env` file: `GEMINI_API_KEY=your_key_here`

Options:
- `--recruiters RECRUITERS`: Number of Indian recruiter accounts (default: 200)
- `--applicants APPLICANTS`: Number of Indian job seeker accounts (default: 500)
- `--jobs JOBS`: Number of job postings from Indian companies (default: 300)

Example:
```bash
# Generate AI-enhanced Indian dataset
python generate_indian_data.py --applicants 300 --jobs 200
```

**Note:** This script will delete all existing users, jobs, and applications before generating new data.

### Demo Accounts

For testing purposes, you can use the following demo accounts:

**Recruiter:**
- Email: recruiter@example.com
- Password: password

**Job Seeker:**
- Email: applicant@example.com
- Password: password

## Development

### Project Structure
```
jobmatch/
├── app/                      # Main application package
│   ├── models/               # Database models
│   ├── routes/               # Route handlers
│   ├── static/               # Static files (CSS, JS, images)
│   ├── templates/            # Jinja2 templates
│   ├── utils/                # Utility functions
│   └── __init__.py           # App initialization
├── migrations/               # Database migrations
├── requirements.txt          # Python dependencies
├── run.py                    # Application entry point
├── init_db.py                # Database initialization script
├── generate_demo_data.py     # Demo data generator script
├── generate_indian_data.py   # AI-powered Indian data generator
└── README.md                 # Project documentation
```

### Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements
- FontAwesome for icons
- Bootstrap for UI components
- Flask community for excellent documentation