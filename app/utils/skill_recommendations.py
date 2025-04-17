"""
Fallback skill recommendation utilities that don't rely on external APIs
"""

import logging
import random
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Predefined skill data for different job categories
TECH_SKILLS = {
    "Web Development": [
        {"name": "React", "reason": "Popular frontend framework used by many tech companies"},
        {"name": "Node.js", "reason": "Server-side JavaScript runtime for building scalable applications"},
        {"name": "TypeScript", "reason": "Adds static typing to JavaScript for better developer experience"},
        {"name": "REST API Design", "reason": "Essential for building modern web services"},
        {"name": "GraphQL", "reason": "Modern API technology that provides more efficient data fetching"}
    ],
    "Data Science": [
        {"name": "Python", "reason": "Primary language used in data science and machine learning"},
        {"name": "SQL", "reason": "Essential for working with databases and data analysis"},
        {"name": "Pandas", "reason": "Popular data manipulation library for Python"},
        {"name": "Machine Learning", "reason": "Foundation for predictive analytics and AI applications"},
        {"name": "Data Visualization", "reason": "Important for communicating insights from data"}
    ],
    "Cloud Computing": [
        {"name": "AWS", "reason": "Leading cloud platform with high market demand"},
        {"name": "Docker", "reason": "Container technology essential for modern deployment"},
        {"name": "Kubernetes", "reason": "Industry standard for container orchestration"},
        {"name": "Infrastructure as Code", "reason": "Modern approach to managing cloud resources"},
        {"name": "CI/CD", "reason": "Automation for software delivery and deployment"}
    ],
    "Cybersecurity": [
        {"name": "Network Security", "reason": "Fundamental for protecting organizational infrastructure"},
        {"name": "Ethical Hacking", "reason": "Helps identify and address security vulnerabilities"},
        {"name": "Security Compliance", "reason": "Important for regulatory requirements in many industries"},
        {"name": "Identity Management", "reason": "Critical for secure access control"},
        {"name": "Threat Analysis", "reason": "Essential for proactive security measures"}
    ]
}

# General skills valuable across domains
GENERAL_SKILLS = [
    {"name": "Project Management", "reason": "Essential for coordinating work across teams"},
    {"name": "Communication", "reason": "Critical for effective collaboration in any role"},
    {"name": "Problem Solving", "reason": "Fundamental skill valued by all employers"},
    {"name": "Critical Thinking", "reason": "Helps in analyzing situations and making decisions"},
    {"name": "Teamwork", "reason": "Important for working effectively in any organization"}
]

def get_fallback_recommendations(
    user_skills: List[str] = None, 
    job_interests: List[str] = None, 
    count: int = 5
) -> List[Dict[str, Any]]:
    """
    Generate basic skill recommendations without using external APIs
    
    Args:
        user_skills: List of user's current skills (to avoid recommending)
        job_interests: List of jobs the user is interested in (for targeting recommendations)
        count: Number of recommendations to return
        
    Returns:
        List of skill recommendation objects
    """
    if user_skills is None:
        user_skills = []
    
    if job_interests is None:
        job_interests = []
    
    # Normalize skills for case-insensitive comparison
    user_skills_normalized = [skill.lower() for skill in user_skills]
    
    # Determine which skill categories to use based on job interests
    categories = []
    for job in job_interests:
        job_lower = job.lower()
        if any(term in job_lower for term in ["web", "frontend", "backend", "full stack", "developer"]):
            categories.append("Web Development")
        if any(term in job_lower for term in ["data", "analyst", "science", "machine learning", "ai"]):
            categories.append("Data Science")
        if any(term in job_lower for term in ["cloud", "devops", "infrastructure", "platform"]):
            categories.append("Cloud Computing")
        if any(term in job_lower for term in ["security", "cyber", "compliance", "risk"]):
            categories.append("Cybersecurity")
    
    # If no specific categories matched, include all categories
    if not categories:
        categories = list(TECH_SKILLS.keys())
    
    # Get skills from the relevant categories
    all_skills = []
    for category in categories:
        all_skills.extend(TECH_SKILLS.get(category, []))
    
    # Always include some general skills
    all_skills.extend(GENERAL_SKILLS)
    
    # Filter out skills the user already has
    filtered_skills = [
        skill for skill in all_skills 
        if skill["name"].lower() not in user_skills_normalized
    ]
    
    # Randomize the order to provide variety
    random.shuffle(filtered_skills)
    
    # Take only the requested number of recommendations
    recommendations = filtered_skills[:count]
    
    # Assign relevance scores (simulating a smart algorithm)
    for i, rec in enumerate(recommendations):
        # Start with higher scores for the first recommendations
        base_score = 90 - (i * 5)
        # Add some randomness
        variance = random.randint(-5, 5)
        rec["relevance_score"] = max(60, min(95, base_score + variance))
        
        # Make sure each recommendation has the expected structure
        if "reason" in rec and "skill_name" not in rec:
            rec["skill_name"] = rec["name"]
    
    return recommendations

def get_fallback_skill_details(skill_name: str) -> Dict[str, Any]:
    """
    Get basic information about a skill without using external APIs
    
    Args:
        skill_name: Name of the skill
        
    Returns:
        Dictionary with basic information about the skill
    """
    # Generic skill description template
    return {
        "description": f"{skill_name} is a valuable skill in today's job market that can enhance your employability and career prospects.",
        "market_value": f"Professionals with {skill_name} skills are in demand across various industries. This skill can help you qualify for more job opportunities.",
        "learning_time": "Learning time varies based on your background and dedication, but most people can gain basic proficiency within 2-3 months of consistent practice.",
        "resources": [
            {
                "name": "Online Courses",
                "url": "https://www.coursera.org/",
                "description": f"Search for {skill_name} courses on platforms like Coursera, Udemy, or edX."
            },
            {
                "name": "Documentation and Tutorials",
                "url": "https://www.w3schools.com/",
                "description": "Look for official documentation or tutorial websites for structured learning."
            },
            {
                "name": "Practice Projects",
                "url": "https://github.com/",
                "description": "Build small projects to apply what you learn and create portfolio pieces."
            }
        ]
    } 