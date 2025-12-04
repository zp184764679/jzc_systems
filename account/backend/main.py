from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.routes.register import register_bp
from app.routes.auth import auth_bp
from app.routes.users import users_bp
from app.routes.hr_sync import hr_sync_bp
import os

app = Flask(__name__)

# Secret key for sessions
app.secret_key = os.getenv('SECRET_KEY', 'jzc-hardware-account-management-secret-key-2025')

# Database configuration
DB_USER = os.getenv('MYSQL_USER', 'app')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD', 'app')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('MYSQL_DATABASE', 'account')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Enable CORS with credentials
CORS(app, supports_credentials=True, origins=['*'], allow_headers=['Content-Type', 'Authorization'])

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
