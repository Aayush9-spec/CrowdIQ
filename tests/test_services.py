import pytest
from models.venue import create_default_venue
from models.simulation import CrowdSimulation
from services.crowd_engine import CrowdEngine
from services.notification import notification_service


@pytest.fixture
def crowd_engine():
    venue = create_default_venue()
    sim = CrowdSimulation(venue)
    return CrowdEngine(venue, sim)


def test_engine_analytics(crowd_engine):
    """Ensure analytics are generated properly for all zones."""
    analytics = crowd_engine.get_crowd_analytics()
    # Matches actual CrowdEngine.get_crowd_analytics return keys
    assert "summary" in analytics
    assert "top_crowded" in analytics
    assert "recommendations" in analytics
    assert "highly_crowded_count" in analytics["summary"]


def test_engine_wait_times(crowd_engine):
    """Ensure wait times are predicted dynamically."""
    wait_times = crowd_engine.get_wait_time_predictions()
    assert isinstance(wait_times, list)
    for w in wait_times:
        # Actual key is 'name', not 'zone_name' in crowd_engine.py:82
        assert "name" in w
        assert "current_wait" in w
        assert "predicted_wait_15m" in w


def test_notification_service():
    """Test standard notification service behavior."""
    venue = create_default_venue()
    # Updated to match new all-caps phase naming
    notification_service.update_alerts(venue, {"phase": "PRE_MATCH"})
    alerts = notification_service.get_alerts()
    assert isinstance(alerts, list)
