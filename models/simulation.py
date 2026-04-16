import time
import math
from threading import Thread, Lock
from datetime import datetime


class CrowdSimulation:
    def __init__(self, venue):
        self.venue = venue
        self.lock = Lock()
        self.running = False
        self.event_phase = "PRE_MATCH"  # PRE_MATCH, ONGOING, HALFTIME, POST_MATCH
        self.simulation_thread = None
        self.update_interval = 2  # Seconds between updates for the simulation

        # Internal floating-point trackers for smooth sub-integer accumulations
        self._exact_counts = {}

        # Initialize some crowd
        self._initialize_crowd()

    def _initialize_crowd(self):
        with self.lock:
            for zone_id, zone in self.venue.zones.items():
                if zone.type == "stand":
                    # Start almost empty but smooth
                    self._exact_counts[zone.id] = zone.capacity * 0.05
                elif zone.type == "parking":
                    self._exact_counts[zone.id] = zone.capacity * 0.15
                else:
                    self._exact_counts[zone.id] = 0.0

                zone.current_count = int(self._exact_counts[zone.id])
                self._update_wait_time(zone)

    def _update_wait_time(self, zone):
        # Exponential wait time formula based firmly on occupancy (Queue Theory)
        # Eliminates pure randomization jitter
        occupancy = zone.current_count / zone.capacity if zone.capacity > 0 else 0

        # Smooth exponential curve: low occupancy = 0 wait. High occupancy = high wait.
        if zone.type == "gate":
            zone.wait_time_minutes = int(min(25, 20 * (occupancy**1.5)))
        elif zone.type == "food":
            zone.wait_time_minutes = int(min(30, 25 * (occupancy**1.8)))
        elif zone.type == "restroom":
            zone.wait_time_minutes = int(min(15, 12 * (occupancy**2.0)))
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

    def _move_crowd(self, source_type, target_type, percentage_to_move, all_zones):
        """Deterministically moves crowd from all zones of source_type to target_type"""
        sources = [z for z in all_zones if z.type == source_type]
        targets = [z for z in all_zones if z.type == target_type]

        if not sources or not targets:
            return

        total_source_count = sum(self._exact_counts[z.id] for z in sources)
        amount_to_move = total_source_count * percentage_to_move

        if amount_to_move < 0.1:
            return  # Negligible movement

        # Drain sources proportionally
        drain_per_source = amount_to_move / len(sources)
        for s in sources:
            actual_drain = min(self._exact_counts[s.id], drain_per_source)
            self._exact_counts[s.id] -= actual_drain

            # Funnel to targets proportionally (find a target with capacity)
            target = min(
                targets, key=lambda z: self._exact_counts[z.id] / (z.capacity or 1)
            )
            self._exact_counts[target.id] += actual_drain

    def update(self):
        with self.lock:
            total_crowd = sum(self._exact_counts.values())

            # Phase shifts based on total crowd filling the standard stadium limits
            if (
                self.event_phase == "PRE_MATCH"
                and total_crowd > self.venue.total_capacity * 0.82
            ):
                self.event_phase = "ONGOING"
            elif (
                self.event_phase == "ONGOING"
                and total_crowd > self.venue.total_capacity * 0.85
            ):
                # In a real app this would be time-based. We simulate halftime peak artificially.
                self.event_phase = "HALFTIME"

            zones_list = list(self.venue.zones.values())

            # 1. External Flow (People arriving from outside system to parking)
            if self.event_phase == "PRE_MATCH":
                # Smooth continuous arrival curve
                parkings = [z for z in zones_list if z.type == "parking"]
                for p in parkings:
                    # Logarithmic slowdown as it fills up
                    fill_rate = 30.0 * (
                        1.0 - (self._exact_counts[p.id] / (p.capacity or 1))
                    )
                    if fill_rate > 0:
                        self._exact_counts[p.id] += fill_rate

            # 2. Directed Internal Flows (Deterministic Pipeline)
            if self.event_phase == "PRE_MATCH":
                self._move_crowd("parking", "gate", 0.10, zones_list)
                self._move_crowd("gate", "stand", 0.15, zones_list)
                self._move_crowd("stand", "food", 0.02, zones_list)  # Grab food early
                self._move_crowd("food", "stand", 0.08, zones_list)

            elif self.event_phase == "ONGOING":
                # Drain remaining gates/parking
                self._move_crowd("parking", "gate", 0.20, zones_list)
                self._move_crowd("gate", "stand", 0.30, zones_list)
                # Tiny trickle to amenities
                self._move_crowd("stand", "food", 0.005, zones_list)
                self._move_crowd("stand", "restroom", 0.008, zones_list)
                self._move_crowd("food", "stand", 0.15, zones_list)
                self._move_crowd("restroom", "stand", 0.20, zones_list)

            elif self.event_phase == "HALFTIME":
                # Sudden massive rush to amenities
                self._move_crowd("stand", "food", 0.05, zones_list)
                self._move_crowd("stand", "restroom", 0.08, zones_list)
                # Slower drain back to stands initially
                self._move_crowd("food", "stand", 0.02, zones_list)
                self._move_crowd("restroom", "stand", 0.04, zones_list)

            elif self.event_phase == "POST_MATCH":
                # Rapid drain outwards
                self._move_crowd("stand", "gate", 0.10, zones_list)
                self._move_crowd("gate", "parking", 0.15, zones_list)

                # People leaving parking completely (vanishing from system)
                parkings = [z for z in zones_list if z.type == "parking"]
                for p in parkings:
                    self._exact_counts[p.id] *= 0.90

            # Sync exact fractional numbers back to integer counters safely
            for zone in zones_list:
                # Ensure no negatives and respect capacity boundary naturally
                count = max(0, min(int(self._exact_counts[zone.id]), zone.capacity))
                zone.current_count = count
                self._exact_counts[zone.id] = float(count)  # Sync back truncation
                self._update_wait_time(zone)

    def get_status(self):
        total_real_crowd = int(sum(self._exact_counts.values()))
        return {
            "phase": self.event_phase,
            "total_crowd": total_real_crowd,
            "timestamp": datetime.now().isoformat(),
        }
