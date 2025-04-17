import json
import logging
import google.generativeai as genai
from flask import current_app
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def setup_genai():
    """Configure the Google Generative AI client with API key"""
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        logger.warning("No Gemini API key found. AI features will be disabled.")
        return False
    
    try:
        # Check if API key is valid (not just whitespace or placeholder)
        if api_key.strip() in ["", "your_api_key_here", "REPLACE_ME"]:
            logger.warning("Gemini API key appears to be a placeholder or empty")
            return False
            
        genai.configure(api_key=api_key)
        # Verify configuration by checking a model exists
        model_list = genai.list_models()
        if not model_list:
            logger.warning("No models available with provided Gemini API key")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Failed to configure Gemini AI: {str(e)}", exc_info=True)
        return False

def get_skill_recommendations(
    current_user_skills: List[str], 
    jobs_of_interest: List[str],
    experience_level: str
) -> List[Dict[str, Any]]:
    """
    Generate skill recommendations based on user's current skills and jobs of interest
    
    Args:
        current_user_skills: List of skills the user already has
        jobs_of_interest: Jobs the user is interested in
        experience_level: User's experience level (e.g., "Entry-level", "Mid-level", "Senior")
        
    Returns:
        List of dictionaries with recommended skills and reasons
    """
    # Ensure input data is valid
    if not jobs_of_interest:
        logger.error("No jobs of interest provided for recommendation generation")
        raise ValueError("At least one job of interest is required")
        
    if not setup_genai():
        logger.error("Gemini AI setup failed - cannot generate recommendations")
        raise Exception("Gemini AI is not configured properly")
    
    try:
        # Prepare the prompt for the AI
        prompt = f"""
        You are a career advisor specializing in skill recommendations.
        
        USER'S CURRENT SKILLS:
        {', '.join(current_user_skills) if current_user_skills else 'No skills provided'}
        
        USER'S DESIRED JOBS:
        {', '.join(jobs_of_interest) if jobs_of_interest else 'No specific jobs mentioned'}
        
        USER'S EXPERIENCE LEVEL:
        {experience_level}
        
        Based on the above information, recommend 5-8 skills that would be most valuable for the user to learn next.
        For each skill:
        1. Provide a detailed reason why this skill would be beneficial
        2. Assign a relevance score (0-100) based on how important this skill is for their target jobs
        
        Output your recommendations as a JSON array of objects with the following structure:
        [
            {{
                "skill_name": "Name of the skill",
                "reason": "Detailed reason why this skill is recommended",
                "relevance_score": 85
            }},
            ...
        ]
        
        Only include skills the user doesn't already have. Focus on practical, in-demand skills that would enhance their employability.
        """
        
        logger.debug(f"Sending prompt to Gemini API: {prompt[:100]}...")
        
        # Call the Gemini API
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            
            if not response or not hasattr(response, 'text'):
                logger.error("Received empty or invalid response from Gemini API")
                raise Exception("Invalid response from AI model")
                
            # Extract and parse the JSON response
            content = response.text
            logger.debug(f"Received raw response: {content[:200]}...")
        except Exception as api_error:
            logger.error(f"Error calling Gemini API: {str(api_error)}", exc_info=True)
            raise Exception(f"Error generating recommendations: {str(api_error)}")
        
        try:
            # Find JSON in the response (it might be wrapped in markdown code blocks)
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("Could not find JSON array in response")
                logger.debug(f"Problematic content: {content}")
                raise ValueError("Invalid response format from AI - could not find JSON array")
                
            json_str = content[json_start:json_end]
            recommendations = json.loads(json_str)
            
            # Validate the structure of each recommendation
            valid_recommendations = []
            for rec in recommendations:
                if "skill_name" in rec and "reason" in rec and "relevance_score" in rec:
                    # Ensure relevance_score is a number between 0-100
                    try:
                        rec["relevance_score"] = max(0, min(100, float(rec["relevance_score"])))
                        valid_recommendations.append(rec)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid relevance_score in recommendation: {rec}")
                        rec["relevance_score"] = 70  # Default if invalid
                        valid_recommendations.append(rec)
                else:
                    logger.warning(f"Skipping recommendation with missing fields: {rec}")
                        
            if not valid_recommendations:
                logger.error("No valid recommendations found in AI response")
                raise ValueError("AI did not return any valid skill recommendations")
                
            return valid_recommendations
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from AI response: {str(e)}")
            logger.debug(f"Raw response: {content}")
            raise Exception("Could not parse skill recommendations from AI")
            
    except Exception as e:
        logger.error(f"Error getting skill recommendations from AI: {str(e)}", exc_info=True)
        raise

