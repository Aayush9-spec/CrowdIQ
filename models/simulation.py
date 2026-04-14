import random
import time
from threading import Thread, Lock
from datetime import datetime

class CrowdSimulation:
    def __init__(self, venue):
        self.venue = venue
        self.lock = Lock()
        self.running = False
        self.event_phase = "PRE_MATCH"  # PRE_MATCH, ONGOING, HALFTIME, POST_MATCH
        self.simulation_thread = None
        self.update_interval = 2 # Seconds between updates for the simulation
        
        # Initialize some crowd
        self._initialize_crowd()

    def _initialize_crowd(self):
        with self.lock:
            # Start with some people in stands and parking
            for zone_id, zone in self.venue.zones.items():
                if zone.type == 'stand':
                    zone.current_count = int(zone.capacity * 0.2)
                elif zone.type == 'parking':
                    zone.current_count = int(zone.capacity * 0.1)
                else:
                    zone.current_count = random.randint(0, 50)
                
                self._update_wait_time(zone)

    def _update_wait_time(self, zone):
        # Basic wait time formula based on occupancy
        occupancy = zone.current_count / zone.capacity if zone.capacity > 0 else 0
        if zone.type == 'gate':
            zone.wait_time_minutes = int(occupancy * 15) + random.randint(1, 5)
        elif zone.type == 'food':
            zone.wait_time_minutes = int(occupancy * 20) + random.randint(2, 8)
        elif zone.type == 'restroom':
            zone.wait_time_minutes = int(occupancy * 10) + random.randint(1, 4)
        else:
            zone.wait_time_minutes = 0

    def start(self):
        if not self.running:
            self.running = True
            self.simulation_thread = Thread(target=self._run_simulation)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()

    def stop(self):
        self.running = False

    def _run_simulation(self):
        while self.running:
            self.update()
            time.sleep(self.update_interval)

    def update(self):
        with self.lock:
            # Advance event phase based on total crowd (simple heuristic)
            total_crowd = self.venue.get_total_crowd()
            if total_crowd > self.venue.total_capacity * 0.8:
                if self.event_phase == "PRE_MATCH":
                    self.event_phase = "ONGOING"
            
            # Simple movement logic between zones
            zones_list = list(self.venue.zones.values())
            
            for zone in zones_list:
                # 5% of people in each zone might move
                movers_count = int(zone.current_count * 0.05)
                if movers_count == 0 and zone.current_count > 0:
                    movers_count = 1
                
                if movers_count > 0:
                    # Pick a target zone based on type and current phase
                    target_zone = self._pick_target_zone(zone, zones_list)
                    
                    if target_zone and target_zone.id != zone.id:
                        # Check capacity
                        move_amount = min(movers_count, target_zone.capacity - target_zone.current_count)
                        if move_amount > 0:
                            zone.current_count -= move_amount
                            target_zone.current_count += move_amount
                
                # Update wait times
                self._update_wait_time(zone)
            
            # Simulate people entering/leaving the stadium
            self._simulate_external_flow()

    def _pick_target_zone(self, source_zone, all_zones):
        if self.event_phase == "PRE_MATCH":
            # Flow towards stands
            if source_zone.type in ['gate', 'parking', 'food']:
                stands = [z for z in all_zones if z.type == 'stand']
                return random.choice(stands) if stands else None
            # Some flow to food/restrooms
            if random.random() < 0.3:
                amenities = [z for z in all_zones if z.type in ['food', 'restroom']]
                return random.choice(amenities) if amenities else None
        
        elif self.event_phase == "ONGOING":
            # Mostly stay in stands, some to food/restrooms
            if source_zone.type == 'stand' and random.random() < 0.05:
                amenities = [z for z in all_zones if z.type in ['food', 'restroom']]
                return random.choice(amenities) if amenities else None
            if source_zone.type in ['food', 'restroom']:
                stands = [z for z in all_zones if z.type == 'stand']
                return random.choice(stands) if stands else None
                
        return random.choice(all_zones)

    def _simulate_external_flow(self):
        # People arriving at gates
        if self.event_phase == "PRE_MATCH" and self.venue.get_total_crowd() < self.venue.total_capacity:
            gates = [z for z in self.venue.zones.values() if z.type == 'gate']
            for gate in gates:
                arrivals = random.randint(10, 50)
                gate.current_count += arrivals
                
    def get_status(self):
        return {
            "phase": self.event_phase,
            "total_crowd": self.venue.get_total_crowd(),
            "timestamp": datetime.now().isoformat()
        }
