from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.routes.register import register_bp
from app.routes.auth import auth_bp
from app.routes.users import users_bp
from app.routes.hr_sync import hr_sync_bp
import os
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)

# 安全修复：强制要求 SECRET_KEY 环境变量
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    if os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG", "").lower() == "true":
        logger.warning("SECRET_KEY 未设置，使用开发临时密钥")
        secret_key = "dev-only-temp-secret-key-" + str(os.getpid())
    else:
        raise RuntimeError("SECRET_KEY 环境变量未设置（生产环境必须配置）")
app.secret_key = secret_key

# 安全修复：强制要求数据库凭证环境变量
DB_USER = os.getenv('MYSQL_USER')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('MYSQL_DATABASE', 'account')

if not DB_USER or not DB_PASSWORD:
    if os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG", "").lower() == "true":
        logger.warning("MYSQL_USER/MYSQL_PASSWORD 未设置，使用开发默认值")
        DB_USER = DB_USER or "app"
        DB_PASSWORD = DB_PASSWORD or "app"
    else:
        raise RuntimeError("MYSQL_USER 和 MYSQL_PASSWORD 环境变量必须设置（生产环境）")

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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

CORS(app, supports_credentials=True, origins=cors_origins_list, allow_headers=['Content-Type', 'Authorization'])

# Register blueprints
app.register_blueprint(register_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(hr_sync_bp)

@app.route('/health', methods=['GET'])
def health_check():
    return {'status': 'ok', 'service': 'account-management'}

# Database initialization and upgrade
with app.app_context():
    # Import and run database initialization
    from app.models.registration import init_db
    init_db()

    # Run database upgrade to add any missing columns
    try:
        from db_upgrade import upgrade_database
        upgrade_database()
        print("✅ Database schema is up to date")
    except Exception as e:
        print(f"⚠️  Database upgrade warning: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8004, debug=False)
