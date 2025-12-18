# app.py
# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash  # noqa: F401
from extensions import db, migrate
from models.user import User
from models.pr import PR  # noqa: F401
from models.pr_item import PRItem  # noqa: F401
import os
from dotenv import load_dotenv
from importlib import import_module
from flask_cors import CORS
import inspect
import traceback
import logging
import models  # noqa
from extensions import db, migrate, init_celery  # ← 补上 init_celery

# =========================
# 加载环境变量 & 初始化 Flask
# =========================
load_dotenv()
app = Flask(__name__)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Secret
SECRET = os.getenv("APP_SECRET", "dev-secret")
app.config["SECRET_KEY"] = SECRET

# =========================
# SQLAlchemy 配置（含稳连接）
# =========================
# 数据库配置 - 必须从环境变量获取
db_uri = os.getenv("SQLALCHEMY_DATABASE_URI")
if not db_uri:
    logger.error("SQLALCHEMY_DATABASE_URI 环境变量未设置，请检查 .env 文件")
    raise RuntimeError("SQLALCHEMY_DATABASE_URI 环境变量未设置")
app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 防止闲置 "Lost connection" 的关键配置
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,    # 借出前先 ping，死连接自动重建
    "pool_recycle": 1200,     # 20 分钟回收重建，避免开 NAT 30 分钟空闲清理
    "pool_size": 10,          # 常驻连接数（按并发调整）
    "max_overflow": 20,       # 高峰期额外连接
    "connect_args": {
        "connect_timeout": 10,
        "read_timeout": 60,
        "write_timeout": 60,
    },
}

# 初始化数据库 & 迁移
db.init_app(app)
migrate.init_app(app, db)
celery = init_celery(app)  # ← 新增：让 Celery 任务有 Flask 应用上下文

# =========================
# 初始化共享认证数据库
# =========================
try:
    from shared.auth import init_auth_db
    init_auth_db()
    logger.info("✅ 共享认证数据库已初始化")
except Exception as e:
    logger.warning(f"⚠️ 共享认证数据库初始化失败: {e}")

# =========================
# CORS 配置
# =========================
CORS(
    app,
    origins=[
        r"http://localhost:\d+",  # 本地开发
        r"http://127.0.0.1:\d+",  # 本地开发
        r"http://192\.168\.\d+\.\d+:\d+",  # 内网开发
        "http://61.145.212.28:3000",  # 生产服务器
        "http://61.145.212.28:9000",  # 生产服务器
        "http://61.145.212.28",  # 生产服务器
        "https://jzchardware.cn",  # 生产域名
    ],
    supports_credentials=True,
    allow_headers=[
        "Content-Type",
        "Authorization",
        "User-ID",
        "User-Role",
        "Supplier-ID"
    ],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    max_age=3600
)

