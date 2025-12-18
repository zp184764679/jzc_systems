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
            db_path = Path(__file__).parent.parent / 'eam.db'
            app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
            app.logger.info(f"Using SQLite database: {db_path}")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "eam-secret-key-2025")
    app.config['JSON_AS_ASCII'] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # CORS configuration - 安全修复：使用白名单替代通配符
    cors_origins_env = os.getenv('CORS_ORIGINS', '')
    if cors_origins_env:
        cors_origins = [o.strip() for o in cors_origins_env.split(',') if o.strip() and o.strip() != '*']
    else:
        cors_origins = []

    if not cors_origins:
        # 默认允许的域名（本地开发 + 生产环境）
        cors_origins = [
            'http://localhost:7200',   # EAM 前端
            'http://127.0.0.1:7200',
            'http://localhost:3001',   # Portal
            'http://127.0.0.1:3001',
            'https://jzchardware.cn',
        ]

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
    from .models import machine, base_data, maintenance, spare_parts, capacity

    # Create database tables if using SQLite (development mode)
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        with app.app_context():
            db.create_all()
            app.logger.info("Database tables created successfully")

    # Register blueprints
    from .routes import machines as machines_routes
    from .routes import integration as integration_routes
    from .routes import base_data as base_data_routes
    from .routes import maintenance as maintenance_routes
    from .routes import spare_parts as spare_parts_routes
    from .routes import capacity as capacity_routes
    app.register_blueprint(machines_routes.bp)
    app.register_blueprint(integration_routes.bp)
    app.register_blueprint(base_data_routes.bp)
    app.register_blueprint(maintenance_routes.bp)
    app.register_blueprint(spare_parts_routes.bp)
    app.register_blueprint(capacity_routes.bp)

    # Health check route
    @app.get("/ping")
    def ping():
        return {"message": "pong", "app": "EAM"}

    @app.get("/health")
    def health():
        try:
            # Test database connection
            db.session.execute(db.text("SELECT 1"))
            return jsonify({"status": "healthy", "service": "EAM", "database": "connected"})
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
