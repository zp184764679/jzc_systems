# CRITICAL: Load .env BEFORE any other imports that may use shared.auth
# This ensures JWT_SECRET_KEY is available when jwt_utils.py is imported
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化扩展
    db.init_app(app)

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

    # 注册蓝图
    from routes.shipments import shipments_bp
    from routes.addresses import addresses_bp
    from routes.requirements import requirements_bp
    from routes.integration import integration_bp
    from routes.base_data import bp as base_data_bp
    from routes.auth import bp as auth_bp
    from routes.logistics import logistics_bp
    from routes.rma import rma_bp
    from routes.reports import reports_bp

    app.register_blueprint(shipments_bp, url_prefix='/api')
    app.register_blueprint(addresses_bp, url_prefix='/api')
    app.register_blueprint(requirements_bp, url_prefix='/api')
    app.register_blueprint(integration_bp, url_prefix='/api')
    app.register_blueprint(logistics_bp, url_prefix='/api')
    app.register_blueprint(rma_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/api')
    app.register_blueprint(base_data_bp)
    app.register_blueprint(auth_bp)

    # 创建数据库表
    with app.app_context():
        db.create_all()
        app.logger.info("Database tables created successfully")

    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'service': 'SHM - 出货管理系统'}

    return app

if __name__ == '__main__':
    app = create_app()
    # 安全修复：从环境变量读取 debug 模式，默认关闭
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"SHM Backend starting on port {Config.PORT}, debug={debug_mode}")
    app.run(host='0.0.0.0', port=Config.PORT, debug=debug_mode)
