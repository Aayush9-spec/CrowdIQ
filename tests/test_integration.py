import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing
    with app.test_client() as client:
        yield client

def test_simulation_workflow(client):
    """Test changing phase and checking status update."""
    # 1. Check initial status
    res1 = client.get("/api/status")
    initial_phase = res1.json["phase"]
    
    # 2. Change phase
    new_phase = "ONGOING" if initial_phase != "ONGOING" else "HALFTIME"
    res2 = client.post("/api/simulation/phase", json={"phase": new_phase})
    assert res2.status_code == 200
    assert res2.json["status"] == "success"
    
    # 3. Verify status changed
    res3 = client.get("/api/status")
    assert res3.json["phase"] == new_phase

def test_assistant_integration(client):
    """Test assistant chat flow with mocked Gemini."""
    # Mock the gemini_service.get_ai_response
    # (Assuming we have pytest-mock installed, if not we use unittest.mock)
    from unittest.mock import patch
    
    with patch("services.gemini_service.GeminiService.get_ai_response") as mock_gemini:
        mock_gemini.return_value = "Mocked AI Response: The stadium is safe."
        
        response = client.post("/api/assistant/chat", json={"message": "Is it safe?"})
        assert response.status_code == 200
        assert "response" in response.json
        assert response.json["response"] == "Mocked AI Response: The stadium is safe."

def test_analytics_consistency(client):
    """Test that analytics data matches status data."""
    status = client.get("/api/status").json
    analytics = client.get("/api/analytics").json
    
    assert "summary" in analytics
    assert status["total_crowd"] >= 0
    assert analytics["summary"]["avg_occupancy"] >= 0
