# backend/app/routes/auth.py
"""
Authentication routes for SCM system
"""
from flask import Blueprint, request, jsonify
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.auth import verify_token

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/sso-login', methods=['POST', 'OPTIONS'])
def sso_login():
    """SSO登录 - 接收Portal传来的token"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "success"}), 200

    try:
        # 从请求体或URL参数获取token
        data = request.get_json(silent=True) or {}
        token = data.get('token') or request.args.get('token')

        if not token:
            return jsonify({'error': '缺少token'}), 400

        # 验证token
        payload = verify_token(token)

        if not payload:
            return jsonify({'error': 'Token无效或已过期'}), 401

        # 返回用户信息，前端存储到localStorage
        return jsonify({
            'message': 'SSO登录成功',
            'user': payload
        }), 200

    except Exception as e:
        return jsonify({'error': f'SSO登录失败: {str(e)}'}), 500
