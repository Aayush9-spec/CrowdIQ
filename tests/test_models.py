import pytest
from models.venue import Zone, Venue, create_default_venue
from models.simulation import CrowdSimulation


def test_zone_creation():
    """Verify zone properties maintain correct types and defaults."""
    # Matches Zone(id, name, zone_type, capacity, coordinates, lat, lng)
    zone = Zone(
        id="test-z1",
        name="Test Zone",
        zone_type="stand",
        capacity=1000,
        coordinates=[],
        lat=13.0,
        lng=80.0,
    )
    assert zone.id == "test-z1"
    assert zone.capacity == 1000
    assert zone.current_count == 0
    assert zone.to_dict()["occupancy_rate"] == 0.0


def test_zone_occupancy():
    """Test occupancy calculation."""
    zone = Zone(
        id="test-z2",
        name="Test Zone 2",
        zone_type="food",
        capacity=500,
        coordinates=[],
        lat=13.0,
        lng=80.0,
    )
    zone.current_count = 250
    assert zone.to_dict()["occupancy_rate"] == 50.0


def test_venue_initialization():
    """Verify venue initializes with correct total capacity and zones."""
    venue = create_default_venue()
    # Updated to match real-world Chepauk capacity from venue.py
    assert "M. A. Chidambaram" in venue.name
    assert venue.total_capacity == 38000
    assert len(venue.zones) > 0


def test_simulation_status():
    """Test simulation state tracking."""
    venue = create_default_venue()
    sim = CrowdSimulation(venue)
    status = sim.get_status()
    # Matches new all-caps phase naming
    assert status["phase"] == "PRE_MATCH"
    # Initial crowd is now > 0 due to _initialize_crowd logic
    assert status["total_crowd"] > 0
