import sys
import os as _setup_os
sys.path.insert(0, _setup_os.path.abspath(_setup_os.path.join(_setup_os.path.dirname(__file__), "../..", "..")))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Database configuration - support both MySQL and SQLite
    db_uri = os.getenv('SQLALCHEMY_DATABASE_URI', None)

    if db_uri:
        # Use explicit database URI if provided
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    else:
        # Check if we should use SQLite (for development) or MySQL
        use_sqlite = os.getenv('USE_SQLITE', 'true').lower() == 'true'

        if use_sqlite:
            # Use SQLite for development
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./hr_system.db'
        else:
            # Use MySQL
            db_host = os.getenv('DB_HOST', 'localhost')
            db_user = os.getenv('MYSQL_USER', 'root')
            db_password = os.getenv('MYSQL_PASSWORD', 'root')
            db_name = os.getenv('MYSQL_DATABASE', 'hr_system')
            app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Only use connection pooling for MySQL
    if 'mysql' in app.config['SQLALCHEMY_DATABASE_URI']:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
            'pool_size': 10,
            'max_overflow': 20
        }

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)

    # 安全修复：CORS 配置 - 仅允许已知域名
    cors_origins = os.getenv('CORS_ORIGINS', '')
    if cors_origins:
        cors_origins_list = [o.strip() for o in cors_origins.split(',') if o.strip()]
    else:
        cors_origins_list = [
            'http://localhost:3000',
            'http://localhost:5173',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:5173',
            'http://61.145.212.28:3000',
            'http://61.145.212.28',
            'https://jzchardware.cn:8888',
            'https://jzchardware.cn',
        ]

    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins_list,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # Database cleanup handlers
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Clean up database sessions after each request"""
        db.session.remove()

    # Temporarily disabled - will enable after database credentials are confirmed
    # @app.before_request
    # def before_request():
    #     """Ensure database connection is alive before each request"""
    #     try:
    #         db.session.execute('SELECT 1')
    #     except Exception:
    #         db.session.rollback()

    # Register blueprints
    from app.routes import employees_bp, base_data_bp
    from app.routes.auth import auth_bp
    from app.routes.register import register_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(register_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(base_data_bp)

    # Create tables
    with app.app_context():
        db.create_all()

    # Initialize authentication database
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', '..'))
        from shared.auth import init_auth_db
        init_auth_db()
        print("✅ 认证数据库初始化成功")
    except Exception as e:
        print(f"⚠️ 认证数据库初始化失败: {e}")

    @app.route('/')
    def index():
        return {'message': 'HR System Backend API', 'status': 'running'}

    @app.route('/health')
    def health():
        try:
            # Check database connection
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            return {'status': 'healthy', 'database': 'connected'}
        except Exception as e:
            return {'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}, 500

    return app
