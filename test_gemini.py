#!/usr/bin/env python
"""
Test script to verify Gemini API key is working correctly.
Run this script to test the API connection.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

def test_gemini_api():
    """Test if the Gemini API key is valid and working"""
    if not GEMINI_API_KEY:
        print("❌ ERROR: GEMINI_API_KEY not found in .env file")
        print("Please add your Gemini API key to the .env file.")
        return False
    
    # Simple prompt to test the API - no f-string needed here
    prompt = """
    Respond with a simple "Hello, JobMatch! I'm working correctly." if this API call succeeds.
    Keep the response short.
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
            "maxOutputTokens": 100
        }
    }
    
    try:
        print("Testing Gemini API connection...")
        response = requests.post(
            f"{api_url}?key={GEMINI_API_KEY}",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            response_json = response.json()
            
            # Extract the text response from Gemini
            text_response = response_json["candidates"][0]["content"]["parts"][0]["text"]
            print(f"✅ SUCCESS: API connection successful!")
            print(f"Response: {text_response}")
            return True
        else:
            print(f"❌ ERROR: API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR: Exception while calling Gemini API: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gemini_api()
    
    if success:
        print("\nThe Gemini API integration is working correctly!")
        print("All AI-powered features in JobMatch should function properly.")
    else:
        print("\nThe Gemini API integration is NOT working.")
        print("AI-powered features will use fallback algorithms.")
        print("\nTo fix this issue:")
        print("1. Check that your API key in the .env file is correct")
        print("2. Ensure you have enabled the Gemini API in your Google AI Studio console")
        print("3. Verify your internet connection and firewall settings") 