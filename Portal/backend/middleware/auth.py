"""
Authentication and Permission Middleware
"""
from functools import wraps
from flask import request, jsonify
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token

from models import SessionLocal
from models.project_member import ProjectMember


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '未授权：缺少认证信息'}), 401

        token = auth_header.split(' ')[1]
        payload = verify_token(token)

        if not payload:
            return jsonify({'error': '未授权：Token无效或已过期'}), 401

        # Attach user to request
        request.current_user = payload
        return f(*args, **kwargs)

    return decorated_function


def require_project_permission(permission_name):
    """
    Decorator to check if user has specific permission in a project
    Usage: @require_project_permission('can_edit_project')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get current user from request
            user = getattr(request, 'current_user', None)
            if not user:
                return jsonify({'error': '未授权'}), 401

            # Get project_id from kwargs or request
            project_id = kwargs.get('project_id') or request.view_args.get('project_id')
            if not project_id:
                # Try to get from request body
                data = request.get_json(silent=True)
                if data:
                    project_id = data.get('project_id')

            if not project_id:
                return jsonify({'error': '缺少项目ID'}), 400

            # Check permission
            session = SessionLocal()
            try:
                user_id = user.get('user_id') or user.get('id')
                member = session.query(ProjectMember).filter_by(
                    project_id=project_id,
                    user_id=user_id
                ).first()

                if not member:
                    return jsonify({'error': '您不是该项目成员'}), 403

                # Check if has permission
                if not member.has_permission(permission_name):
                    return jsonify({'error': f'权限不足：缺少 {permission_name} 权限'}), 403

                # Attach member to request
                request.project_member = member
                return f(*args, **kwargs)

            finally:
                session.close()

        return decorated_function
    return decorator


def require_project_role(required_role):
    """
    Decorator to check if user has at least the required role in a project
    Role hierarchy: viewer < member < manager < owner
    Usage: @require_project_role('manager')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get current user from request
            user = getattr(request, 'current_user', None)
            if not user:
                return jsonify({'error': '未授权'}), 401

            # Get project_id
            project_id = kwargs.get('project_id') or request.view_args.get('project_id')
            if not project_id:
                data = request.get_json(silent=True)
                if data:
                    project_id = data.get('project_id')

            if not project_id:
                return jsonify({'error': '缺少项目ID'}), 400

            # Role hierarchy
            role_hierarchy = {
                'viewer': 0,
                'member': 1,
                'manager': 2,
                'owner': 3,
            }

            # Check role
            session = SessionLocal()
            try:
                user_id = user.get('user_id') or user.get('id')
                member = session.query(ProjectMember).filter_by(
                    project_id=project_id,
                    user_id=user_id
                ).first()

                if not member:
                    return jsonify({'error': '您不是该项目成员'}), 403

                user_role_level = role_hierarchy.get(member.role.value if hasattr(member.role, 'value') else member.role, 0)
                required_role_level = role_hierarchy.get(required_role, 0)

                if user_role_level < required_role_level:
                    return jsonify({'error': f'权限不足：需要 {required_role} 角色'}), 403

                # Attach member to request
                request.project_member = member
                return f(*args, **kwargs)

            finally:
                session.close()

        return decorated_function
    return decorator


def get_current_user():
    """Helper function to get current user from token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ')[1]
    payload = verify_token(token)
    return payload if payload else None


def is_super_admin():
    """Check if current user is super admin"""
    user = get_current_user()
    if not user:
        return False
    return user.get('role') == 'super_admin'


def is_admin():
    """Check if current user is admin or super admin"""
    user = get_current_user()
    if not user:
        return False
    role = user.get('role')
    return role in ['admin', 'super_admin']
