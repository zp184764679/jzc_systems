# -*- coding: utf-8 -*-
"""
认证和授权装饰器
统一管理身份验证和权限检查
"""
from functools import wraps
from flask import request
from utils.response import error_response
import sys
import os

# Add shared module to path for JWT verification
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', '..'))
from shared.auth import verify_token


def require_auth(f):
    """
    要求用户已认证
    验证JWT token并检查User-ID
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 优先验证 JWT token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = verify_token(token)
            if payload:
                # Token有效，使用token中的user_id
                kwargs['current_user_id'] = str(payload.get('user_id'))
                kwargs['current_user_role'] = payload.get('role')
                kwargs['token_payload'] = payload
                return f(*args, **kwargs)

        # 回退检查 User-ID header (兼容旧代码)
        user_id = request.headers.get('User-ID')
        if not user_id:
            return error_response("未授权：请先登录", 401)

        # 将user_id注入到kwargs中，方便使用
        kwargs['current_user_id'] = user_id
        return f(*args, **kwargs)

    return decorated_function


def require_jwt(f):
    """
    严格要求JWT token认证（不接受User-ID header）
    用于敏感操作
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return error_response("未授权：缺少认证令牌", 401)

        token = auth_header.split(' ')[1]
        payload = verify_token(token)

        if not payload:
            return error_response("未授权：令牌无效或已过期", 401)

        kwargs['current_user_id'] = str(payload.get('user_id'))
        kwargs['current_user_role'] = payload.get('role')
        kwargs['token_payload'] = payload
        return f(*args, **kwargs)

    return decorated_function


def require_supplier():
    """
    要求供应商已认证
    检查Supplier-ID header是否存在
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            supplier_id = request.headers.get('Supplier-ID')
            if not supplier_id:
                return error_response("未授权：缺少供应商ID", 401)

            # 将supplier_id注入到kwargs中
            kwargs['current_supplier_id'] = supplier_id
            return f(*args, **kwargs)

        return decorated_function
    return decorator


def require_role(*allowed_roles):
    """
    要求用户具有特定角色

    用法:
        @require_role('admin', 'super_admin')
        def my_route():
            pass

    参数:
        allowed_roles: 允许的角色列表
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = request.headers.get('User-ID')
            user_role = request.headers.get('User-Role')

            if not user_id:
                return error_response("未授权：缺少用户ID", 401)

            if not user_role:
                return error_response("未授权：缺少用户角色", 401)

            if user_role not in allowed_roles:
                return error_response(f"权限不足：需要以下角色之一：{', '.join(allowed_roles)}", 403)

            # 将user信息注入到kwargs中
            kwargs['current_user_id'] = user_id
            kwargs['current_user_role'] = user_role
            return f(*args, **kwargs)

        return decorated_function
    return decorator


def require_admin(f):
    """
    要求管理员权限（admin或super_admin）
    这是require_role的便捷方法
    """
    @wraps(f)
    @require_role('admin', 'super_admin')
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)

    return decorated_function


def require_super_admin(f):
    """
    要求超级管理员权限
    这是require_role的便捷方法
    """
    @wraps(f)
    @require_role('super_admin')
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    """
    获取当前用户信息
    返回: {'user_id': str, 'user_role': str} 或 None
    """
    user_id = request.headers.get('User-ID')
    user_role = request.headers.get('User-Role')

    if not user_id:
        return None

    return {
        'user_id': user_id,
        'user_role': user_role
    }


def get_current_supplier():
    """
    获取当前供应商信息
    返回: {'supplier_id': str} 或 None
    """
    supplier_id = request.headers.get('Supplier-ID')

    if not supplier_id:
        return None

    return {
        'supplier_id': supplier_id
    }


def check_permission(user_role, required_roles):
    """
    检查用户角色是否在允许的角色列表中

    参数:
        user_role: 用户角色
        required_roles: 允许的角色列表

    返回:
        bool: 是否有权限
    """
    if not user_role:
        return False

    if isinstance(required_roles, str):
        required_roles = [required_roles]

    return user_role in required_roles


def is_admin(user_role=None):
    """
    判断是否为管理员

    参数:
        user_role: 用户角色，如果为None则从request header获取

    返回:
        bool: 是否为管理员
    """
    if user_role is None:
        user_role = request.headers.get('User-Role')

    return user_role in ['admin', 'super_admin']


def is_super_admin(user_role=None):
    """
    判断是否为超级管理员

    参数:
        user_role: 用户角色，如果为None则从request header获取

    返回:
        bool: 是否为超级管理员
    """
    if user_role is None:
        user_role = request.headers.get('User-Role')

    return user_role == 'super_admin'


# =========================
# 用户查询函数 (数据源: shared.auth / account.users)
# =========================

def get_user_by_id(user_id):
    """
    根据ID获取用户（从统一数据源 account.users）

    参数:
        user_id: 用户ID
    返回:
        用户对象 或 None
    """
    try:
        from shared.auth import User as AuthUser
        import shared.auth.models as auth_models

        session = auth_models.AuthSessionLocal()
        user = session.query(AuthUser).filter(AuthUser.id == user_id).first()
        session.close()
        return user
    except Exception as e:
        print(f"获取用户失败: {e}")
        return None


def get_users_by_role(role):
    """
    根据角色获取用户列表（从统一数据源 account.users）

    参数:
        role: 角色名称，如 'super_admin', 'admin', 'user'
    返回:
        用户列表
    """
    try:
        from shared.auth import User as AuthUser
        import shared.auth.models as auth_models

        session = auth_models.AuthSessionLocal()
        users = session.query(AuthUser).filter(AuthUser.role == role).all()
        session.close()
        return users
    except Exception as e:
        print(f"获取用户列表失败: {e}")
        return []


def get_all_approvers(exclude_user_id=None):
    """
    获取所有审批人（super_admin角色）

    参数:
        exclude_user_id: 排除的用户ID（通常是申请人自己）
    返回:
        审批人列表
    """
    try:
        from shared.auth import User as AuthUser
        import shared.auth.models as auth_models

        session = auth_models.AuthSessionLocal()
        query = session.query(AuthUser).filter(AuthUser.role == 'super_admin')

        if exclude_user_id:
            query = query.filter(AuthUser.id != exclude_user_id)

        users = query.all()
        session.close()
        return users
    except Exception as e:
        print(f"获取审批人列表失败: {e}")
        return []
