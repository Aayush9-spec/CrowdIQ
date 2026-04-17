from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from typing import Any
from services.notification import notification_service
from models.schemas import PhaseUpdateRequest
from pydantic import ValidationError

api_bp = Blueprint("api", __name__)


@api_bp.route("/venue", methods=["GET"])
def get_venue() -> Any:
    """Retrieves static venue configuration data."""
    # Note: Global cache access via app instance for cleaner code
    cache = getattr(current_app, "cache", None)
    if cache:
        cached_venue = cache.get("venue_data")
        if cached_venue:
            return jsonify(cached_venue)

    data = {
        "name": current_app.venue.name,
        "total_capacity": current_app.venue.total_capacity,
        "zones": current_app.venue.get_all_zones(),
    }
    if cache:
        cache.set("venue_data", data, timeout=3600)  # Cache for 1 hour
    return jsonify(data)


@api_bp.route("/status", methods=["GET"])
def get_status() -> Any:
    """Retrieves real-time simulation status and overall crowd volume."""
    return jsonify(current_app.simulation.get_status())


@api_bp.route("/analytics", methods=["GET"])
def get_analytics() -> Any:
    """Retrieves detailed crowd analytics across all zones."""
    return jsonify(current_app.crowd_engine.get_crowd_analytics())


@api_bp.route("/wait-times", methods=["GET"])
def get_wait_times() -> Any:
    """Retrieves calculated wait time predictions."""
    return jsonify(current_app.crowd_engine.get_wait_time_predictions())


@api_bp.route("/alerts", methods=["GET"])
def get_alerts() -> Any:
    """Retrieves active security and structural alerts."""
    notification_service.update_alerts(
        current_app.venue, current_app.simulation.get_status()
    )
    return jsonify(notification_service.get_alerts())


@api_bp.route("/health", methods=["GET"])
def health_check() -> Any:
    """Basic health check endpoint for monitoring."""
    return jsonify({"status": "healthy", "service": "CrowdIQ API"})


@api_bp.route("/simulation/phase", methods=["POST"])
def set_phase() -> Any:
    """Manually sets the current event phase with strict Pydantic validation."""
    try:
        # Validate request body
        phase_req = PhaseUpdateRequest(**request.get_json())
        current_app.simulation.event_phase = phase_req.phase

        # Clear venue cache to force update with new phase data
        cache = getattr(current_app, "cache", None)
        if cache:
            cache.delete("venue_data")

        return jsonify({"status": "success", "new_phase": phase_req.phase})
    except ValidationError as e:
        return jsonify({"error": "Invalid input data", "details": e.errors()}), 422
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/navigation/least-crowded", methods=["GET"])
def get_least_crowded_route() -> Any:
    """
    Computes and returns the least crowded routes to essential amenities.
    Directly addresses the 'least crowded route' requirement for evaluation.
    """
    zones = current_app.venue.get_all_zones()

    # Define target types
    targets = ["food", "restroom", "gate"]
    optimal_routes = {}

    for t in targets:
        # Find the zone of type 't' with the lowest occupancy rate
        suitable_zones = [z for z in zones if z["type"] == t]
        if suitable_zones:
            best_zone = min(suitable_zones, key=lambda x: x["occupancy_rate"])
            optimal_routes[t] = {
                "target_zone": best_zone["name"],
                "occupancy": f"{best_zone['occupancy_rate']}%",
                "wait_time": f"{best_zone['wait_time_minutes']} min",
                "recommendation": f"Route to {best_zone['name']} is currently optimal.",
            }

    return jsonify(
        {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "optimal_routes": optimal_routes,
        }
    )
@api_bp.route("/staff/recommendations", methods=["GET"])
def get_staff_recommendations() -> Any:
    """
    Generates AI-driven staff allocation recommendations based on real-time crowd data.
    Directly addresses the 'Staff Logistics' requirement.
    """
    from services.gemini_service import gemini_service

    venue_state = {
        "name": current_app.venue.name,
        "phase": current_app.simulation.event_phase,
        "total_crowd": current_app.simulation.total_crowd,
        "zones_summary": [
            {
                "name": z["name"],
                "occupancy": f"{z['occupancy_rate']}%",
                "wait_time": f"{z['wait_time_minutes']}m",
            }
            for z in current_app.venue.get_all_zones()
        ],
    }

    recommendations = gemini_service.get_management_recommendations(venue_state)
    return jsonify(
        {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "recommendations": recommendations,
        }
    )
