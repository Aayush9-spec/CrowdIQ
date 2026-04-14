import os
from flask import Flask, render_template
from flask_cors import CORS

from config import get_config
from models.venue import create_default_venue
from models.simulation import CrowdSimulation
from services.crowd_engine import CrowdEngine
from routes.api import api_bp, init_api
from routes.assistant import assistant_bp, init_assistant

def create_app():
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    # Enable CORS
    CORS(app)
    
    # Load config
    config = get_config()
    app.config.from_object(config)
    
    # Initialize Core Components
    venue = create_default_venue()
    simulation = CrowdSimulation(venue)
    crowd_engine = CrowdEngine(venue, simulation)
    
    # Initialize Blueprints and pass dependencies
    init_api(venue, simulation, crowd_engine)
    init_assistant(crowd_engine)
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(assistant_bp, url_prefix='/api/assistant')
    
    # Start Simulation
    simulation.start()
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/health')
    def health():
        return {"status": "up"}

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
