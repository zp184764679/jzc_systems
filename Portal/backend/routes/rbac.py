"""
RBAC API Routes - Role and Permission Management
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.auth import (
    Role, Permission, DataPermissionRule, MenuPermission,
    RBACService, verify_token, is_admin, is_super_admin,
    AuditService
)
from shared.auth.rbac_models import role_permissions, user_roles, role_menus
import shared.auth.models as auth_models

rbac_bp = Blueprint('rbac', __name__, url_prefix='/api/rbac')


def require_admin_auth(f):
    """Decorator to require admin authentication"""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '缺少认证信息'}), 401

        token = auth_header.split(' ')[1]
        payload = verify_token(token)

        if not payload:
            return jsonify({'error': 'Token无效或已过期'}), 401

        role = payload.get('role', 'user')
        if not is_admin(role):
            return jsonify({'error': '需要管理员权限'}), 403

        g.current_user = payload
        g.user_id = payload.get('user_id') or payload.get('id')
        g.username = payload.get('username')
        g.is_super_admin = is_super_admin(role)

        return f(*args, **kwargs)
    return decorated


# ============== Role Management ==============

@rbac_bp.route('/roles', methods=['GET'])
@require_admin_auth
def get_roles():
    """
    Get all roles with filters

    Query params:
    - module: Filter by module
    - role_type: Filter by role_type (system/custom)
    - search: Search in code, name
    """
    module = request.args.get('module')
    role_type = request.args.get('role_type')
    search = request.args.get('search')

    session = auth_models.AuthSessionLocal()
    try:
        query = session.query(Role)

        if module:
            query = query.filter(Role.module == module)
        if role_type:
            query = query.filter(Role.role_type == role_type)
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                (Role.code.like(search_pattern)) |
                (Role.name.like(search_pattern))
            )

        roles = query.order_by(Role.level.desc(), Role.module, Role.code).all()

        return jsonify({
            'data': [r.to_dict() for r in roles],
            'total': len(roles)
        }), 200
    finally:
        session.close()


@rbac_bp.route('/roles/<int:role_id>', methods=['GET'])
@require_admin_auth
def get_role(role_id):
    """Get single role with permissions"""
    session = auth_models.AuthSessionLocal()
    try:
        role = session.query(Role).filter_by(id=role_id).first()
        if not role:
            return jsonify({'error': '角色不存在'}), 404

        role_dict = role.to_dict()
        role_dict['permissions'] = [p.to_dict() for p in role.permissions]

        return jsonify(role_dict), 200
    finally:
        session.close()


@rbac_bp.route('/roles', methods=['POST'])
@require_admin_auth
def create_role():
    """
    Create a new role

    Request body:
    {
        "code": "string",
        "name": "string",
        "description": "string",
        "module": "string",
        "level": int
    }
    """
    if not g.is_super_admin:
        return jsonify({'error': '仅超级管理员可创建角色'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': '请提供角色信息'}), 400

    required_fields = ['code', 'name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'缺少必填字段: {field}'}), 400

    session = auth_models.AuthSessionLocal()
    try:
        # Check if code already exists
        existing = session.query(Role).filter_by(code=data['code']).first()
        if existing:
            return jsonify({'error': '角色代码已存在'}), 400

        role = Role(
            code=data['code'],
            name=data['name'],
            description=data.get('description'),
            module=data.get('module'),
            level=data.get('level', 0),
            role_type='custom',
            created_by=g.user_id
        )
        session.add(role)
        session.commit()

        # Audit log
        AuditService.log(
            action_type='role_create',
            user_id=g.user_id,
            username=g.username,
            resource_type='role',
            resource_id=role.id,
            description=f'创建角色: {role.name} ({role.code})',
            status='success',
            module='portal'
        )

        return jsonify({
            'message': '角色创建成功',
            'role': role.to_dict()
        }), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@rbac_bp.route('/roles/<int:role_id>', methods=['PUT'])
@require_admin_auth
def update_role(role_id):
    """Update a role"""
    if not g.is_super_admin:
        return jsonify({'error': '仅超级管理员可修改角色'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': '请提供更新信息'}), 400

    session = auth_models.AuthSessionLocal()
    try:
        role = session.query(Role).filter_by(id=role_id).first()
        if not role:
            return jsonify({'error': '角色不存在'}), 404

        # Don't allow modifying system roles
        if role.role_type == 'system':
            return jsonify({'error': '系统角色不可修改'}), 403

        # Update fields
        if 'name' in data:
            role.name = data['name']
        if 'description' in data:
            role.description = data['description']
        if 'module' in data:
            role.module = data['module']
        if 'level' in data:
            role.level = data['level']
        if 'is_active' in data:
            role.is_active = data['is_active']

        role.updated_at = datetime.utcnow()
        session.commit()

        # Clear cache
        RBACService.clear_cache()

        AuditService.log(
            action_type='role_update',
            user_id=g.user_id,
            username=g.username,
            resource_type='role',
            resource_id=role.id,
            description=f'更新角色: {role.name}',
            status='success',
            module='portal'
        )

        return jsonify({
            'message': '角色更新成功',
            'role': role.to_dict()
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@rbac_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@require_admin_auth
def delete_role(role_id):
    """Delete a role"""
    if not g.is_super_admin:
        return jsonify({'error': '仅超级管理员可删除角色'}), 403

    session = auth_models.AuthSessionLocal()
    try:
        role = session.query(Role).filter_by(id=role_id).first()
        if not role:
            return jsonify({'error': '角色不存在'}), 404

        if role.role_type == 'system':
            return jsonify({'error': '系统角色不可删除'}), 403

        role_name = role.name
        session.delete(role)
        session.commit()

        RBACService.clear_cache()

        AuditService.log(
            action_type='role_delete',
            user_id=g.user_id,
            username=g.username,
            resource_type='role',
            resource_id=role_id,
            description=f'删除角色: {role_name}',
            status='success',
            module='portal'
        )

        return jsonify({'message': '角色删除成功'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============== Permission Management ==============

@rbac_bp.route('/permissions', methods=['GET'])
@require_admin_auth
def get_permissions():
    """
    Get all permissions

    Query params:
    - module: Filter by module
    - action: Filter by action type
    - category: Filter by category
    """
    module = request.args.get('module')
    action = request.args.get('action')
    category = request.args.get('category')

    session = auth_models.AuthSessionLocal()
    try:
        query = session.query(Permission).filter_by(is_active=True)

        if module:
            query = query.filter(Permission.module == module)
        if action:
            query = query.filter(Permission.action == action)
        if category:
            query = query.filter(Permission.category == category)

        permissions = query.order_by(Permission.module, Permission.category, Permission.code).all()

        # Group by module for easier frontend use
        grouped = {}
        for perm in permissions:
            if perm.module not in grouped:
                grouped[perm.module] = []
            grouped[perm.module].append(perm.to_dict())

        return jsonify({
            'data': [p.to_dict() for p in permissions],
            'grouped': grouped,
            'total': len(permissions)
        }), 200
    finally:
        session.close()


@rbac_bp.route('/roles/<int:role_id>/permissions', methods=['GET'])
@require_admin_auth
def get_role_permissions(role_id):
    """Get permissions for a role"""
    session = auth_models.AuthSessionLocal()
    try:
        role = session.query(Role).filter_by(id=role_id).first()
        if not role:
            return jsonify({'error': '角色不存在'}), 404

        return jsonify({
            'role': role.to_dict(),
            'permissions': [p.to_dict() for p in role.permissions]
        }), 200
    finally:
        session.close()


@rbac_bp.route('/roles/<int:role_id>/permissions', methods=['PUT'])
@require_admin_auth
def update_role_permissions(role_id):
    """
    Update permissions for a role

    Request body:
    {
        "permission_ids": [1, 2, 3]
    }
    """
    if not g.is_super_admin:
        return jsonify({'error': '仅超级管理员可分配权限'}), 403

    data = request.get_json()
    if not data or 'permission_ids' not in data:
        return jsonify({'error': '请提供权限ID列表'}), 400

    permission_ids = data['permission_ids']

    session = auth_models.AuthSessionLocal()
    try:
        role = session.query(Role).filter_by(id=role_id).first()
        if not role:
            return jsonify({'error': '角色不存在'}), 404

        # Clear existing permissions
        from sqlalchemy import delete
        session.execute(
            delete(role_permissions).where(role_permissions.c.role_id == role_id)
        )

        # Add new permissions
        if permission_ids:
            from sqlalchemy import insert
            for perm_id in permission_ids:
                session.execute(
                    insert(role_permissions).values(
                        role_id=role_id,
                        permission_id=perm_id,
                        created_by=g.user_id
                    )
                )

        session.commit()
        RBACService.clear_cache()

        AuditService.log(
            action_type='permission_change',
            user_id=g.user_id,
            username=g.username,
            resource_type='role',
            resource_id=role_id,
            description=f'更新角色 {role.name} 的权限 ({len(permission_ids)} 个)',
            status='success',
            module='portal'
        )

        return jsonify({
            'message': '权限更新成功',
            'permission_count': len(permission_ids)
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============== User Role Assignment ==============

@rbac_bp.route('/users/<int:user_id>/roles', methods=['GET'])
@require_admin_auth
def get_user_roles(user_id):
    """Get roles for a user"""
    roles = RBACService.get_user_roles(user_id)
    return jsonify({
        'user_id': user_id,
        'roles': [r.to_dict() for r in roles]
    }), 200


@rbac_bp.route('/users/<int:user_id>/roles', methods=['PUT'])
@require_admin_auth
def update_user_roles(user_id):
    """
    Update roles for a user

    Request body:
    {
        "role_ids": [1, 2, 3]
    }
    """
    data = request.get_json()
    if not data or 'role_ids' not in data:
        return jsonify({'error': '请提供角色ID列表'}), 400

    role_ids = data['role_ids']

    session = auth_models.AuthSessionLocal()
    try:
        # Verify user exists
        user = session.query(auth_models.User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # Clear existing roles
        from sqlalchemy import delete
        session.execute(
            delete(user_roles).where(user_roles.c.user_id == user_id)
        )

        # Add new roles
        if role_ids:
            from sqlalchemy import insert
            for role_id in role_ids:
                session.execute(
                    insert(user_roles).values(
                        user_id=user_id,
                        role_id=role_id,
                        created_by=g.user_id
                    )
                )

        session.commit()
        RBACService.clear_cache(user_id)

        AuditService.log(
            action_type='permission_change',
            user_id=g.user_id,
            username=g.username,
            resource_type='user',
            resource_id=user_id,
            description=f'更新用户 {user.username} 的角色 ({len(role_ids)} 个)',
            status='success',
            module='portal'
        )

        return jsonify({
            'message': '角色分配成功',
            'role_count': len(role_ids)
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@rbac_bp.route('/users/<int:user_id>/permissions', methods=['GET'])
@require_admin_auth
def get_user_permissions(user_id):
    """Get effective permissions for a user"""
    permissions = RBACService.get_user_permissions(user_id)
    roles = RBACService.get_user_roles(user_id)

    return jsonify({
        'user_id': user_id,
        'roles': [r.to_dict() for r in roles],
        'permissions': list(permissions)
    }), 200


# ============== Current User Permissions ==============

@rbac_bp.route('/my-permissions', methods=['GET'])
def get_my_permissions():
    """Get permissions for current user"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': '缺少认证信息'}), 401

    token = auth_header.split(' ')[1]
    payload = verify_token(token)

    if not payload:
        return jsonify({'error': 'Token无效或已过期'}), 401

    user_id = payload.get('user_id') or payload.get('id')
    permissions = RBACService.get_user_permissions(user_id)
    roles = RBACService.get_user_role_codes(user_id)

    return jsonify({
        'user_id': user_id,
        'roles': roles,
        'permissions': list(permissions)
    }), 200


