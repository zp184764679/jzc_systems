"""
TDM 产品技术标准管理系统 - Flask 应用入口
"""
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask, jsonify
from flask_cors import CORS
from config import get_config
from models import db

# 导入路由蓝图
from routes import (products_bp, technical_specs_bp, inspection_bp, process_docs_bp, files_bp,
                    materials_bp, processes_bp, drawings_bp)


def create_app():
    """创建 Flask 应用"""
    app = Flask(__name__)

    # 加载配置
    config = get_config()
    app.config.from_object(config)

    # 初始化 CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": config.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # 初始化数据库
    db.init_app(app)

    # 注册蓝图
    app.register_blueprint(products_bp, url_prefix='/api')
    app.register_blueprint(technical_specs_bp, url_prefix='/api')
    app.register_blueprint(inspection_bp, url_prefix='/api')
    app.register_blueprint(process_docs_bp, url_prefix='/api')
    app.register_blueprint(files_bp, url_prefix='/api')
    # 共享数据蓝图（材料库、工艺库、图纸）
    app.register_blueprint(materials_bp, url_prefix='/api')
    app.register_blueprint(processes_bp, url_prefix='/api')
    app.register_blueprint(drawings_bp, url_prefix='/api')

    # 健康检查
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'service': 'TDM Backend',
            'version': '1.0.0'
        })

    # 根路由
    @app.route('/')
    def index():
        return jsonify({
            'service': 'TDM - Technical Data Management',
            'version': '1.0.0',
            'description': '产品技术标准管理系统'
        })

    # 创建数据库表
    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8009))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    print(f"TDM Backend starting on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug)
