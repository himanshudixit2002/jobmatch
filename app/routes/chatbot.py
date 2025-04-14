"""
Chatbot Routes for JobMatch

This module handles routes related to the AI-powered chatbot functionality,
including message processing, intent detection, and response generation.
"""

from flask import Blueprint, request, jsonify, session
from flask_login import current_user
import uuid
import json
import re
from app.models.models import db, ChatMessage, ChatbotIntent, UserChatPreference, User, Job, Skill
from datetime import datetime
import random
from app.utils.chatbot_helper import ChatbotHelper

chatbot = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

# Dictionary to store active chatbot helpers by session_id
active_chatbots = {}

# Initialize session ID for guest users
def get_session_id():
    if 'chat_session_id' not in session:
        session['chat_session_id'] = str(uuid.uuid4())
    return session['chat_session_id']

@chatbot.route('/message', methods=['POST'])
def process_message():
    """Process an incoming chatbot message and generate a response"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
            
        session_id = get_session_id()
        
        # Store user message
        chat_msg = ChatMessage(
            user_id=current_user.id if current_user.is_authenticated else None,
            session_id=session_id,
            message=user_message,
            is_bot=False
        )
        db.session.add(chat_msg)
        db.session.commit()
        
        # Get or create chatbot helper for this session
        if session_id not in active_chatbots:
            active_chatbots[session_id] = ChatbotHelper(session_id)
        
        # Generate response using Google's generative AI
        result = active_chatbots[session_id].get_response(user_message)
        response = result['response']
        follow_ups = result['follow_up_questions']
        
        # Validate response
        if not response or not isinstance(response, str):
            print(f"Invalid response generated: {response}")
            response = "I'm sorry, I couldn't generate a proper response. Could you try asking in a different way?"
        
        # Store bot response
        bot_msg = ChatMessage(
            user_id=current_user.id if current_user.is_authenticated else None,
            session_id=session_id,
            message=response,
            is_bot=True,
            context={'intent': 'generated_by_ai'}
        )
        db.session.add(bot_msg)
        db.session.commit()
        
        return jsonify({
            'response': response,
            'follow_up_questions': follow_ups,
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"Error in process_message: {str(e)}")
        return jsonify({
            'response': "I'm having trouble processing your request right now. Please try again in a moment.",
            'follow_up_questions': ["How to find jobs?", "Resume advice?", "Interview tips?"],
            'error': str(e)
        }), 500

@chatbot.route('/history', methods=['GET'])
def get_chat_history():
    """Get chat history for the current session"""
    session_id = get_session_id()
    
    # Get messages from database
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at).all()
    
    # Format messages for response
    history = [
        {
            'id': msg.id,
            'message': msg.message,
            'is_bot': msg.is_bot,
            'timestamp': msg.created_at.isoformat()
        }
        for msg in messages
    ]
    
    return jsonify({
        'history': history,
        'session_id': session_id
    })

@chatbot.route('/preferences', methods=['GET', 'POST'])
def manage_preferences():
    """Get or update user chat preferences"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Handle GET request to retrieve preferences
    if request.method == 'GET':
        prefs = UserChatPreference.query.filter_by(user_id=current_user.id).first()
        
        if not prefs:
            # Create default preferences if not exists
            prefs = UserChatPreference(user_id=current_user.id)
            db.session.add(prefs)
            db.session.commit()
        
        return jsonify(prefs.serialize())
    
    # Handle POST request to update preferences
    data = request.get_json()
    prefs = UserChatPreference.query.filter_by(user_id=current_user.id).first()
    
    if not prefs:
        prefs = UserChatPreference(user_id=current_user.id)
        db.session.add(prefs)
    
    # Update preferences
    if 'auto_suggestions' in data:
        prefs.auto_suggestions = bool(data['auto_suggestions'])
    if 'chat_history_enabled' in data:
        prefs.chat_history_enabled = bool(data['chat_history_enabled'])
    if 'notification_enabled' in data:
        prefs.notification_enabled = bool(data['notification_enabled'])
    if 'theme' in data and data['theme'] in ['light', 'dark']:
        prefs.theme = data['theme']
    
    db.session.commit()
    return jsonify(prefs.serialize())

@chatbot.route('/clear', methods=['POST'])
def clear_chat_history():
    """Clear chat history for the current session"""
    session_id = get_session_id()
    
    ChatMessage.query.filter_by(session_id=session_id).delete()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Chat history cleared'})

# Clean up old helpers periodically to prevent memory leaks
@chatbot.before_app_request
def cleanup_inactive_helpers():
    """Clean up inactive chatbot helpers to prevent memory leaks"""
    # This is a very simple cleanup that runs occasionally
    if random.random() < 0.01:  # 1% chance of running on any request
        # In a real app, you'd use timestamps to determine inactive sessions
        if len(active_chatbots) > 100:  # If we have too many active sessions
            # Just keep the 50 most recent ones
            active_chatbots_list = list(active_chatbots.items())
            active_chatbots.clear()
            for session_id, helper in active_chatbots_list[-50:]:
                active_chatbots[session_id] = helper

