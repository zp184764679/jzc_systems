import os
from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化扩展
    db.init_app(app)
    cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    # 注册蓝图
    from routes.shipments import shipments_bp
    from routes.addresses import addresses_bp
    from routes.requirements import requirements_bp
    from routes.integration import integration_bp
    from routes.base_data import bp as base_data_bp
    from routes.auth import bp as auth_bp

    app.register_blueprint(shipments_bp, url_prefix='/api')
    app.register_blueprint(addresses_bp, url_prefix='/api')
    app.register_blueprint(requirements_bp, url_prefix='/api')
    app.register_blueprint(integration_bp, url_prefix='/api')
    app.register_blueprint(base_data_bp)
    app.register_blueprint(auth_bp)

    # 创建数据库表
    with app.app_context():
        db.create_all()
        app.logger.info("Database tables created successfully")

    @app.route('/api/health')
    def health_check():
        return {'status': 'ok', 'service': 'SHM - 出货管理系统'}

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=Config.PORT, debug=True)
