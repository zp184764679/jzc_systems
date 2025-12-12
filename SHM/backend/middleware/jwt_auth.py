"""
JWT Authentication Middleware for SHM System
安全修复：添加认证装饰器
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
        token = _get_token_from_request()

        if not token:
            return jsonify({'error': '缺少认证token', 'success': False}), 401

        # 验证token
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Token无效或已过期', 'success': False}), 401

        # 将用户信息添加到request
        request.user = payload
        return f(*args, **kwargs)

    return decorated_function
