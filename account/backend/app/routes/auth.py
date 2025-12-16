from flask import Blueprint, request, jsonify, session
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', '../..', '..'))

from shared.auth import (
    User, init_auth_db, create_access_token, verify_token,
    verify_password, has_system_permission, is_admin, Roles
)
import shared.auth.models as auth_models

# Initialize auth database
init_auth_db()

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with username/email and password"""
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': '请提供用户名和密码'}), 400

    username = data['username']
    password = data['password']

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
        if not has_system_permission(user.permissions, 'account') and not is_admin(user.role):
            return jsonify({'error': '您没有访问账务系统的权限，请联系管理员'}), 403

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
        token = create_access_token(token_data)

        # Store user info in session
        session['user_id'] = user.id
        session['username'] = user.username

        return jsonify({
            'message': '登录成功',
            'token': token,
            'user': user.to_dict()
        })

    except Exception as e:
        return jsonify({'error': f'登录失败: {str(e)}'}), 500
    finally:
        auth_session.close()


@auth_bp.route('/sso-login', methods=['POST'])
def sso_login():
    """SSO Login - validate token from Portal"""
    data = request.get_json()
    token = data.get('token') if data else None

    if not token:
        return jsonify({'error': '缺少token'}), 400

    try:
        # Verify the token
        payload = verify_token(token)

        if not payload:
            return jsonify({'error': 'Token无效或已过期'}), 401

        user_id = payload.get('user_id')

        auth_session = auth_models.AuthSessionLocal()
        try:
            user = auth_session.query(User).filter(User.id == user_id).first()

            if not user:
                return jsonify({'error': '用户不存在'}), 404

            if not user.is_active:
                return jsonify({'error': '账户已被禁用'}), 403

            # Check system permission
            if not has_system_permission(user.permissions, 'account') and not is_admin(user.role):
                return jsonify({'error': '您没有访问账务系统的权限'}), 403

            # Store user info in session
            session['user_id'] = user.id
            session['username'] = user.username

            return jsonify({
                'message': 'SSO登录成功',
                'user': user.to_dict()
            })

        finally:
            auth_session.close()

    except Exception as e:
        return jsonify({'error': f'Token验证失败: {str(e)}'}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout current user"""
    session.clear()
    return jsonify({'message': '登出成功'})


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user information"""
    # Try to get user from session
    user_id = session.get('user_id')

    if not user_id:
        # Try to get from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            parts = auth_header.split(' ')
            if len(parts) != 2:
                return jsonify({'error': '无效的认证头格式'}), 401
            token = parts[1]
            try:
                payload = verify_token(token)
                user_id = payload.get('user_id')
            except Exception:
                return jsonify({'error': '未授权'}), 401
        else:
            return jsonify({'error': '未授权'}), 401

    auth_session = auth_models.AuthSessionLocal()
    try:
        user = auth_session.query(User).filter(User.id == user_id).first()

        if not user:
            session.clear()
            return jsonify({'error': '用户不存在'}), 404

        if not user.is_active:
            session.clear()
            return jsonify({'error': '账户已被禁用'}), 403

        return jsonify({'user': user.to_dict()})

    except Exception as e:
        return jsonify({'error': f'获取用户信息失败: {str(e)}'}), 500
    finally:
        auth_session.close()


def require_admin(f):
    """Decorator to require admin role for route access"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try to get user from session
        user_id = session.get('user_id')

        if not user_id:
            # Try to get from Authorization header
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                parts = auth_header.split(' ')
                if len(parts) != 2:
                    return jsonify({'error': '无效的认证头格式'}), 401
                token = parts[1]
                try:
                    payload = verify_token(token)
                    user_id = payload.get('user_id')
                except Exception:
                    return jsonify({'error': '未授权'}), 401
            else:
                return jsonify({'error': '未授权'}), 401

        auth_session = auth_models.AuthSessionLocal()
        try:
            user = auth_session.query(User).filter(User.id == user_id).first()

            if not user or not user.is_active:
                return jsonify({'error': '未授权'}), 401

            if not is_admin(user.role):
                return jsonify({'error': '需要管理员权限'}), 403

            return f(*args, **kwargs)

        finally:
            auth_session.close()

    return decorated_function
