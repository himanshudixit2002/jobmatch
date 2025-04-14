#!/usr/bin/env python
"""
Resume Parser CLI - Test tool for the resume parsing functionality
Usage: python parse_resume.py <resume_file_path>
"""

import sys
import os
import json
import google.generativeai as genai
from typing import Dict, List

# Configure the API key
API_KEY = "AIzaSyAL1oDOOvBMk3TRcjl8LFtanftZiGV59H4"
genai.configure(api_key=API_KEY)

def extract_skills_from_resume(resume_text: str) -> List[str]:
    """
    Extract skills from resume text using Gemini API
    
    Args:
        resume_text (str): The resume text content
        
    Returns:
        List[str]: List of extracted skills
    """
    if not resume_text or resume_text.strip() == "":
        return []
    
    try:
        # Define the model
        model = genai.GenerativeModel('models/gemini-1.5-pro')
        
        # Create the prompt
        prompt = f"""
        Extract a list of professional skills from the following resume.
        Return ONLY a Python list of skills as strings, nothing else.
        Skills should be standard industry terms.
        
        RESUME:
        {resume_text}
        """
        
        # Generate the response
        response = model.generate_content(prompt)
        
        # Parse the response to extract the Python list
        response_text = response.text
        
        # Extract list content using basic string manipulation 
        # (safer than eval, assumes response is a proper Python list format)
        if '[' in response_text and ']' in response_text:
            list_text = response_text[response_text.find('['):response_text.rfind(']')+1]
            # Clean and parse the list
            skill_list = [
                skill.strip().strip('"\'') 
                for skill in list_text.strip('[]').split(',')
                if skill.strip()
            ]
            return skill_list
        
        # Fallback: split by lines and clean up
        skills = [
            line.strip().strip('"-,\'[]') 
            for line in response_text.split('\n')
            if line.strip() and not line.strip().startswith('```') and not line.strip().endswith('```')
        ]
        return [skill for skill in skills if skill]
        
    except Exception as e:
        print(f"Error extracting skills with Gemini API: {str(e)}")
        return []

def parse_resume(resume_text: str) -> Dict:
    """
    Parse a resume text to extract structured information using Gemini API
    
    Args:
        resume_text (str): The resume text content
        
    Returns:
        Dict: Dictionary containing parsed resume information
    """
    if not resume_text or resume_text.strip() == "":
        return {
            "skills": [],
            "experience": 0,
            "education": "",
            "success": False,
            "error": "Empty resume text"
        }
    
    try:
        # Define the model
        model = genai.GenerativeModel('models/gemini-1.5-pro')
        
        # Create the prompt
        prompt = f"""
        Parse the following resume and extract key information.
        Return a structured JSON object with the following fields:
        - skills: list of professional skills
        - experience_years: estimated total years of experience (integer)
        - highest_education: highest education level and field
        - job_history: list of previous job positions with company, title, and duration
        
        RESUME:
        {resume_text}
        """
        
        # Generate the response
        response = model.generate_content(prompt)
        
        # Get the response text
        response_text = response.text
        
        # Parse the JSON response (simplified approach)
        import json
        
        # Extract JSON if it's wrapped in code blocks
        if '```json' in response_text:
            json_str = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            json_str = response_text.split('```')[1].split('```')[0].strip()
        else:
            json_str = response_text.strip()
            
        result = json.loads(json_str)
        
        # Ensure we have all expected fields with fallbacks
        parsed_result = {
            "skills": result.get("skills", []),
            "experience": result.get("experience_years", 0),
            "education": result.get("highest_education", ""),
            "job_history": result.get("job_history", []),
            "success": True
        }
        
        return parsed_result
        
    except Exception as e:
        print(f"Error parsing resume with Gemini API: {str(e)}")
        return {
            "skills": [],
            "experience": 0,
            "education": "",
            "success": False,
            "error": str(e)
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_resume.py <resume_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist")
        sys.exit(1)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            resume_text = f.read()
        
        print(f"Parsing resume: {file_path}")
        print("-" * 50)
        
        # Parse resume
        result = parse_resume(resume_text)
        
        if result["success"]:
            print("Resume parsing successful!")
            print("\nExtracted information:")
            print(f"Education: {result['education']}")
            print(f"Experience (years): {result['experience']}")
            
            print("\nSkills:")
            for skill in result.get("skills", []):
                print(f"- {skill}")
            
            if "job_history" in result and result["job_history"]:
                print("\nJob History:")
                for job in result["job_history"]:
                    job_info = []
                    if "company" in job:
                        job_info.append(f"Company: {job['company']}")
                    if "title" in job:
                        job_info.append(f"Title: {job['title']}")
                    if "duration" in job:
                        job_info.append(f"Duration: {job['duration']}")
                    
                    print("- " + ", ".join(job_info))
            
            # Save results to JSON file
            output_file = os.path.splitext(file_path)[0] + "_parsed.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            
            print(f"\nDetailed results saved to: {output_file}")
        else:
            print(f"Resume parsing failed: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 