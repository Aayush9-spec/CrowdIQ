from flask import Blueprint, jsonify, request, current_app
from services.gemini_service import gemini_service

assistant_bp = Blueprint("assistant", __name__)


@assistant_bp.route("/chat", methods=["POST"])
def chat():
    """AI-powered chat assistant for attendees and staff."""
    data = request.json
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Get current venue context to ground the AI
    venue_context = current_app.crowd_engine.get_venue_context_for_ai()

    # Get response from Gemini
    response = gemini_service.get_ai_response(user_message, venue_context)

    return jsonify(
        {
            "response": response,
            "context_used": {
                "phase": venue_context["phase"],
                "total_crowd": venue_context["total_crowd"],
            },
        }
    )


@assistant_bp.route("/recommendations", methods=["GET"])
def recommendations():
    """Generates strategic management recommendations for the dashboard."""
    venue_context = current_app.crowd_engine.get_venue_context_for_ai()
    recommendations_text = gemini_service.get_management_recommendations(venue_context)

    return jsonify(
        {
            "status": "success",
            "recommendations": recommendations_text,
            "phase": venue_context["phase"],
        }
    )


@assistant_bp.route("/reset", methods=["POST"])
def reset():
    """Resets the assistant session state."""
    return jsonify({"status": "session reset successful"})
