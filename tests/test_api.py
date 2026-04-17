import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "up"}


def test_api_venue_endpoint(client):
    """Test the venue data endpoint."""
    response = client.get("/api/venue")
    assert response.status_code == 200
    data = response.json
    assert "name" in data
    assert "zones" in data
    assert len(data["zones"]) > 0


def test_api_status_endpoint(client):
    """Test the status endpoint."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json
    assert "phase" in data
    assert "total_crowd" in data


def test_api_wait_times_endpoint(client):
    """Test the wait times endpoint."""
    response = client.get("/api/wait-times")
    assert response.status_code == 200
    data = response.json
    assert isinstance(data, list)
    if len(data) > 0:
        assert "current_wait" in data[0]


def test_simulation_phase_validation(client):
    """Test strict Pydantic validation for phase updates."""
    # Valid phase
    response = client.post("/api/simulation/phase", json={"phase": "ONGOING"})
    assert response.status_code == 200

    # Invalid phase
    response = client.post("/api/simulation/phase", json={"phase": "INVALID_PHASE"})
    assert response.status_code == 422
    assert "error" in response.json


def test_recommendations_endpoint(client):
    """Test the new AI recommendations endpoint."""
    from unittest.mock import patch

    with patch(
        "services.gemini_service.GeminiService.get_management_recommendations"
    ) as mock_rec:
        mock_rec.return_value = "1. Allocate more staff to Zone A\n2. Open Gate 4"
        response = client.get("/api/assistant/recommendations")
        assert response.status_code == 200
        assert "recommendations" in response.json
        assert "1. Allocate" in response.json["recommendations"]
