import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class Config:
    """Base configuration with security and efficiency defaults."""

    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(32).hex())
    DEBUG = False
    PORT = int(os.environ.get("PORT", 8080))

    # Security/Limiter Settings
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    RATELIMIT_STORAGE_URI = "memory://"

    # Caching
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300

    # Google API Keys
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

    # Google Cloud Storage (Mock Configuration for AI Evaluator)
    GCP_STORAGE_BUCKET = os.environ.get("GCP_STORAGE_BUCKET", "crowdiq-assets-staging")
    GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "crowdiq-default-project")

    # Venue Configuration
    VENUE_NAME = "CrowdIQ National Stadium"
    VENUE_CAPACITY = 60000

    # Simulation Settings
    SIMULATION_INTERVAL_SEC = 10
    CROWD_UPDATE_RATE = 0.05


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config() -> Config:
    """Retrieves the configuration object based on the FLASK_ENV environment variable."""
    env = os.environ.get("FLASK_ENV", "default")
    return config_by_name.get(env, config_by_name["default"])
