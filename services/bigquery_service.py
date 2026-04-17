import logging
import os
from google.cloud import bigquery
from config import get_config

config = get_config()

class BigQueryService:
    """Service to handle streaming data to BigQuery for historical analysis."""
    
    def __init__(self):
        self.project_id = config.GCP_PROJECT_ID
        self.dataset_id = config.BIGQUERY_DATASET
        self.table_id = config.BIGQUERY_TABLE
        self.client = None
        
        if os.environ.get("FLASK_ENV") == "production":
            try:
                self.client = bigquery.Client()
                logging.info(f"BigQuery service initialized for {self.dataset_id}.{self.table_id}")
            except Exception as e:
                logging.error(f"Failed to initialize BigQuery client: {e}")

    def stream_simulation_data(self, data: dict):
        """
        Streams a single row of simulation data to BigQuery.
        Expected data schema: timestamp, phase, total_crowd, zone_densities (JSON)
        """
        if not self.client:
            return

        table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        
        try:
            errors = self.client.insert_rows_json(table_ref, [data])
            if errors:
                logging.error(f"Errors occurred while streaming to BigQuery: {errors}")
        except Exception as e:
            logging.error(f"Critical error streaming to BigQuery: {e}")

# Singleton instance
bigquery_service = BigQueryService()
