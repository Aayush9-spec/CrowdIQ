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
            "occupancy_rate": (
                round((self.current_count / self.capacity) * 100, 1)
                if self.capacity > 0
                else 0
            ),
            "wait_time_minutes": self.wait_time_minutes,
            "lat": self.lat,
            "lng": self.lng,
            "coordinates": self.coordinates,
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
    venue = Venue("M. A. Chidambaram Stadium (Chepauk)", 38000)

    # Accurate real-world coordinates for Chepauk Stadium
    # Main Pavilion and Stands
    venue.add_zone(
        Zone("stand_ms", "Main Stand (South)", "stand", 8000, [], 13.0615, 80.2793)
    )
    venue.add_zone(
        Zone(
            "stand_north", "North Stand (I, J, K)", "stand", 12000, [], 13.0642, 80.2793
        )
    )
    venue.add_zone(
        Zone("stand_east", "East Stand (C, D, E)", "stand", 9000, [], 13.0628, 80.2808)
    )
    venue.add_zone(
        Zone("stand_west", "West Stand (G, H)", "stand", 9000, [], 13.0628, 80.2778)
    )

    # Real Entry Gates
    venue.add_zone(
        Zone(
            "gate_victoria",
            "Victoria Hostel Gate (East)",
            "gate",
            3000,
            [],
            13.0625,
            80.2818,
        )
    )
    venue.add_zone(
        Zone(
            "gate_wallahjah",
            "Wallahjah Road Gate (North)",
            "gate",
            4000,
            [],
            13.0650,
            80.2795,
        )
    )
    venue.add_zone(
        Zone("gate_anna", "Anna Salai Gate (West)", "gate", 3000, [], 13.0630, 80.2770)
    )

    # Core Amenities
    venue.add_zone(
        Zone("food_p1", "Pavilion Concourse (Food)", "food", 1500, [], 13.0618, 80.2800)
    )
    venue.add_zone(
        Zone("food_n1", "North Stand Buffet", "food", 1200, [], 13.0640, 80.2785)
    )

    venue.add_zone(
        Zone(
            "rest_main", "Stadium Main Restrooms", "restroom", 400, [], 13.0620, 80.2788
        )
    )
    venue.add_zone(
        Zone(
            "rest_north",
            "North Gallery Restrooms",
            "restroom",
            300,
            [],
            13.0644,
            80.2800,
        )
    )

    # Official Parking Lots
    venue.add_zone(
        Zone("parking_vca", "VCA Parking Area", "parking", 2000, [], 13.0600, 80.2800)
    )
    venue.add_zone(
        Zone(
            "parking_metro",
            "Metro Parking South",
            "parking",
            1500,
            [],
            13.0585,
            80.2785,
        )
    )

    return venue
