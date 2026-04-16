from datetime import datetime
import uuid


class NotificationService:
    def __init__(self):
        self.active_alerts = []
        self._last_checked_phase = None

    def update_alerts(self, venue, simulation_status):
        # 1. Check for phase changes
        current_phase = simulation_status["phase"]
        if self._last_checked_phase and self._last_checked_phase != current_phase:
            self.add_alert(
                "Phase Update", f"The event has moved to {current_phase} phase.", "info"
            )
        self._last_checked_phase = current_phase

        # 2. Check for capacity alerts
        for zone in venue.get_all_zones():
            if zone["occupancy_rate"] > 90:
                self.add_alert(
                    "Capacity Warning",
                    f"{zone['name']} is reaching maximum capacity. Consider using alternative routes.",
                    "warning",
                )
            elif zone["occupancy_rate"] > 98:
                self.add_alert(
                    "Zone Full",
                    f"{zone['name']} is now FULL. Entry is restricted.",
                    "critical",
                )

        # 3. Weather alerts (Simulated)
        # In a real app, this would come from a weather API

        # Update timestamps and expiration (keep last 10 alerts)
        self.active_alerts = self.active_alerts[-10:]

    def add_alert(self, title, message, severity="info"):
        # Check if identical alert already exists recently to avoid spam
        for alert in self.active_alerts[-3:]:
            if alert["title"] == title and alert["message"] == message:
                return

        new_alert = {
            "id": str(uuid.uuid4()),
            "title": title,
            "message": message,
            "severity": severity,  # info, warning, critical
            "timestamp": datetime.now().isoformat(),
        }
        self.active_alerts.append(new_alert)

    def get_alerts(self):
        return sorted(self.active_alerts, key=lambda x: x["timestamp"], reverse=True)


# Singleton instance
notification_service = NotificationService()
