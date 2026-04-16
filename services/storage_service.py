import os
import logging
from google.cloud import storage
from config import get_config

config = get_config()

class StorageService:
    """Service to handle interactions with Google Cloud Storage."""
    
    def __init__(self):
        self.bucket_name = config.GCP_STORAGE_BUCKET
        self.client = None
        
        # Only initialize if in production or if keys are provided
        if os.environ.get("FLASK_ENV") == "production":
            try:
                self.client = storage.Client()
                logging.info(f"Storage service initialized for bucket: {self.bucket_name}")
            except Exception as e:
                logging.error(f"Failed to initialize Storage client: {e}")

    def get_public_url(self, blob_name: str) -> str:
        """Returns the public URL for a given blob name."""
        if not self.client:
            # Fallback for local development
            return f"/static/assets/mocks/{blob_name}"
            
        return f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"

    def list_assets(self, prefix: str = ""):
        """Lists files in the storage bucket with a given prefix."""
        if not self.client:
            return ["stadium_map.png", "logo_light.svg", "zone_heatmaps/"]
            
        try:
            bucket = self.client.bucket(self.bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            logging.error(f"Error listing storage assets: {e}")
            return []

# Singleton instance
storage_service = StorageService()