# =========================
# 全局 OPTIONS 预检处理（确保CORS成功）
# =========================
@app.before_request
def handle_preflight():
    """处理所有OPTIONS预检请求，确保CORS响应正确"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, User-ID, User-Role, Supplier-ID")
        response.headers.add("Access-Control-Max-Age", "3600")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 204

# =========================
# 认证路由图（登录/注册/获取当前用户）
# =========================
# ✅ 认证功能已移至 routes/auth_routes.py
# auth_bp = Blueprint('auth', __name__)
# 
# @auth_bp.route('/login', methods=['POST', 'OPTIONS'])
# def login():
#     if request.method == 'OPTIONS':
#         response = jsonify({})
#         response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
#         response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
#         response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, User-ID, User-Role")
#         response.headers.add("Access-Control-Max-Age", "3600")
#         return response, 204
#     
#     data = request.get_json(silent=True) or {}
#     email = data.get('email')
#     password = data.get('password')
# 
#     if not email or not password:
#         return jsonify({"error": "请提供完整的登录信息"}), 400
# 
#     user = User.query.filter_by(email=email).first()
#     if not user or not user.check_password(password):
#         return jsonify({"error": "账户或密码错误"}), 400
# 
#     if user.status != 'approved':
#         return jsonify({"error": "用户尚未通过管理员审批"}), 403
# 
#     return jsonify({
#         "message": "登录成功", 
#         "user_id": user.id, 
#         "name": user.username,
#         "email": user.email,
#         "role": user.role,
#         "status": user.status,
#         "department": user.department or "",
#         "employee_no": user.employee_no or "",
#         "phone": user.phone or "",
#         "created_at": user.created_at.isoformat() if user.created_at else None
#     }), 200
# 
# @auth_bp.route('/register', methods=['POST', 'OPTIONS'])
# def register():
#     if request.method == 'OPTIONS':
#         response = jsonify({})
#         response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
#         response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
#         response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, User-ID, User-Role")
#         response.headers.add("Access-Control-Max-Age", "3600")
#         return response, 204
#     
#     data = request.get_json(silent=True) or {}
#     username = data.get('username')
#     email = data.get('email')
#     password = data.get('password')
# 
#     if not username or not email or not password:
#         return jsonify({"error": "请提供完整的注册信息"}), 400
# 
#     existing_user = User.query.filter_by(email=email).first()
#     if existing_user:
#         return jsonify({"error": "该邮箱已被注册"}), 400
# 
#     new_user = User.create_user(
#         username=username,
#         email=email,
#         password=password,
#         status='pending'
#     )
# 
#     db.session.add(new_user)
#     try:
#         db.session.commit()
#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"保存用户信息失败: {e}")
#         return jsonify({"error": "保存用户信息失败"}), 500
# 
#     return jsonify({"message": "注册成功，待管理员审批"}), 201
# 
# @auth_bp.route('/me', methods=['GET', 'OPTIONS'])
# def get_current_user():
#     if request.method == 'OPTIONS':
#         response = jsonify({})
#         response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
#         response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
#         response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, User-ID, User-Role")
#         response.headers.add("Access-Control-Max-Age", "3600")
#         return response, 204
#     
#     try:
#         user_id = request.headers.get('User-ID')
#         if not user_id:
#             return jsonify({"error": "未提供用户ID"}), 400
# 
#         user = User.query.get(int(user_id))
#         if not user:
#             return jsonify({"error": "用户未找到"}), 404
# 
#         return jsonify({
#             'id': user.id,
#             'name': user.username,
#             'email': user.email,
#             'role': user.role,
#             'status': user.status,
#             'department': user.department or "",
#             'employee_no': user.employee_no or "",
#             'phone': user.phone or "",
#             'created_at': user.created_at.isoformat() if user.created_at else None
#         }), 200
#     except Exception as e:
#         logger.error(f"获取用户信息错误: {str(e)}")
#         return jsonify({"error": "服务器内部错误"}), 500
# 
# # =========================
# # 默认管理员（幂等确保）
# # =========================
# def create_admin_user():
#     """
#     幂等：如无则创建，已有则确保角色为 admin & 状态 approved
#     账户：184764679@qq.com / 密码：exak472008
#     """
#     try:
#         admin_user = User.query.filter_by(email='184764679@qq.com').first()
#         if not admin_user:
#             admin_user = User.create_user(
#                 username='Admin',
#                 email='184764679@qq.com',
#                 password="exak472008",
#                 status='approved'
#             )
#             admin_user.role = 'super_admin'
#             db.session.add(admin_user)
#             db.session.commit()
#             logger.info("✅ 默认管理员已创建")
#         else:
#             changed = False
#             if admin_user.role != 'super_admin':
#                 admin_user.role = 'super_admin'
#                 changed = True
#             if admin_user.status != 'approved':
#                 admin_user.status = 'approved'
#                 changed = True
#             if changed:
#                 db.session.commit()
#                 logger.info("✅ 已确保现有用户为管理员且已审批")
#             else:
#                 logger.info("ℹ️ 管理员已存在且状态正确，无需创建")
#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"创建/确保管理员时发生错误：{e}")
# 
# # 方式 2：应用启动后首次请求时自动确保管理员（Flask 3.x 兼容版）
# _admin_ensured = False  # 全局标志，防止多次重复执行
# 
# @app.before_request
# def _ensure_admin_once():
#     """
#     Flask 3.x 没有 before_first_request，因此改成 before_request + 全局标志控制。
#     多进程下每个进程会执行一次，但 create_admin_user() 是幂等的，不会重复插入。
#     """
#     global _admin_ensured
#     if not _admin_ensured:
#         try:
#             create_admin_user()
#         except Exception as e:
#             logger.warning(f"⚠️ 首次请求时自动创建管理员失败：{e}")
#         finally:
#             _admin_ensured = True
# 
# =========================
# 自动注册 routes/ 目录下蓝图
# =========================
def register_blueprints(app):
    """
    自动从 routes/ 目录加载 *_routes.py 模块，并注册其中的 Blueprint：
    - 优先使用模块内的 BLUEPRINTS 列表（若存在）
    - 否则自动发现模块内所有 Blueprint 实例（变量名不限）
    - 如模块仅导出 bp 变量，也兼容
    - 支持模块级 URL_PREFIX（未提供则默认 /api/v1）
    """
    router_dir = os.path.join(os.path.dirname(__file__), 'routes')
    logger.info(f"[Blueprint] Checking directory: {router_dir}")

    if not os.path.isdir(router_dir):
        logger.info("[Blueprint] routes/ 目录不存在，跳过自动注册")
        return

    init_py = os.path.join(router_dir, '__init__.py')
    if not os.path.exists(init_py):
        logger.warning("[Blueprint] 缺少 routes/__init__.py，将自动创建一个空文件。")
        try:
            with open(init_py, 'w', encoding='utf-8') as f:
                f.write("# routes package marker\n")
        except Exception as e:
            logger.error(f"[Blueprint] 创建 __init__.py 失败：{e}")

    registered_names = set()

    for filename in os.listdir(router_dir):
        if filename in ('__init__.py', '__pycache__'):
            continue
        if not filename.endswith('_routes.py'):
            continue

        module_name = os.path.splitext(filename)[0]
        module_path = f'routes.{module_name}'
        try:
            module = import_module(module_path)
            logger.info(f"[Blueprint] Loaded module: {module_path}")

            url_prefix = getattr(module, 'URL_PREFIX', '/api/v1')

            # ① 显式列表优先
            bp_list = getattr(module, 'BLUEPRINTS', None)
            candidates = []
            if isinstance(bp_list, (list, tuple)):
                candidates = [bp for bp in bp_list if isinstance(bp, Blueprint)]

            # ② 没有 BLUEPRINTS 就自动发现所有 Blueprint 实例
            if not candidates:
                for name, obj in inspect.getmembers(module):
                    if isinstance(obj, Blueprint):
                        candidates.append(obj)

            # ③ 兼容老式导出方式：bp
            if not candidates and hasattr(module, 'bp') and isinstance(module.bp, Blueprint):
                candidates = [module.bp]

            if not candidates:
                logger.warning(f"[Blueprint] No Blueprint found in {module_path}")
                continue

            for bp in candidates:
                if bp.name in registered_names:
                    logger.warning(f"[Blueprint] Skip duplicated blueprint: {bp.name}")
                    continue
                app.register_blueprint(bp, url_prefix=url_prefix)
                registered_names.add(bp.name)
                logger.info(f"[Blueprint] ✅ Registered: {bp.name} @ {url_prefix} (from {module_path})")

        except Exception as e:
            logger.error(f"[Blueprint] Error in {module_path}: {e}\n{traceback.format_exc()}")
