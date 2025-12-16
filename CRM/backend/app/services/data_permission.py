# -*- coding: utf-8 -*-
"""
CRM 数据权限控制服务
支持基于用户、部门、角色的数据访问控制
"""
import os
import sys
from functools import wraps
from flask import request, jsonify, g

# 添加 shared 模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

try:
    from shared.auth_middleware import decode_token
    from shared.auth.permissions import is_admin, Roles
except ImportError:
    # Fallback if shared module not available
    import jwt
    JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'jzc-dev-shared-secret-key-2025')

    def decode_token(token):
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])

    def is_admin(role):
        return role in ('admin', 'super_admin')

    class Roles:
        USER = 'user'
        ADMIN = 'admin'
        SUPER_ADMIN = 'super_admin'


class DataAccessLevel:
    """数据访问级别"""
    SELF = 'self'           # 只能访问自己的数据
    TEAM = 'team'           # 可以访问团队的数据
    DEPARTMENT = 'department'  # 可以访问部门的数据
    ALL = 'all'             # 可以访问所有数据


def get_current_user():
    """获取当前用户信息"""
    return getattr(g, 'current_user', None)


def crm_auth(f):
    """
    CRM 认证装饰器
    从 Token 中解析用户信息并存入 g.current_user
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)

        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({
                'success': False,
                'error': '缺少认证Token',
                'code': 'AUTH_REQUIRED'
            }), 401

        token = auth_header
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]

        try:
            payload = decode_token(token)

            g.current_user = {
                'user_id': payload.get('user_id') or payload.get('id'),
                'username': payload.get('username'),
                'full_name': payload.get('full_name'),
                'role': payload.get('role', 'user'),
                'department_id': payload.get('department_id'),
                'department_name': payload.get('department_name'),
                'team_id': payload.get('team_id'),
                'emp_no': payload.get('emp_no'),
            }

            return f(*args, **kwargs)

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'code': 'AUTH_ERROR'
            }), 401

    return decorated


def crm_optional_auth(f):
    """
    CRM 可选认证装饰器
    Token 存在则解析，不存在也允许访问
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)

        auth_header = request.headers.get('Authorization')

        if auth_header:
            token = auth_header
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]

            try:
                payload = decode_token(token)
                g.current_user = {
                    'user_id': payload.get('user_id') or payload.get('id'),
                    'username': payload.get('username'),
                    'full_name': payload.get('full_name'),
                    'role': payload.get('role', 'user'),
                    'department_id': payload.get('department_id'),
                    'department_name': payload.get('department_name'),
                    'team_id': payload.get('team_id'),
                    'emp_no': payload.get('emp_no'),
                }
            except:
                g.current_user = None
        else:
            g.current_user = None

        return f(*args, **kwargs)

    return decorated


