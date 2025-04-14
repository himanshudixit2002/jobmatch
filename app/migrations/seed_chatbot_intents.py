"""
Seed script for populating the chatbot intents database

This script adds predefined intents, responses, and follow-up questions
to the ChatbotIntent table for use by the JobMatch AI assistant.
"""

from app import create_app
from app.models.models import db, ChatbotIntent
import json

def seed_chatbot_intents():
    """Add initial chatbot intents to the database"""
    app = create_app()
    
    with app.app_context():
        # Clear existing intents
        ChatbotIntent.query.delete()
        
        # List of intents to add
        intents = [
            {
                "intent_name": "greeting",
                "keywords": ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"],
                "response_template": "{time_greeting}, {user_name}! I'm your JobMatch assistant. How can I help you with your job search today?",
                "follow_up_questions": [
                    "How do I find a job?",
                    "What skills are in demand?",
                    "How does the matching algorithm work?"
                ]
            },
            {
                "intent_name": "job_search",
                "keywords": ["find job", "search job", "job listing", "job opening", "available jobs", "looking for job"],
                "response_template": "We currently have {job_count} active job listings. You can browse them by clicking on 'Browse Jobs' in the navigation menu. You can filter by location, skills, and experience level to find the best match for you.",
                "follow_up_questions": [
                    "How do I apply for a job?",
                    "What makes a good application?",
                    "How can I improve my match score?"
                ]
            },
            {
                "intent_name": "resume_advice",
                "keywords": ["resume", "cv", "curriculum vitae", "resume tips", "improve resume", "update resume"],
                "response_template": "A strong resume is crucial for your job search! Here are some tips:\n\n1. Highlight skills that match the job you're applying for\n2. Use action verbs and quantify achievements\n3. Keep it concise and well-organized\n4. Include keywords relevant to your industry\n\nThe most sought-after skills currently include: {popular_skills}",
                "follow_up_questions": [
                    "How do I add skills to my profile?",
                    "Can you review my resume?",
                    "What format should my resume be in?"
                ]
            },
            {
                "intent_name": "interview_prep",
                "keywords": ["interview", "interview tips", "prepare for interview", "interview question", "interview advice"],
                "response_template": "Preparing for an interview? Great! Here are some tips:\n\n1. Research the company thoroughly\n2. Practice common interview questions\n3. Prepare examples that demonstrate your skills\n4. Have questions ready to ask the interviewer\n5. Dress professionally and arrive early\n\nWould you like more specific advice for a particular type of interview?",
                "follow_up_questions": [
                    "How do I answer 'tell me about yourself'?",
                    "What should I wear to an interview?",
                    "How do I negotiate salary?"
                ]
            },
            {
                "intent_name": "application_status",
                "keywords": ["application status", "check application", "application update", "job application", "submitted application"],
                "response_template": "You can check the status of your job applications by clicking on 'My Applications' in the navigation menu. This will show all your submitted applications and their current status (pending, reviewed, interviewed, etc.).",
                "follow_up_questions": [
                    "What do the different statuses mean?",
                    "How long until I hear back?",
                    "Should I follow up on my application?"
                ]
            },
            {
                "intent_name": "recruiter_info",
                "keywords": ["recruiter", "post job", "hiring", "find candidate", "talent", "employer"],
                "response_template": "As a recruiter, you can post job openings, review applications, and schedule interviews through our platform. To post a new job, click on 'Post Job' in the navigation menu. You'll be able to specify required skills, experience level, and other details.",
                "follow_up_questions": [
                    "How do I edit a job posting?",
                    "How does the matching algorithm work?",
                    "How do I contact candidates?"
                ]
            },
            {
                "intent_name": "profile_management",
                "keywords": ["profile", "update profile", "edit profile", "my profile", "account settings"],
                "response_template": "You can view and edit your profile by clicking on your name in the top-right corner and selecting 'My Profile' or 'Edit Profile'. Make sure to keep your skills and experience up to date for better job matches!",
                "follow_up_questions": [
                    "How do I add skills to my profile?",
                    "Can recruiters see my profile?",
                    "How do I change my password?"
                ]
            },
            {
                "intent_name": "matching_algorithm",
                "keywords": ["algorithm", "match", "matching", "job match", "match score", "compatibility"],
                "response_template": "Our matching algorithm calculates a compatibility score between your profile and job postings. It considers skills (70% weight) and experience (30% weight). The more skills you have that match the job requirements, the higher your match score will be. Keep your profile updated with relevant skills to improve your matches!",
                "follow_up_questions": [
                    "How do I improve my match score?",
                    "Why did I get a low match score?",
                    "Can recruiters see my match score?"
                ]
            },
            {
                "intent_name": "general_inquiry",
                "keywords": ["help", "support", "information", "question", "explain", "how to", "what is"],
                "response_template": "I'm here to help with any questions about JobMatch! You can ask about finding jobs, submitting applications, preparing for interviews, or using any feature of our platform. What specific information are you looking for?",
                "follow_up_questions": [
                    "How do I get started?",
                    "What are the most popular features?",
                    "Is there a mobile app?"
                ]
            },
            {
                "intent_name": "thank_you",
                "keywords": ["thanks", "thank you", "appreciate", "helpful", "great", "awesome"],
                "response_template": "You're welcome! I'm happy to help. Is there anything else you'd like to know about JobMatch?",
                "follow_up_questions": [
                    "How do I find a job?",
                    "Tell me about the matching algorithm",
                    "What makes a good resume?"
                ]
            }
        ]
        
        # Add intents to database
        for intent_data in intents:
            intent = ChatbotIntent(
                intent_name=intent_data["intent_name"],
                keywords=json.dumps(intent_data["keywords"]),
                response_template=intent_data["response_template"],
                follow_up_questions=json.dumps(intent_data["follow_up_questions"])
            )
            db.session.add(intent)
        
        db.session.commit()
        print(f"Added {len(intents)} chatbot intents to the database")

if __name__ == "__main__":
    seed_chatbot_intents() 