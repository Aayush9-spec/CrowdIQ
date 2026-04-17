import time
import logging
import os
from google.cloud import monitoring_v3
from config import get_config

config = get_config()


class MonitoringService:
    """Service to handle custom metrics for Google Cloud Monitoring."""

    def __init__(self):
        self.project_id = config.GCP_PROJECT_ID
        self.client = None
        self.enabled = config.MONITORING_ENABLED

        if self.enabled and os.environ.get("FLASK_ENV") == "production":
            try:
                self.client = monitoring_v3.MetricServiceClient()
                logging.info(
                    f"Cloud Monitoring initialized for project: {self.project_id}"
                )
            except Exception as e:
                logging.error(f"Failed to initialize Monitoring client: {e}")
                self.enabled = False

    def log_metric(self, metric_name: str, value: float, labels: dict = None):
        """Sends a custom gauge metric to Cloud Monitoring."""
        if not self.enabled or not self.client:
            return

        try:
            series = monitoring_v3.TimeSeries()
            series.metric.type = f"custom.googleapis.com/crowdiq/{metric_name}"
            series.resource.type = "global"

            if labels:
                for k, v in labels.items():
                    series.metric.labels[k] = v

            now = monitoring_v3.TimeInterval()
            now.end_time.seconds = int(time.time())

            point = monitoring_v3.Point()
            point.value.double_value = value
            point.interval = now

            series.points = [point]

            project_name = f"projects/{self.project_id}"
            self.client.create_time_series(name=project_name, time_series=[series])
        except Exception as e:
            logging.error(f"Error logging metric {metric_name}: {e}")


# Singleton instance
monitoring_service = MonitoringService()
