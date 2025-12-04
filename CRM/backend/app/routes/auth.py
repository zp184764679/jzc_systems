# backend/app/routes/auth.py
"""
SSO Authentication routes for CRM system
"""
import sys
import os
from flask import Blueprint, request, jsonify

# Add parent path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def verify_token(token):
    """Verify JWT token from Portal"""
    import jwt
    try:
        # Use the same secret as Portal shared auth module
        secret_key = os.getenv('JWT_SECRET_KEY', 'jzchardware-sso-secret-key-change-in-production')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@bp.route('/sso-login', methods=['POST', 'OPTIONS'])
def sso_login():
    """SSO login endpoint - validates token from Portal"""
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}
    token = data.get('token') or request.args.get('token')

    if not token:
        return jsonify({'error': 'Token is required'}), 400

    payload = verify_token(token)

    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401

    return jsonify({
        'message': 'SSO登录成功',
        'user': payload
    }), 200


@bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user info from token"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No token provided'}), 401

    token = auth_header.split(' ')[1]
    payload = verify_token(token)

    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401

    return jsonify({'user': payload}), 200
