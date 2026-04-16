import pytest
from models.venue import Zone, Venue, create_default_venue
from models.simulation import CrowdSimulation


def test_zone_creation():
    """Verify zone properties maintain correct types and defaults."""
    zone = Zone(
        id="test-z1", name="Test Zone", capacity=1000, type="seating", lat=0.0, lng=0.0
    )
    assert zone.id == "test-z1"
    assert zone.capacity == 1000
    assert zone.current_count == 0
    assert zone.get_occupancy_percentage() == 0.0


def test_zone_occupancy():
    """Test occupancy calculation."""
    zone = Zone(
        id="test-z2",
        name="Test Zone 2",
        capacity=500,
        type="food_court",
        lat=0.0,
        lng=0.0,
    )
    zone.current_count = 250
    assert zone.get_occupancy_percentage() == 50.0


def test_venue_initialization():
    """Verify venue initializes with correct total capacity and zones."""
    venue = create_default_venue()
    assert venue.name == "CrowdIQ National Stadium"
    assert venue.total_capacity == 60000
    assert len(venue.zones) > 0


def test_simulation_status():
    """Test simulation state tracking."""
    venue = create_default_venue()
    sim = CrowdSimulation(venue)
    status = sim.get_status()
    assert status["phase"] == "Pre-Match"
    assert status["total_crowd"] == 0
