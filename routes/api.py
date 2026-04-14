from flask import Blueprint, jsonify, request
from services.notification import notification_service

api_bp = Blueprint('api', __name__)

# These will be initialized in app.py
venue = None
simulation = None
crowd_engine = None

def init_api(v, s, e):
    global venue, simulation, crowd_engine
    venue = v
    simulation = s
    crowd_engine = e

@api_bp.route('/venue', methods=['GET'])
def get_venue():
    return jsonify({
        "name": venue.name,
        "total_capacity": venue.total_capacity,
        "zones": venue.get_all_zones()
    })

@api_bp.route('/status', methods=['GET'])
def get_status():
    return jsonify(simulation.get_status())

@api_bp.route('/analytics', methods=['GET'])
def get_analytics():
    return jsonify(crowd_engine.get_crowd_analytics())

@api_bp.route('/wait-times', methods=['GET'])
def get_wait_times():
    return jsonify(crowd_engine.get_wait_time_predictions())

@api_bp.route('/alerts', methods=['GET'])
def get_alerts():
    # Update alerts based on current state before returning
    notification_service.update_alerts(venue, simulation.get_status())
    return jsonify(notification_service.get_alerts())

@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "CrowdIQ API"})