def crm_admin_required(f):
    """
    CRM 管理员权限装饰器
    必须先使用 @crm_auth
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)

        current_user = get_current_user()

        if not current_user:
            return jsonify({
                'success': False,
                'error': '未认证',
                'code': 'NOT_AUTHENTICATED'
            }), 401

        if not is_admin(current_user.get('role', '')):
            return jsonify({
                'success': False,
                'error': '需要管理员权限',
                'code': 'ADMIN_REQUIRED'
            }), 403

        return f(*args, **kwargs)

    return decorated


def get_data_access_level(user=None):
    """
    获取用户的数据访问级别

    Args:
        user: 用户信息字典，默认从 g.current_user 获取

    Returns:
        DataAccessLevel: 数据访问级别
    """
    if user is None:
        user = get_current_user()

    if not user:
        return DataAccessLevel.SELF

    role = user.get('role', 'user')

    # 管理员可以访问所有数据
    if is_admin(role):
        return DataAccessLevel.ALL

    # 主管级别可以访问部门数据
    if role == 'supervisor':
        return DataAccessLevel.DEPARTMENT

    # 普通用户只能访问自己的数据
    return DataAccessLevel.SELF


def apply_data_permission_filter(query, model, user=None):
    """
    应用数据权限过滤到查询

    Args:
        query: SQLAlchemy 查询对象
        model: 数据模型类（需要有 owner_id 或 created_by 字段）
        user: 用户信息字典

    Returns:
        过滤后的查询对象
    """
    if user is None:
        user = get_current_user()

    if not user:
        # 未登录用户返回空结果
        return query.filter(False)

    access_level = get_data_access_level(user)

    if access_level == DataAccessLevel.ALL:
        # 管理员可以看所有数据
        return query

    user_id = user.get('user_id')

    # 检查模型是否有 owner_id 字段
    if hasattr(model, 'owner_id'):
        if access_level == DataAccessLevel.DEPARTMENT:
            # 部门级别：同部门的数据
            department_id = user.get('department_id')
            if department_id and hasattr(model, 'department_id'):
                from sqlalchemy import or_
                return query.filter(
                    or_(
                        model.owner_id == user_id,
                        model.department_id == department_id
                    )
                )
            else:
                return query.filter(model.owner_id == user_id)

        elif access_level == DataAccessLevel.TEAM:
            # 团队级别：同团队的数据
            team_id = user.get('team_id')
            if team_id and hasattr(model, 'team_id'):
                from sqlalchemy import or_
                return query.filter(
                    or_(
                        model.owner_id == user_id,
                        model.team_id == team_id
                    )
                )
            else:
                return query.filter(model.owner_id == user_id)

        else:
            # 只能看自己的数据
            return query.filter(model.owner_id == user_id)

    # 如果模型没有 owner_id，检查 created_by
    elif hasattr(model, 'created_by'):
        if access_level in (DataAccessLevel.ALL,):
            return query
        return query.filter(model.created_by == user_id)

    # 如果模型没有权限控制字段，根据访问级别决定
    if access_level == DataAccessLevel.ALL:
        return query

    # 默认返回所有数据（向后兼容，之后可以改为返回空）
    return query


def can_access_record(record, user=None):
    """
    检查用户是否有权访问指定记录

    Args:
        record: 数据记录对象
        user: 用户信息字典

    Returns:
        bool: 是否有访问权限
    """
    if user is None:
        user = get_current_user()

    if not user:
        return False

    access_level = get_data_access_level(user)

    if access_level == DataAccessLevel.ALL:
        return True

    user_id = user.get('user_id')

    # 检查 owner_id
    if hasattr(record, 'owner_id'):
        if record.owner_id == user_id:
            return True

        if access_level == DataAccessLevel.DEPARTMENT:
            department_id = user.get('department_id')
            if department_id and hasattr(record, 'department_id'):
                return record.department_id == department_id

        elif access_level == DataAccessLevel.TEAM:
            team_id = user.get('team_id')
            if team_id and hasattr(record, 'team_id'):
                return record.team_id == team_id

        return False

    # 检查 created_by
    if hasattr(record, 'created_by'):
        if record.created_by == user_id:
            return True
        return access_level == DataAccessLevel.ALL

    # 没有权限控制字段，默认允许访问
    return True


def can_edit_record(record, user=None):
    """
    检查用户是否有权编辑指定记录

    Args:
        record: 数据记录对象
        user: 用户信息字典

    Returns:
        bool: 是否有编辑权限
    """
    if user is None:
        user = get_current_user()

    if not user:
        return False

    # 管理员可以编辑所有记录
    if is_admin(user.get('role', '')):
        return True

    user_id = user.get('user_id')

    # 只有 owner 可以编辑
    if hasattr(record, 'owner_id'):
        return record.owner_id == user_id

    if hasattr(record, 'created_by'):
        return record.created_by == user_id

    # 没有权限控制字段，默认允许编辑
    return True


def can_delete_record(record, user=None):
    """
    检查用户是否有权删除指定记录

    Args:
        record: 数据记录对象
        user: 用户信息字典

    Returns:
        bool: 是否有删除权限
    """
    if user is None:
        user = get_current_user()

    if not user:
        return False

    # 只有管理员或 owner 可以删除
    if is_admin(user.get('role', '')):
        return True

    user_id = user.get('user_id')

    if hasattr(record, 'owner_id'):
        return record.owner_id == user_id

    if hasattr(record, 'created_by'):
        return record.created_by == user_id

    return False
