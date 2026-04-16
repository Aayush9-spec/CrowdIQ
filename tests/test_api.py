import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
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
        assert "predicted_wait_15m" in data[0]
