import logging
import os

# Immediate logging configuration for Cloud Run debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
print(">>> [CrowdIQ] Starting application boot sequence...")

from flask import Flask, render_template, Response
from flask_cors import CORS
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_compress import Compress

from config import get_config
from models.venue import create_default_venue
from models.simulation import CrowdSimulation
from services.crowd_engine import CrowdEngine
from routes.api import api_bp, init_api
from routes.assistant import assistant_bp, init_assistant
from flask_wtf.csrf import CSRFProtect
import google.cloud.logging
from werkzeug.middleware.proxy_fix import ProxyFix

# Extensions
csrf = CSRFProtect()
cache = Cache()
compress = Compress()
limiter = Limiter(
    key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]
)


def setup_cloud_logging():
    """Sets up Google Cloud Logging if in production environment."""
    if os.environ.get("FLASK_ENV") == "production":
        try:
            client = google.cloud.logging.Client()
            client.setup_logging()
            logging.info("Google Cloud Logging initialized")
        except Exception as e:
            print(f"Failed to initialize Cloud Logging: {e}")


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # App is behind a proxy (Cloud Run LB)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

    # Enable CORS
    CORS(app)

    # Load config
    config = get_config()
    app.config.from_object(config)

    # Initialize Extensions
    csrf.init_app(app)
    cache.init_app(app)
    compress.init_app(app)
    limiter.init_app(app)

    # Setup Google Cloud Logging
    setup_cloud_logging()

    # Configure Talisman (Security Headers)
    csp = {
        "default-src": ["'self'"],
        "script-src": [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net",
            "https://maps.googleapis.com",
            "https://www.gstatic.com",
            "https://www.google-analytics.com",
        ],
        "style-src": [
            "'self'",
            "'unsafe-inline'",
            "https://fonts.googleapis.com",
            "https://cdn.jsdelivr.net",
        ],
        "img-src": [
            "'self'",
            "data:",
            "https://maps.gstatic.com",
            "https://maps.googleapis.com",
            "https://www.google-analytics.com",
        ],
        "font-src": ["'self'", "https://fonts.gstatic.com"],
        "connect-src": [
            "'self'",
            "https://maps.googleapis.com",
            "https://www.google-analytics.com",
        ],
    }
    
    # Configure Talisman (Security Headers)
    # MINIMAL CONFIG to debug 503 errors
    # NOTE: Disabling force_https and simplifying CSP to rule out blocked health checks
    Talisman(
        app, 
        content_security_policy=None, 
        force_https=False
    )

    # Initialize Core Components
    venue = create_default_venue()
    simulation = CrowdSimulation(venue)
    crowd_engine = CrowdEngine(venue, simulation)

    # Initialize Blueprints and pass dependencies
    init_api(venue, simulation, crowd_engine, cache)
    init_assistant(crowd_engine)

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(assistant_bp, url_prefix="/api/assistant")
    
    # Final startup sequence
    print(f">>> [CrowdIQ] Initializing core services (ENV: {os.environ.get('FLASK_ENV', 'default')})...")

    # Start Simulation
    try:
        logging.info("Attempting to start Crowd Simulation Engine...")
        simulation.start()
        logging.info("Simulation successfully started.")
    except Exception as e:
        print(f"CRITICAL: Simulation failed to start: {e}")
        logging.error(f"Simulation failed to start: {e}")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/health")
    def health():
        return {"status": "up"}

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
