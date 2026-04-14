import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'crowdiq-secret-key-12345')
    DEBUG = False
    PORT = int(os.environ.get('PORT', 8080))
    
    # Google API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    
    # Venue Configuration
    VENUE_NAME = "CrowdIQ National Stadium"
    VENUE_CAPACITY = 60000
    
    # Simulation Settings
    SIMULATION_INTERVAL_SEC = 10
    CROWD_UPDATE_RATE = 0.05  # Percentage of crowd that moves every update

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

# Mapping of environment to config object
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    env = os.environ.get('FLASK_ENV', 'default')
    return config_by_name.get(env, config_by_name['default'])