# 
# # 手动注册认证蓝图 & 自动注册业务蓝图
# app.register_blueprint(auth_bp, url_prefix='/api/v1')
# logger.info(f"[Blueprint] ✅ Registered: {auth_bp.name} @ /api/v1 (manual)")

register_blueprints(app)

# ✅ 注册 PR 模块分包路由
try:
    from routes.pr import register_pr_routes
    register_pr_routes(app)
    logger.info("[Blueprint] ✅ Registered: PR module routes @ /api/v1/pr")
except ImportError as e:
    logger.warning(f"[Blueprint] ⚠️ PR module import failed: {e}")
except Exception as e:
    logger.error(f"[Blueprint] ❌ PR module registration failed: {e}")
    
# ✅ 注册 Supplier Admin 模块分包路由（新增）
try:
    from routes.supplier_admin import BLUEPRINTS
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)
    logger.info("[Blueprint] ✅ Registered: Supplier Admin module routes")
except ImportError as e:
    logger.warning(f"[Blueprint] ⚠️ Supplier Admin module import failed: {e}")
except Exception as e:
    logger.error(f"[Blueprint] ❌ Supplier Admin module registration failed: {e}")
# =========================
# 静态文件服务 - 提供 uploads 文件夹访问
# =========================
from flask import send_from_directory

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """
    提供uploads文件夹中的文件
    支持按年月组织的文件夹结构，例如: /uploads/2025/01/xxxxx.pdf
    """
    uploads_folder = os.path.join(app.root_path, 'uploads')
    return send_from_directory(uploads_folder, filename)

# =========================
# 健康检查 & 根路径
# =========================
@app.route('/health', methods=['GET', 'OPTIONS'])
@app.route('/api/health', methods=['GET', 'OPTIONS'])  # 兼容启动器的健康检查路径
def health_check():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, User-ID, User-Role")
        response.headers.add("Access-Control-Max-Age", "3600")
        return response, 204
    return jsonify({"status": "healthy", "message": "Server is running"}), 200

@app.route('/')
def index():
    return jsonify({"message": "采购系统 API", "version": "1.0"})

# =========================
# 全局错误处理
# =========================
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "请求的资源不存在"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"服务器内部错误: {error}")
    return jsonify({"error": "服务器内部错误"}), 500

# =========================
# 本地直跑
# =========================
if __name__ == '__main__':
    with app.app_context():
        try:
            # 创建所有数据库表
            db.create_all()
            logger.info("✅ 数据库表已初始化")

            # 确保管理员存在（已禁用自动创建）
            # create_admin_user()
        except Exception as e:
            logger.error(f"启动时初始化错误: {e}")

    logger.info("✅ DB pool initialized with: pool_pre_ping=True, pool_recycle=1200, pool_size=10, max_overflow=20")
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug, port=port, host='0.0.0.0')








