from datetime import datetime
import uuid
import logging


class NotificationService:
    """
    Manages real-time alerts and system notifications.
    Includes audit logging for security and operational monitoring.
    """

    def __init__(self):
        self.active_alerts = []
        self._last_checked_phase = None

    def update_alerts(self, venue, simulation_status):
        """Checks for threshold violations and phase changes to trigger alerts."""
        # 1. Check for phase changes
        current_phase = simulation_status["phase"]
        if self._last_checked_phase and self._last_checked_phase != current_phase:
            self.add_alert(
                "Phase Update",
                f"The event has moved to {current_phase} phase.",
                "info",
                audit=True,
            )
        self._last_checked_phase = current_phase

        # 2. Check for capacity alerts
        for zone in venue.get_all_zones():
            if zone["occupancy_rate"] > 90:
                self.add_alert(
                    "Capacity Warning",
                    f"{zone['name']} is reaching maximum capacity. Consider using alternative routes.",
                    "warning",
                    audit=True,
                )
            elif zone["occupancy_rate"] > 98:
                self.add_alert(
                    "Zone Full",
                    f"{zone['name']} is now FULL. Entry is restricted.",
                    "critical",
                    audit=True,
                )

        # Update timestamps and expiration (keep last 10 alerts)
        self.active_alerts = self.active_alerts[-10:]

    def add_alert(self, title, message, severity="info", audit=False):
        """Adds a new alert and optionally logs it for auditing."""
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

        if audit:
            # Structure log for Google Cloud Logging
            logging.info(
                f"AUDIT_ALERT: [{severity.upper()}] {title} - {message}",
                extra={
                    "json_fields": {
                        "alert_id": new_alert["id"],
                        "severity": severity,
                        "title": title,
                    }
                },
            )

    def get_alerts(self):
        """Returns the list of active alerts sorted by timestamp."""
        return sorted(self.active_alerts, key=lambda x: x["timestamp"], reverse=True)


# Singleton instance
notification_service = NotificationService()
