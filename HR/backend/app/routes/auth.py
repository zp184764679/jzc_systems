"""
Authentication routes for HR system
"""
from flask import Blueprint, request, jsonify, make_response
from functools import wraps
import sys
import os
import logging

logger = logging.getLogger(__name__)

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', '../..', '..'))

from shared.auth import (
    User,
    init_auth_db,
    create_access_token,
    verify_token,
    verify_password,
    has_system_permission,
    is_admin,
    Roles
)
import shared.auth.models as auth_models

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/sso-login', methods=['POST', 'OPTIONS'])
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


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    Returns JWT token in httpOnly cookie
    """
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': '请提供用户名和密码'}), 400

    username = data['username']
    password = data['password']

    # Get database session
    auth_session = auth_models.AuthSessionLocal()
    try:
        # Find user by username or email
        user = auth_session.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user:
            return jsonify({'error': '用户名或密码错误'}), 401

        if not user.is_active:
            return jsonify({'error': '账户已被禁用'}), 403

        # Verify password
        if not verify_password(password, user.hashed_password):
            return jsonify({'error': '用户名或密码错误'}), 401

        # Check system permission
        if not has_system_permission(user.permissions, 'hr') and not is_admin(user.role):
            return jsonify({'error': '您没有访问HR系统的权限，请联系管理员'}), 403

        # Create comprehensive JWT token
        token_data = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'emp_no': user.emp_no,
            'role': user.role,
            'is_admin': user.is_admin,  # Backward compatibility
        }
        access_token = create_access_token(token_data)

        # Create response
        response = make_response(jsonify({
            'message': '登录成功',
            'user': user.to_dict()
        }))

        # Set httpOnly cookie
        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=True,
            samesite='Lax',
            path='/',
            max_age=28800  # 8 hours
        )

        return response

    except Exception as e:
        return jsonify({'error': f'登录失败: {str(e)}'}), 500
    finally:
        auth_session.close()


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout endpoint - Clears the JWT cookie"""
    response = make_response(jsonify({'message': '退出登录成功'}))
    response.delete_cookie('access_token', path='/')
    return response


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current authenticated user - Reads JWT from cookie or Authorization header"""
    # Try cookie first
    access_token = request.cookies.get('access_token')
    
    # Try Authorization header if no cookie
    if not access_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ')[1]
    
    if not access_token:
        return jsonify({'error': '未登录'}), 401

    # Verify token
    try:
        payload = verify_token(access_token)
        if not payload:
            return jsonify({'error': '登录已过期，请重新登录'}), 401
    except Exception as e:
        logger.warning(f"Token verification failed in get_current_user: {e}")
        return jsonify({'error': '登录已过期，请重新登录'}), 401

    # Get user from database
    auth_session = auth_models.AuthSessionLocal()
    try:
        user_id = payload.get('user_id')
        user = auth_session.query(User).filter(User.id == user_id).first()

        if not user:
            return jsonify({'error': '用户不存在'}), 404

        if not user.is_active:
            return jsonify({'error': '账户已被禁用'}), 403

        return jsonify(user.to_dict())

    finally:
        auth_session.close()


def require_auth(f):
    """Decorator for protected routes - Verifies JWT token from cookie or header"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try cookie first
        access_token = request.cookies.get('access_token')
        
        # Try Authorization header if no cookie
        if not access_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                access_token = auth_header.split(' ')[1]

        if not access_token:
            return jsonify({'error': '未登录'}), 401

        # Verify token
        try:
            payload = verify_token(access_token)
            if not payload:
                return jsonify({'error': '登录已过期，请重新登录'}), 401
        except Exception as e:
            logger.warning(f"Token verification failed in require_auth: {e}")
            return jsonify({'error': '登录已过期，请重新登录'}), 401

        # Get user from database
        auth_session = auth_models.AuthSessionLocal()
        try:
            user_id = payload.get('user_id')
            user = auth_session.query(User).filter(User.id == user_id).first()

            if not user:
                return jsonify({'error': '用户不存在'}), 401

            if not user.is_active:
                return jsonify({'error': '账户已被禁用'}), 403

            # Pass user to the route function
            return f(user=user, *args, **kwargs)

        finally:
            auth_session.close()

    return decorated_function


def require_admin(f):
    """Decorator to require admin role for route access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try cookie first
        access_token = request.cookies.get('access_token')
        
        # Try Authorization header if no cookie
        if not access_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                access_token = auth_header.split(' ')[1]

        if not access_token:
            return jsonify({'error': '未授权'}), 401

        try:
            payload = verify_token(access_token)
            if not payload:
                return jsonify({'error': '未授权'}), 401
        except Exception as e:
            logger.warning(f"Token verification failed in require_admin: {e}")
            return jsonify({'error': '未授权'}), 401

        auth_session = auth_models.AuthSessionLocal()
        try:
            user_id = payload.get('user_id')
            user = auth_session.query(User).filter(User.id == user_id).first()

            if not user or not user.is_active:
                return jsonify({'error': '未授权'}), 401

            if not is_admin(user.role):
                return jsonify({'error': '需要管理员权限'}), 403

            return f(*args, **kwargs)

        finally:
            auth_session.close()

    return decorated_function
