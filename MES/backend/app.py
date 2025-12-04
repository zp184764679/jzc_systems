# MES制造执行系统 - 主应用
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from database import db

load_dotenv()

app = Flask(__name__)
# CORS配置 - 从环境变量读取允许的域名
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

# 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'SQLALCHEMY_DATABASE_URI',
    'sqlite:///./mes_system.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 数据库连接池配置
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,           # 连接池大小
    'max_overflow': 20,        # 超出pool_size后最多可创建的连接数
    'pool_recycle': 1200,      # 连接回收时间（秒）
    'pool_pre_ping': True,     # 每次取连接时检查连接是否有效
}

db.init_app(app)

# 导入模型
from models.work_order import WorkOrder
from models.production_record import ProductionRecord
from models.quality_inspection import QualityInspection
from models import base_data

# 导入路由
from routes.work_order_routes import work_order_bp
from routes.production_routes import production_bp
from routes.dashboard_routes import dashboard_bp
from routes.integration_routes import integration_bp
from routes.base_data_routes import bp as base_data_bp

# 注册蓝图
app.register_blueprint(work_order_bp, url_prefix='/api/work-orders')
app.register_blueprint(production_bp, url_prefix='/api/production')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(integration_bp, url_prefix='/api/integration')
app.register_blueprint(base_data_bp)


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'MES',
        'version': '1.0.0'
    })


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'MES - Manufacturing Execution System',
        'version': '1.0.0',
        'endpoints': {
            'work_orders': '/api/work-orders',
            'production': '/api/production',
            'dashboard': '/api/dashboard',
            'integration': '/api/integration',
            'health': '/api/health'
        }
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8007, debug=True)
