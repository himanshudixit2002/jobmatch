import os
import json
import requests
import logging
from flask import current_app
from dotenv import load_dotenv

# Load environment variables from .env file for direct access
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_gemini_api_key():
    """Get Gemini API key from Flask config or environment variable"""
    # Try to get from Flask config if in application context
    try:
        return current_app.config.get('GEMINI_API_KEY')
    except RuntimeError:
        # If not in application context, get from environment
        return os.environ.get('GEMINI_API_KEY')

def get_ai_skill_recommendation(user_skills, job_requirements, experience_level):
    """
    Get AI-powered skill recommendations using Google's Gemini API
    
    Args:
        user_skills (list): List of user's current skills
        job_requirements (list): List of skills from relevant job postings
        experience_level (int): User's years of experience
        
    Returns:
        dict: AI recommendations with skills, relevance scores, and reasons
    """
    api_key = get_gemini_api_key()
    
    logger.info(f"Starting AI skill recommendation. Found API key: {bool(api_key)}")
    logger.info(f"User has {len(user_skills)} skills and {len(job_requirements)} job requirements")
    
    if not api_key:
        logger.error("GEMINI_API_KEY not found in configuration")
        return {
            "error": "GEMINI_API_KEY not found in configuration",
            "skills": []
        }
    
    # Format the prompt for the AI - using triple quotes to avoid f-string issues
    prompt = f"""
As an AI career advisor, analyze a job seeker's skills and recommend new skills they should acquire to improve their employability.

Job seeker's current skills: {', '.join(user_skills)}
Skills in demand from job listings: {', '.join(job_requirements)}
Job seeker's experience level: {experience_level} years

Provide 5 recommended skills that would most benefit this job seeker, considering:
1. Which skills appear most frequently in job listings that the job seeker doesn't have
2. Which skills complement their existing skillset
3. Which skills are appropriate for their experience level
4. Which skills are trending in the current job market

Format your response as a JSON object with the following structure:
{{
  "skills": [
    {{
      "name": "Skill Name",
      "relevance_score": 85,
      "recommendation_reason": "Detailed reason explaining why this skill is recommended"
    }},
    ... more skills ...
  ]
}}

Provide only the JSON with no additional text.
"""
    
    # Call Gemini API
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1024
        }
    }
    
    try:
        logger.info("Sending request to Gemini API")
        response = requests.post(
            f"{api_url}?key={api_key}",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            response_json = response.json()
            
            # Extract the text response from Gemini
            text_response = response_json["candidates"][0]["content"]["parts"][0]["text"]
            logger.info(f"Received response from Gemini API: {text_response[:100]}...")
            
            # Parse the JSON string from the text response
            try:
                # Clean the text if it has markdown code blocks
                if "```json" in text_response:
                    text_response = text_response.split("```json")[1].split("```")[0].strip()
                elif "```" in text_response:
                    text_response = text_response.split("```")[1].split("```")[0].strip()
                
                # Log the processed text for debugging
                logger.info(f"Processed text for JSON parsing: {text_response[:100]}...")
                
                result = json.loads(text_response)
                
                # Ensure the response has the correct structure
                if "skills" not in result:
                    logger.error("Response does not contain 'skills' key")
                    # Add default structure to avoid errors
                    result = {"skills": []}
                
                logger.info(f"Successfully parsed JSON with {len(result.get('skills', []))} skills")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                logger.error(f"Problematic text: {text_response}")
                return {
                    "error": f"Failed to parse AI response: {str(e)}",
                    "skills": []
                }
        else:
            logger.error(f"API request failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
            return {
                "error": f"API request failed with status {response.status_code}",
                "skills": []
            }
    except Exception as e:
        logger.error(f"Exception calling Gemini API: {str(e)}")
        return {
            "error": f"Error calling Gemini API: {str(e)}",
            "skills": []
        }

def get_skill_details(skill_name):
    """
    Get detailed information about a skill using Gemini API
    
    Args:
        skill_name (str): Name of the skill
        
    Returns:
        dict: Detailed information about the skill
    """
    api_key = get_gemini_api_key()
    
    logger.info(f"Getting skill details for: {skill_name}")
    
    if not api_key:
        logger.error("GEMINI_API_KEY not found in configuration")
        return {
            "error": "GEMINI_API_KEY not found in configuration"
        }
    
    # Format the prompt with triple quotes to avoid f-string issues
    prompt = f"""
Provide detailed information about the technical skill "{skill_name}" for a job seeker.
Include:
1. A brief description (2-3 sentences)
2. Why it's valuable in the job market
3. How long it typically takes to learn (beginner to proficient)
4. 2-3 free resources for learning this skill (with links if applicable)

Format your response as a JSON object with the following structure:
{{
  "name": "{skill_name}",
  "description": "Brief description",
  "market_value": "Why it's valuable",
  "learning_time": "Estimated learning time",
  "resources": [
    {{
      "name": "Resource name",
      "url": "Resource URL",
      "description": "Brief description of the resource"
    }},
    ... more resources ...
  ]
}}

Provide only the JSON with no additional text.
"""
    
    # Call Gemini API 
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1024
        }
    }
    
    try:
        logger.info("Sending skill details request to Gemini API")
        response = requests.post(
            f"{api_url}?key={api_key}",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            response_json = response.json()
            
            # Extract the text response from Gemini
            text_response = response_json["candidates"][0]["content"]["parts"][0]["text"]
            logger.info(f"Received skill details response: {text_response[:100]}...")
            
            # Parse the JSON string from the text response
            try:
                # Clean the text if it has markdown code blocks
                if "```json" in text_response:
                    text_response = text_response.split("```json")[1].split("```")[0].strip()
                elif "```" in text_response:
                    text_response = text_response.split("```")[1].split("```")[0].strip()
                
                logger.info(f"Processed text for JSON parsing: {text_response[:100]}...")
                result = json.loads(text_response)
                return result
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error for skill details: {str(e)}")
                logger.error(f"Problematic text: {text_response}")
                return {
                    "error": f"Failed to parse AI response: {str(e)}",
                    "name": skill_name,
                    "description": "Unable to retrieve skill details at this time."
                }
        else:
            logger.error(f"API request failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
            return {
                "error": f"API request failed with status {response.status_code}",
                "name": skill_name,
                "description": "Unable to retrieve skill details at this time."
            }
    except Exception as e:
        logger.error(f"Exception calling Gemini API for skill details: {str(e)}")
        return {
            "error": f"Error calling Gemini API: {str(e)}",
            "name": skill_name,
            "description": "Unable to retrieve skill details at this time."
        } 