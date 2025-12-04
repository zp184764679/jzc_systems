from flask import Blueprint, request, jsonify
import sys
import os
import json

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.auth import User, hash_password, verify_token
import shared.auth.models as auth_models
from functools import wraps

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


def require_admin(f):
    '''Decorator to require admin authentication'''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '未授权访问'}), 401

        token = auth_header.split(' ')[1]
        try:
            payload = verify_token(token)
            if not payload:
                return jsonify({'error': '无效的令牌'}), 401
            request.current_user = payload

            # Check if user is admin (by is_admin field or by role)
            is_admin = payload.get('is_admin', False)
            role = payload.get('role', '')
            if not is_admin and role not in ['admin', 'super_admin']:
                return jsonify({'error': '需要管理员权限'}), 403

        except Exception as e:
            return jsonify({'error': '无效的令牌'}), 401

        return f(*args, **kwargs)
    return decorated_function


@users_bp.route('', methods=['GET'])
@require_admin
def get_users():
    '''Get all users (admin only)'''
    auth_session = auth_models.AuthSessionLocal()
    try:
        users = auth_session.query(User).all()
        return jsonify([user.to_dict() for user in users])
    except Exception as e:
        return jsonify({'error': f'获取用户列表失败: {str(e)}'}), 500
    finally:
        auth_session.close()


@users_bp.route('/<int:user_id>', methods=['GET'])
@require_admin
def get_user(user_id):
    '''Get user by ID (admin only)'''
    auth_session = auth_models.AuthSessionLocal()
    try:
        user = auth_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        return jsonify(user.to_dict())
    except Exception as e:
        return jsonify({'error': f'获取用户信息失败: {str(e)}'}), 500
    finally:
        auth_session.close()


@users_bp.route('/<int:user_id>', methods=['PUT'])
@require_admin
def update_user(user_id):
    '''Update user (admin only)'''
    data = request.get_json()
    
    auth_session = auth_models.AuthSessionLocal()
    try:
        user = auth_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # Update allowed fields
        if 'email' in data:
            user.email = data['email']
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'emp_no' in data:
            user.emp_no = data['emp_no']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'role' in data and data['role'] in ['user', 'supervisor', 'admin', 'super_admin']:
            user.role = data['role']
        if 'permissions' in data:
            user.permissions = json.dumps(data['permissions'])
        # Organization structure fields
        if 'department_name' in data:
            user.department_name = data['department_name']
        if 'department_id' in data:
            user.department_id = data['department_id']
        if 'position_name' in data:
            user.position_name = data['position_name']
        if 'position_id' in data:
            user.position_id = data['position_id']
        if 'team_name' in data:
            user.team_name = data['team_name']
        if 'team_id' in data:
            user.team_id = data['team_id']
        
        auth_session.commit()
        return jsonify({
            'message': '用户信息已更新',
            'user': user.to_dict()
        })
    except Exception as e:
        auth_session.rollback()
        return jsonify({'error': f'更新用户失败: {str(e)}'}), 500
    finally:
        auth_session.close()


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    '''Delete user (admin only)'''
    auth_session = auth_models.AuthSessionLocal()
    try:
        user = auth_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # Prevent deleting yourself
        if user.id == request.current_user.get('user_id'):
            return jsonify({'error': '不能删除自己的账户'}), 400
        
        auth_session.delete(user)
        auth_session.commit()
        return jsonify({'message': '用户已删除'})
    except Exception as e:
        auth_session.rollback()
        return jsonify({'error': f'删除用户失败: {str(e)}'}), 500
    finally:
        auth_session.close()


@users_bp.route('/<int:user_id>/toggle-active', methods=['POST'])
@require_admin
def toggle_user_active(user_id):
    '''Toggle user active status (admin only)'''
    auth_session = auth_models.AuthSessionLocal()
    try:
        user = auth_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        user.is_active = not user.is_active
        auth_session.commit()
        
        status = '激活' if user.is_active else '停用'
        return jsonify({
            'message': f'用户已{status}',
            'user': user.to_dict()
        })
    except Exception as e:
        auth_session.rollback()
        return jsonify({'error': f'更新用户状态失败: {str(e)}'}), 500
    finally:
        auth_session.close()


@users_bp.route('/<int:user_id>/reset-password', methods=['POST'])
@require_admin
def reset_password(user_id):
    '''Reset user password (admin only)'''
    data = request.get_json()
    
    if not data or 'new_password' not in data:
        return jsonify({'error': '请提供新密码'}), 400
    
    new_password = data['new_password']
    if len(new_password) < 6:
        return jsonify({'error': '密码至少6个字符'}), 400
    
    auth_session = auth_models.AuthSessionLocal()
    try:
        user = auth_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        user.hashed_password = hash_password(new_password)
        auth_session.commit()
        
        return jsonify({'message': '密码已重置'})
    except Exception as e:
        auth_session.rollback()
        return jsonify({'error': f'重置密码失败: {str(e)}'}), 500
    finally:
        auth_session.close()
