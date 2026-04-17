import time
import math
import logging
from threading import Thread, Lock
from datetime import datetime
from typing import Dict, List, Any
from services.bigquery_service import bigquery_service
from services.monitoring_service import monitoring_service


class CrowdSimulation:
    """
    Core simulation engine for CrowdIQ.
    Handles crowd movement, wait time calculations, and data streaming to GCP.
    """
    
    def __init__(self, venue: Any):
        self.venue = venue
        self.lock = Lock()
        self.running = False
        self.event_phase = "PRE_MATCH"  # PRE_MATCH, ONGOING, HALFTIME, POST_MATCH
        self.simulation_thread = None
        self.update_interval = 2  # Seconds between updates for the simulation
        self.last_bq_stream = 0

        # Internal floating-point trackers for smooth sub-integer accumulations
        self._exact_counts: Dict[str, float] = {}

        # Initialize some crowd
        self._initialize_crowd()

    def _initialize_crowd(self) -> None:
        """Sets initial occupancy levels based on standard stadium entry patterns."""
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

    def _update_wait_time(self, zone: Any) -> None:
        """Calculates wait times using an exponential queueing theory approximation."""
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

    def start(self) -> None:
        """Starts the background simulation thread safely."""
        if not self.running:
            self.running = True
            self.simulation_thread = Thread(target=self._run_simulation)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
            logging.info("Crowd Simulation Thread started successfully.")

    def stop(self) -> None:
        """Gracefully stops the simulation."""
        self.running = False

    def _run_simulation(self) -> None:
        """Engine loop running in a background thread."""
        while self.running:
            try:
                self.update()
                time.sleep(self.update_interval)
            except Exception as e:
                logging.error(f"Error in simulation loop: {e}")

    def _move_crowd(self, source_type: str, target_type: str, percentage_to_move: float, all_zones: List[Any]) -> None:
        """Deterministically moves crowd from all zones of source_type to target_type."""
        sources = [z for z in all_zones if z.type == source_type]
        targets = [z for z in all_zones if z.type == target_type]

        if not sources or not targets:
            return

        total_source_count = sum(self._exact_counts[z.id] for z in sources)
        amount_to_move = total_source_count * percentage_to_move

        if amount_to_move < 0.1:
            return  # Negligible movement

        drain_per_source = amount_to_move / len(sources)
        for s in sources:
            actual_drain = min(self._exact_counts[s.id], drain_per_source)
            self._exact_counts[s.id] -= actual_drain

            # Funnel to targets proportionally (find a target with capacity)
            target = min(
                targets, key=lambda z: self._exact_counts[z.id] / (z.capacity or 1)
            )
            self._exact_counts[target.id] += actual_drain

    def update(self) -> None:
        """Main update tick: handles phase shifts, crowd flow, and data exports."""
        with self.lock:
            total_crowd = sum(self._exact_counts.values())

            # Phase shifts based on total crowd filling
            if (
                self.event_phase == "PRE_MATCH"
                and total_crowd > self.venue.total_capacity * 0.82
            ):
                self.event_phase = "ONGOING"
            elif (
                self.event_phase == "ONGOING"
                and total_crowd > self.venue.total_capacity * 0.85
            ):
                self.event_phase = "HALFTIME"

            zones_list = list(self.venue.zones.values())

            # 1. External Flow
            if self.event_phase == "PRE_MATCH":
                parkings = [z for z in zones_list if z.type == "parking"]
                for p in parkings:
                    fill_rate = 30.0 * (1.0 - (self._exact_counts[p.id] / (p.capacity or 1)))
                    if fill_rate > 0:
                        self._exact_counts[p.id] += fill_rate

            # 2. Directed Internal Flows
            if self.event_phase == "PRE_MATCH":
                self._move_crowd("parking", "gate", 0.10, zones_list)
                self._move_crowd("gate", "stand", 0.15, zones_list)
                self._move_crowd("stand", "food", 0.02, zones_list)
                self._move_crowd("food", "stand", 0.08, zones_list)
            elif self.event_phase == "ONGOING":
                self._move_crowd("parking", "gate", 0.20, zones_list)
                self._move_crowd("gate", "stand", 0.30, zones_list)
                self._move_crowd("stand", "food", 0.005, zones_list)
                self._move_crowd("stand", "restroom", 0.008, zones_list)
                self._move_crowd("food", "stand", 0.15, zones_list)
                self._move_crowd("restroom", "stand", 0.20, zones_list)
            elif self.event_phase == "HALFTIME":
                self._move_crowd("stand", "food", 0.05, zones_list)
                self._move_crowd("stand", "restroom", 0.08, zones_list)
                self._move_crowd("food", "stand", 0.02, zones_list)
                self._move_crowd("restroom", "stand", 0.04, zones_list)
            elif self.event_phase == "POST_MATCH":
                self._move_crowd("stand", "gate", 0.10, zones_list)
                self._move_crowd("gate", "parking", 0.15, zones_list)
                parkings = [z for z in zones_list if z.type == "parking"]
                for p in parkings:
                    self._exact_counts[p.id] *= 0.90

            # 3. State Sync & Metric Logging
            for zone in zones_list:
                count = max(0, min(int(self._exact_counts[zone.id]), zone.capacity))
                zone.current_count = count
                self._exact_counts[zone.id] = float(count)
                self._update_wait_time(zone)
                
                # Log density metrics to Google Cloud Monitoring
                occupancy = count / zone.capacity if zone.capacity > 0 else 0
                monitoring_service.log_metric("zone_density", occupancy, {"zone_id": zone.id})

            # Log total crowd total
            monitoring_service.log_metric("total_crowd", total_crowd)

            # 4. BigQuery Data Streaming (Throttle to once every 10 seconds)
            current_time = time.time()
            if current_time - self.last_bq_stream >= 10:
                row = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "phase": self.event_phase,
                    "total_crowd": int(total_crowd),
                    "zone_data_json": str({z.id: z.current_count for z in zones_list})
                }
                bigquery_service.stream_simulation_data(row)
                self.last_bq_stream = current_time

    def get_status(self) -> Dict[str, Any]:
        """Returns summarized simulation status for the API."""
        total_real_crowd = int(sum(self._exact_counts.values()))
        return {
            "phase": self.event_phase,
            "total_crowd": total_real_crowd,
            "timestamp": datetime.now().isoformat(),
        }
