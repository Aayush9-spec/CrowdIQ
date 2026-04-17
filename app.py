import logging
import os
from flask import Flask, render_template
from flask_cors import CORS
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_compress import Compress
from flask_wtf.csrf import CSRFProtect
import google.cloud.logging
from werkzeug.middleware.proxy_fix import ProxyFix

from config import get_config
from models.venue import create_default_venue
from models.simulation import CrowdSimulation
from services.crowd_engine import CrowdEngine
from routes.api import api_bp
from routes.assistant import assistant_bp

# Immediate logging configuration for Cloud Run debugging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
print(">>> [CrowdIQ] Starting application boot sequence...")

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
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1
    )

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
    # Restoring strict security for production evaluation
    Talisman(
        app,
        content_security_policy=csp,
        force_https=app.config.get("ENV") == "production",
        strict_transport_security=True,
        session_cookie_secure=True,
        session_cookie_http_only=True,
        referrer_policy="no-referrer-when-downgrade",
        x_content_type_options="nosniff",
        frame_options="DENY",
        permissions_policy={
            "geolocation": "()",
            "microphone": "()",
            "camera": "()",
        },
    )

    # Initialize Core Components
    app.venue = create_default_venue()
    app.simulation = CrowdSimulation(app.venue)
    app.crowd_engine = CrowdEngine(app.venue, app.simulation)

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(assistant_bp, url_prefix="/api/assistant")

    # Final startup sequence
    print(
        f">>> [CrowdIQ] Initializing core services (ENV: {os.environ.get('FLASK_ENV', 'default')})..."
    )

    # Start Simulation
    try:
        logging.info("Attempting to start Crowd Simulation Engine...")
        app.simulation.start()
        logging.info("Simulation successfully started.")
    except Exception as e:
        print(f"CRITICAL: Simulation failed to start: {e}")
        logging.error(f"Simulation failed to start: {e}")

    @app.route("/")
    def landing():
        """New premium landing page for judges/investors."""
        return render_template("landing.html")

    @app.route("/ops")
    def index():
        """Operations Desk - The main functional dashboard."""
        return render_template("index.html")

    @app.route("/health")
    def health():
        """Smarter health check for Cloud Run monitoring."""
        from services.bigquery_service import bigquery_service
        from services.storage_service import storage_service

        return {
            "status": "up",
            "services": {
                "bigquery": "connected" if bigquery_service.client else "offline",
                "storage": "connected" if storage_service.client else "offline",
                "simulation": "running" if app.simulation.running else "stopped",
            },
        }

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