@rbac_bp.route('/my-menus', methods=['GET'])
def get_my_menus():
    """Get menu permissions for current user"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': '缺少认证信息'}), 401

    token = auth_header.split(' ')[1]
    payload = verify_token(token)

    if not payload:
        return jsonify({'error': 'Token无效或已过期'}), 401

    user_id = payload.get('user_id') or payload.get('id')
    module = request.args.get('module')

    menus = RBACService.get_user_menus(user_id, module)

    return jsonify({
        'user_id': user_id,
        'menus': menus
    }), 200


@rbac_bp.route('/check-permission', methods=['POST'])
def check_permission():
    """
    Check if current user has a permission

    Request body:
    {
        "permission": "hr:employee:read"
    }
    or
    {
        "permissions": ["hr:employee:read", "hr:employee:update"],
        "require_all": false
    }
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': '缺少认证信息'}), 401

    token = auth_header.split(' ')[1]
    payload = verify_token(token)

    if not payload:
        return jsonify({'error': 'Token无效或已过期'}), 401

    user_id = payload.get('user_id') or payload.get('id')
    data = request.get_json()

    if not data:
        return jsonify({'error': '请提供权限信息'}), 400

    # Single permission check
    if 'permission' in data:
        has_perm = RBACService.has_permission(user_id, data['permission'])
        return jsonify({
            'permission': data['permission'],
            'has_permission': has_perm
        }), 200

    # Multiple permissions check
    if 'permissions' in data:
        permissions = data['permissions']
        require_all = data.get('require_all', False)

        if require_all:
            has_perm = RBACService.has_all_permissions(user_id, permissions)
        else:
            has_perm = RBACService.has_any_permission(user_id, permissions)

        return jsonify({
            'permissions': permissions,
            'require_all': require_all,
            'has_permission': has_perm
        }), 200

    return jsonify({'error': '请提供 permission 或 permissions 字段'}), 400


# ============== Module List ==============

@rbac_bp.route('/modules', methods=['GET'])
def get_modules():
    """Get list of available modules"""
    return jsonify({
        'modules': [
            {'code': 'portal', 'name': '门户系统'},
            {'code': 'account', 'name': '账户管理'},
            {'code': 'hr', 'name': '人力资源'},
            {'code': 'crm', 'name': '客户关系'},
            {'code': 'scm', 'name': '仓库管理'},
            {'code': 'shm', 'name': '出货管理'},
            {'code': 'quotation', 'name': '报价系统'},
            {'code': 'caigou', 'name': '采购系统'},
            {'code': 'eam', 'name': '设备管理'},
            {'code': 'mes', 'name': '制造执行'},
            {'code': 'dashboard', 'name': '可视化看板'}
        ]
    }), 200
