from flask import Blueprint, jsonify, request
from services.gemini_service import gemini_service

assistant_bp = Blueprint('assistant', __name__)

# crowd_engine will be initialized in app.py
crowd_engine = None

def init_assistant(e):
    global crowd_engine
    crowd_engine = e

@assistant_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
        
    # Get current venue context to ground the AI
    venue_context = crowd_engine.get_venue_context_for_ai()
    
    # Get response from Gemini
    response = gemini_service.get_ai_response(user_message, venue_context)
    
    return jsonify({
        "response": response,
        "context_used": {
            "phase": venue_context['phase'],
            "total_crowd": venue_context['total_crowd']
        }
    })

@assistant_bp.route('/reset', methods=['POST'])
def reset():
    # In a stateful chat session, we would reset here. 
    # For now, we're using simple generation.
    return jsonify({"status": "session reset successful"})
