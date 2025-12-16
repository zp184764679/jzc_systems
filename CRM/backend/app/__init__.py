# backend/app/__init__.py
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    # Configure logging - use INFO level by default
    log_level = logging.DEBUG if os.getenv('FLASK_DEBUG', 'false').lower() == 'true' else logging.INFO
    logging.basicConfig(level=log_level)
    app.logger.setLevel(log_level)

    # Database configuration - support both MySQL and SQLite
    database_url = os.getenv("DATABASE_URL", "")

    if database_url:
        # Use explicit DATABASE_URL if provided
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Try MySQL first, fallback to SQLite
        db_user = os.getenv("MYSQL_USER", "")
        db_password = os.getenv("MYSQL_PASSWORD", os.getenv("MYSQL_ROOT_PASSWORD", ""))
        db_host = os.getenv("DB_HOST", "localhost")
        db_name = os.getenv("MYSQL_DATABASE", "cncplan")

        if db_user and db_password:
            # MySQL configuration
            app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}?charset=utf8mb4"
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True, "pool_recycle": 280}
        else:
            # SQLite fallback for development
            db_path = Path(__file__).parent.parent / 'crm.db'
            app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
            app.logger.info(f"Using SQLite database: {db_path}")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "crm-secret-key-2025")
    app.config['JSON_AS_ASCII'] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # CORS configuration
    cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
    CORS(app,
         resources={r"/api/*": {"origins": cors_origins}},
         supports_credentials=True,
         methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "User-ID", "User-Role"])

    @app.before_request
    def handle_options():
        if request.method == "OPTIONS":
            return make_response(("", 204))

    # Clean up database session
    @app.teardown_request
    def cleanup_request(exc=None):
        try:
            if exc:
                db.session.rollback()
        finally:
            db.session.remove()

    # Import models
    from .models import customer, core, base_data, sales, contract

    # Create database tables if using SQLite (development mode)
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        with app.app_context():
            db.create_all()
            app.logger.info("Database tables created successfully")

    # Register blueprints
    from .routes import customers, orders, integration, base_data as base_data_routes, auth
    from .routes.opportunities import opportunities_bp
    from .routes.follow_ups import follow_ups_bp
    from .routes.contracts import contracts_bp
    from .routes.customer_grades import customer_grades_bp
    from .routes.customer_reports import bp as customer_reports_bp

    app.register_blueprint(customers.bp)
    app.register_blueprint(orders.bp)
    app.register_blueprint(integration.bp)
    app.register_blueprint(base_data_routes.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(opportunities_bp)
    app.register_blueprint(follow_ups_bp)
    app.register_blueprint(contracts_bp)
    app.register_blueprint(customer_grades_bp)
    app.register_blueprint(customer_reports_bp)

    # Health check route
    @app.get("/ping")
    def ping():
        return {"message": "pong", "app": "CRM"}

    @app.get("/health")
    def health():
        try:
            # Test database connection
            db.session.execute(db.text("SELECT 1"))
            return jsonify({"status": "healthy", "service": "CRM", "database": "connected"})
        except Exception as e:
            return jsonify({"status": "unhealthy", "error": str(e)}), 500

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not Found", "path": request.path}), 404
        return e

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.exception("500 at %s %s", request.method, request.path)
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal Server Error"}), 500
        return e

    return app
