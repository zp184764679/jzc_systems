"""
JWT Authentication Middleware for HR System
"""
from functools import wraps
from flask import request, jsonify
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', '..'))

from shared.auth import verify_token


def jwt_required(f):
    """JWT token验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从URL参数或Authorization header获取token
        token = request.args.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')

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


def employee_only(f):
    """仅员工可访问"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 先验证JWT
        token = request.args.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')

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