def get_skill_details_from_ai(skill_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a skill using AI
    
    Args:
        skill_name: Name of the skill to get details for
        
    Returns:
        Dictionary with detailed information about the skill
    """
    if not skill_name or not skill_name.strip():
        logger.error("Empty skill name provided")
        return {
            "description": "No skill specified",
            "market_value": "Information unavailable",
            "learning_time": "Information unavailable",
            "resources": []
        }
        
    if not setup_genai():
        logger.warning(f"Gemini AI not configured - returning basic info for skill: {skill_name}")
        return {
            "description": f"{skill_name} is a valuable skill in the job market.",
            "market_value": "Information unavailable (AI service not configured)",
            "learning_time": "Varies based on experience",
            "resources": [],
            "error": "AI service not available"
        }
    
    try:
        # Prepare the prompt for the AI
        prompt = f"""
        You are a career advisor with expertise in job skills.
        
        Provide detailed information about the skill: {skill_name}
        
        Include the following information:
        1. A detailed description of the skill
        2. The market value of this skill in the current job market
        3. Estimated time required to learn this skill (for a beginner)
        4. A list of 3-5 resources for learning this skill (online courses, books, websites, etc.)
        
        Format your response as a JSON object with the following structure:
        {{
            "description": "Detailed description",
            "market_value": "Information about market value",
            "learning_time": "Estimated learning time",
            "resources": [
                {{
                    "name": "Resource name",
                    "url": "Resource URL",
                    "description": "Brief description of the resource"
                }},
                ...
            ]
        }}
        """
        
        logger.debug(f"Requesting skill details for: {skill_name}")
        
        # Call the Gemini API with timeout and retry
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            
            if not response or not hasattr(response, 'text'):
                logger.error(f"Empty response from Gemini API for skill: {skill_name}")
                raise Exception("Invalid response from AI model")
                
            # Extract the response content
            content = response.text
            logger.debug(f"Received skill details response for {skill_name}, length: {len(content)}")
        except Exception as api_error:
            logger.error(f"API call failed for skill {skill_name}: {str(api_error)}", exc_info=True)
            return {
                "description": f"{skill_name} is a valuable skill in the job market.",
                "market_value": "Information temporarily unavailable",
                "learning_time": "Varies based on experience",
                "resources": [],
                "error": f"API error: {str(api_error)}"
            }
        
        try:
            # Find JSON in the response (it might be wrapped in markdown code blocks)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error(f"Could not find JSON object in response for skill: {skill_name}")
                logger.debug(f"Problematic content: {content}")
                return {
                    "description": f"{skill_name} is a valuable skill in the job market.",
                    "market_value": "Information temporarily unavailable",
                    "learning_time": "Varies based on experience",
                    "resources": [],
                    "error": "Could not parse AI response"
                }
                
            json_str = content[json_start:json_end]
            skill_details = json.loads(json_str)
            
            # Ensure all expected fields are present
            if "description" not in skill_details:
                skill_details["description"] = f"{skill_name} is a valuable skill in the job market."
            if "market_value" not in skill_details:
                skill_details["market_value"] = "Information unavailable"
            if "learning_time" not in skill_details:
                skill_details["learning_time"] = "Varies based on experience"
            if "resources" not in skill_details:
                skill_details["resources"] = []
                
            return skill_details
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from AI response for skill {skill_name}: {str(e)}")
            logger.debug(f"Raw response: {content}")
            return {
                "description": f"{skill_name} is a valuable skill in the job market.",
                "market_value": "Information temporarily unavailable",
                "learning_time": "Varies based on experience",
                "resources": [],
                "error": "Could not parse AI response"
            }
            
    except Exception as e:
        logger.error(f"Error getting skill details from AI for {skill_name}: {str(e)}", exc_info=True)
        return {
            "description": f"{skill_name} is a valuable skill in the job market.",
            "market_value": "Information temporarily unavailable",
            "learning_time": "Varies based on experience",
            "resources": [],
            "error": str(e)
        } 