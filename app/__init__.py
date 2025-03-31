from flask import Flask, redirect, url_for, flash
from flask_jwt_extended import JWTManager, get_jwt
from pymongo import MongoClient
from config import config
from flask_socketio import SocketIO
import threading
import signal

jwt = JWTManager()
mongo_client = None
db = None
socketio = SocketIO()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", transports=["websocket"])
    
    global mongo_client, db
    mongo_client = MongoClient(app.config['MONGO_URI'])
    db = mongo_client["nnx"]
    
    # Safe CSRF token injection
    @app.context_processor
    def inject_csrf_token():
        from flask_jwt_extended import verify_jwt_in_request
        try:
            verify_jwt_in_request(optional=True)
            jwt_data = get_jwt()
            return dict(csrf_token=jwt_data.get("csrf"))
        except:
            return dict(csrf_token=None)
        
    @jwt.unauthorized_loader
    def custom_unauthorized_response(callback):
        flash("You must log in to access this page.", "danger")
        return redirect(url_for('auth.login'))
    
    from .auth import auth_bp
    from .routes import main_bp

    from app.Vehicle.VehicleBackend import vehicle_bp
    from app.Dashboard.DashboardBackend import dashboard_bp

    app.register_blueprint(vehicle_bp, url_prefix='/vehicle')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)



    def start_background_task():
        from app.distinctVehicleDataStore import run_distinct_vehicle_data_store
        distinctVehicleThread = threading.Thread(target=run_distinct_vehicle_data_store, args=(socketio,), daemon=True)
        distinctVehicleThread.start()

        from app.map_server import run_servers, signal_handler
        mapServerThread = threading.Thread(target=run_servers, daemon=True)
        mapServerThread.start()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    start_background_task()
    
    return app