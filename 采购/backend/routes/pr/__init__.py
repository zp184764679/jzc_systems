# routes/pr/__init__.py
# PR模块蓝图注册

from flask import Blueprint, request, jsonify
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', '..'))
from shared.auth import verify_token


def add_auth_to_blueprint(bp):
    """为蓝图添加认证检查"""
    @bp.before_request
    def check_auth():
        # OPTIONS 请求跳过认证（CORS预检）
        if request.method == 'OPTIONS':
            return None

        # 检查 Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = verify_token(token)
            if payload:
                # 将用户信息存储到 request 对象
                request.current_user_id = payload.get('user_id')
                request.current_user_role = payload.get('role')
                return None

        # 回退检查 User-ID header
        user_id = request.headers.get('User-ID')
        if user_id:
            request.current_user_id = user_id
            request.current_user_role = request.headers.get('User-Role')
            return None

        # 未认证
        return jsonify({"error": "未授权：请先登录"}), 401


def register_pr_routes(app):
    """
    在 app.py 中调用此函数注册所有PR路由

    使用方式：
        from routes.pr import register_pr_routes
        register_pr_routes(app)
    """
    from .create import bp as create_bp
    from .query import bp as query_bp
    from .approval import bp as approval_bp
    from .search import bp as search_bp
    from .statistics import bp as statistics_bp

    # 为所有蓝图添加认证
    for bp in [create_bp, query_bp, approval_bp, search_bp, statistics_bp]:
        add_auth_to_blueprint(bp)

    # 注册所有蓝图，使用统一的url前缀
    app.register_blueprint(create_bp, url_prefix='/api/v1/pr')
    app.register_blueprint(query_bp, url_prefix='/api/v1/pr')
    app.register_blueprint(approval_bp, url_prefix='/api/v1/pr')
    app.register_blueprint(search_bp, url_prefix='/api/v1/pr')
    app.register_blueprint(statistics_bp, url_prefix='/api/v1/pr')

    # 注册别名路由：支持 POST /api/v1/prs（前端期望的端点）
    @app.route('/api/v1/prs', methods=['POST', 'OPTIONS'])
    def create_pr_alias():
        """别名路由：POST /api/v1/prs -> POST /api/v1/pr/prs"""
        # 检查认证
        if request.method != 'OPTIONS':
            auth_header = request.headers.get('Authorization')
            user_id = request.headers.get('User-ID')
            if not auth_header and not user_id:
                return jsonify({"error": "未授权：请先登录"}), 401
        from .create import create_pr
        return create_pr()