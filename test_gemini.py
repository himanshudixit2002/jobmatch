import google.generativeai as genai

# Configure the API key
API_KEY = "AIzaSyAL1oDOOvBMk3TRcjl8LFtanftZiGV59H4"
genai.configure(api_key=API_KEY)

def main():
    try:
        # List available models
        print("Available models:")
        for model in genai.list_models():
            print(f"- {model.name}")
        
        # Use gemini-1.5-pro which is available
        model = genai.GenerativeModel('models/gemini-1.5-pro')
        
        # Create a simple prompt
        prompt = "Say hello and verify you're connected properly"
        
        # Generate the response
        response = model.generate_content(prompt)
        
        # Print the response
        print("-" * 50)
        print("Gemini API Test")
        print("-" * 50)
        print(response.text)
        print("-" * 50)
        print("API connection successful!")
        
    except Exception as e:
        print(f"Error testing Gemini API: {str(e)}")

if __name__ == "__main__":
    main() 