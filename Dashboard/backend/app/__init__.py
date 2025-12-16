from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_marshmallow import Marshmallow
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
ma = Marshmallow()


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 1200,
        'pool_size': 10,
        'max_overflow': 20,
    }
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)

    # CORS configuration - use environment variable or defaults
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:6100,http://localhost:3000,https://jzchardware.cn').split(',')
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "supports_credentials": True
        }
    })

    # Register blueprints
    from app.routes.timeline import timeline_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.tasks import tasks_bp
    from app.routes.customer_portal import customer_portal_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(timeline_bp, url_prefix='/api/timeline')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(customer_portal_bp, url_prefix='/api/customer-portal')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')

    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'dashboard'}

    return app