# Helper functions for response generation
def generate_response(user_message, session_id):
    """Generate a response based on the user's message and conversation context"""
    # Get conversation context by looking at recent messages
    recent_messages = ChatMessage.query.filter_by(
        session_id=session_id
    ).order_by(ChatMessage.created_at.desc()).limit(5).all()
    recent_messages.reverse()  # Chronological order
    
    # Detect intent from user message
    intent, confidence = detect_intent(user_message)
    
    # Create context object
    context = {
        'intent': intent,
        'confidence': confidence,
        'user_data': get_user_data() if current_user.is_authenticated else None,
        'previous_intents': [msg.context.get('intent') for msg in recent_messages if msg.is_bot and msg.context]
    }
    
    # Get appropriate response based on intent
    response = get_response_for_intent(intent, user_message, context)
    
    return response, context

def detect_intent(message):
    """Detect the user's intent from their message"""
    # Get all intents from database
    intents = ChatbotIntent.query.all()
    
    best_match = None
    highest_score = 0
    
    for intent in intents:
        # Calculate match score based on keyword presence
        score = 0
        for keyword in intent.keywords:
            # Use regex to find whole word matches with word boundaries
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            matches = re.findall(pattern, message.lower())
            if matches:
                score += len(matches) * 10  # Weight for exact matches
        
        # Check partial matches
        for keyword in intent.keywords:
            if keyword.lower() in message.lower() and len(keyword) > 3:  # Only consider substantive keywords
                score += 5  # Lower weight for partial matches
        
        if score > highest_score:
            highest_score = score
            best_match = intent.intent_name
    
    # Default to general inquiry if no good match
    if not best_match or highest_score < 10:
        return 'general_inquiry', 0.5
    
    confidence = min(highest_score / 100, 0.95)  # Cap confidence at 0.95
    return best_match, confidence

def get_response_for_intent(intent, user_message, context):
    """Get an appropriate response based on detected intent"""
    intent_obj = ChatbotIntent.query.filter_by(intent_name=intent).first()
    
    if intent_obj:
        response_template = intent_obj.response_template
        
        # Replace variables in template
        if '{user_name}' in response_template and context.get('user_data'):
            response_template = response_template.replace('{user_name}', context['user_data'].get('name', 'there'))
        
        # Replace other dynamic variables
        response_template = replace_dynamic_content(response_template, user_message, context)
        
        return response_template
    
    # Fallback responses for unknown intents
    fallbacks = [
        "I'm not entirely sure I understand. Could you rephrase that or ask me about job searching, applications, or interview preparation?",
        "Thanks for your message. I'm specialized in helping with job-related queries like finding jobs, preparing resumes, or managing applications. How can I assist you with your career?",
        "I'm still learning! Could you try asking me about available jobs, application status, or career advice?",
        "I'm not sure I caught that correctly. I'm here to help with your job search and career questions. What specific help do you need?"
    ]
    
    return random.choice(fallbacks)

def replace_dynamic_content(template, user_message, context):
    """Replace dynamic content in response templates"""
    # Job-related content
    if '{job_count}' in template:
        job_count = Job.query.filter_by(is_active=True).count()
        template = template.replace('{job_count}', str(job_count))
    
    # Skill-related content
    if '{popular_skills}' in template:
        # Get top 3 popular skills
        skills = Skill.query.limit(3).all()
        skill_names = ', '.join([skill.name for skill in skills])
        template = template.replace('{popular_skills}', skill_names)
    
    # Time-aware content
    if '{time_greeting}' in template:
        hour = datetime.now().hour
        greeting = "Good morning" if 5 <= hour < 12 else "Good afternoon" if 12 <= hour < 18 else "Good evening"
        template = template.replace('{time_greeting}', greeting)
    
    return template

def get_user_data():
    """Get relevant data for the current user"""
    if not current_user.is_authenticated:
        return None
    
    user_data = {
        'name': current_user.name,
        'email': current_user.email,
        'is_recruiter': current_user.is_recruiter(),
        'is_applicant': current_user.is_applicant()
    }
    
    # Add user type specific data
    if current_user.is_applicant():
        # Get application count
        application_count = len(current_user.applications)
        user_data['application_count'] = application_count
        
        # Get skills
        skills = [skill.name for skill in current_user.skills]
        user_data['skills'] = skills
    
    if current_user.is_recruiter():
        # Get posted job count
        job_count = len(current_user.jobs)
        user_data['job_count'] = job_count
        
        # Get company
        user_data['company'] = current_user.company
    
    return user_data 