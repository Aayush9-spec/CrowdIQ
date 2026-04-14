class Zone:
    def __init__(self, id, name, zone_type, capacity, coordinates, lat, lng):
        self.id = id
        self.name = name
        self.type = zone_type  # 'gate', 'stand', 'food', 'restroom', 'parking', 'vip'
        self.capacity = capacity
        self.coordinates = coordinates  # For map polygon rendering
        self.lat = lat
        self.lng = lng
        self.current_count = 0
        self.wait_time_minutes = 0

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "capacity": self.capacity,
            "current_count": self.current_count,
            "occupancy_rate": round((self.current_count / self.capacity) * 100, 1) if self.capacity > 0 else 0,
            "wait_time_minutes": self.wait_time_minutes,
            "lat": self.lat,
            "lng": self.lng,
            "coordinates": self.coordinates
        }

class Venue:
    def __init__(self, name, total_capacity):
        self.name = name
        self.total_capacity = total_capacity
        self.zones = {}

    def add_zone(self, zone):
        self.zones[zone.id] = zone

    def get_all_zones(self):
        return [zone.to_dict() for zone in self.zones.values()]

    def get_total_crowd(self):
        return sum(zone.current_count for zone in self.zones.values())

def create_default_venue():
    venue = Venue("CrowdIQ National Stadium", 60000)
    
    # Generic circular stadium layout for simulation
    # In a real app, these coordinates would be precise GPS points
    
    # Stands (North, South, East, West)
    venue.add_zone(Zone("stand_n", "North Stand", "stand", 15000, [], 12.9716, 77.5946))
    venue.add_zone(Zone("stand_s", "South Stand", "stand", 15000, [], 12.9696, 77.5946))
    venue.add_zone(Zone("stand_e", "East Stand", "stand", 15000, [], 12.9706, 77.5956))
    venue.add_zone(Zone("stand_w", "West Stand", "stand", 15000, [], 12.9706, 77.5936))
    
    # Gates
    venue.add_zone(Zone("gate_1", "Main Gate 1", "gate", 2000, [], 12.9726, 77.5946))
    venue.add_zone(Zone("gate_2", "Gate 2 (East)", "gate", 1500, [], 12.9706, 77.5966))
    venue.add_zone(Zone("gate_3", "Gate 3 (South)", "gate", 1500, [], 12.9686, 77.5946))
    venue.add_zone(Zone("gate_4", "Gate 4 (West)", "gate", 1500, [], 12.9706, 77.5926))
    
    # Food Courts
    venue.add_zone(Zone("food_a", "Food Court A (North)", "food", 1000, [], 12.9718, 77.5950))
    venue.add_zone(Zone("food_b", "Food Court B (South)", "food", 1000, [], 12.9698, 77.5942))
    
    # Restrooms
    venue.add_zone(Zone("rest_1", "Restroom Block 1", "restroom", 200, [], 12.9712, 77.5952))
    venue.add_zone(Zone("rest_2", "Restroom Block 2", "restroom", 200, [], 12.9700, 77.5940))
    
    # Parking
    venue.add_zone(Zone("parking_p1", "Primary Parking", "parking", 5000, [], 12.9736, 77.5946))
    
    return venue
