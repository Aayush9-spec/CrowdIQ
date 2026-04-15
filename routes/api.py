from flask import Blueprint, jsonify, request
from typing import Any
from services.notification import notification_service

api_bp = Blueprint('api', __name__)

# These will be initialized in app.py
venue: Any = None
simulation: Any = None
crowd_engine: Any = None
cache: Any = None

def init_api(v: Any, s: Any, e: Any, c: Any) -> None:
    """Initialize API blueprint with core application dependencies."""
    global venue, simulation, crowd_engine, cache
    venue = v
    simulation = s
    crowd_engine = e
    cache = c

@api_bp.route('/venue', methods=['GET'])
def get_venue() -> Any:
    """Retrieves static venue configuration data."""
    if cache:
        cached_venue = cache.get("venue_data")
        if cached_venue:
            return jsonify(cached_venue)
            
    data = {
        "name": venue.name,
        "total_capacity": venue.total_capacity,
        "zones": venue.get_all_zones()
    }
    if cache:
        cache.set("venue_data", data, timeout=3600)  # Cache for 1 hour
    return jsonify(data)

@api_bp.route('/status', methods=['GET'])
def get_status() -> Any:
    """Retrieves real-time simulation status and overall crowd volume."""
    return jsonify(simulation.get_status())

@api_bp.route('/analytics', methods=['GET'])
def get_analytics() -> Any:
    """Retrieves detailed crowd analytics across all zones."""
    return jsonify(crowd_engine.get_crowd_analytics())

@api_bp.route('/wait-times', methods=['GET'])
def get_wait_times() -> Any:
    """Retrieves calculated wait time predictions."""
    return jsonify(crowd_engine.get_wait_time_predictions())

@api_bp.route('/alerts', methods=['GET'])
def get_alerts() -> Any:
    """Retrieves active security and structural alerts."""
    # Update alerts based on current state before returning
    notification_service.update_alerts(venue, simulation.get_status())
    return jsonify(notification_service.get_alerts())

@api_bp.route('/health', methods=['GET'])
def health_check() -> Any:
    """Basic health check endpoint for monitoring."""
    return jsonify({"status": "healthy", "service": "CrowdIQ API"})
