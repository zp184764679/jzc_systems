"""
JWT Authentication Middleware for HR System
安全修复：移除 URL 参数获取 token，添加管理员权限检查
"""
from functools import wraps
from flask import request, jsonify
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', '..'))

from shared.auth import verify_token


def _get_token_from_request():
    """安全地从请求中获取 token（仅从 Header 或 Cookie）"""
    # 优先从 Cookie 获取
    token = request.cookies.get('access_token')

    # 如果 Cookie 没有，从 Authorization header 获取
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]

    return token


def jwt_required(f):
    """JWT token验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 安全修复：仅从 Header/Cookie 获取 token，不从 URL 参数
        token = _get_token_from_request()

        if not token:
            return jsonify({'error': '缺少认证token'}), 401

        # 验证token
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Token无效或已过期'}), 401

        # 将用户信息添加到request
        request.user = payload
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """管理员权限装饰器 - 需要 admin 或 super_admin 角色"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = _get_token_from_request()

        if not token:
            return jsonify({'error': '缺少认证token'}), 401

        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Token无效或已过期'}), 401

        # 检查是否为管理员
        role = payload.get('role', '')
        if role not in ('admin', 'super_admin'):
            return jsonify({'error': '权限不足：需要管理员权限'}), 403

        request.user = payload
        return f(*args, **kwargs)

    return decorated_function


def employee_only(f):
    """仅员工可访问"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = _get_token_from_request()

        if not token:
            return jsonify({'error': '缺少认证token'}), 401

        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Token无效或已过期'}), 401

        # 检查是否为员工
        if payload.get('user_type') != 'employee':
            return jsonify({'error': '仅员工可访问'}), 403

        request.user = payload
        return f(*args, **kwargs)

    return decorated_function
