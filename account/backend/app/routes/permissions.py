"""
Permission Management API Routes
Provides endpoints for managing roles, permissions, and user-role assignments
"""
from flask import Blueprint, request, jsonify
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.auth import User, verify_token
import shared.auth.models as auth_models
from shared.auth.rbac_models import (
    Role, Permission, DataPermissionRule, MenuPermission,
    role_permissions, user_roles, role_menus,
    init_default_roles_and_permissions
)
from shared.auth.rbac_service import RBACService
from functools import wraps
from sqlalchemy import select, delete, insert
from datetime import datetime

permissions_bp = Blueprint('permissions', __name__, url_prefix='/permissions')


def require_admin(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '未授权访问'}), 401

        parts = auth_header.split(' ')
        if len(parts) != 2:
            return jsonify({'error': '无效的认证头格式'}), 401
        token = parts[1]
        try:
            payload = verify_token(token)
            if not payload:
                return jsonify({'error': '无效的令牌'}), 401
            request.current_user = payload
            request.current_user_id = payload.get('user_id') or payload.get('id')

            # Check if user is admin
            is_admin = payload.get('is_admin', False)
            role = payload.get('role', '')
            if not is_admin and role not in ['admin', 'super_admin']:
                return jsonify({'error': '需要管理员权限'}), 403

        except Exception as e:
            return jsonify({'error': '无效的令牌'}), 401

        return f(*args, **kwargs)
    return decorated_function


# ==================== Role Management ====================

@permissions_bp.route('/roles', methods=['GET'])
@require_admin
def get_roles():
    """Get all roles with optional filtering"""
    session = auth_models.AuthSessionLocal()
    try:
        module = request.args.get('module')
        role_type = request.args.get('role_type')

        query = session.query(Role)
        if module:
            query = query.filter(Role.module == module)
        if role_type:
            query = query.filter(Role.role_type == role_type)

        roles = query.order_by(Role.level.desc(), Role.code).all()
        return jsonify([role.to_dict() for role in roles])
    except Exception as e:
        return jsonify({'error': f'获取角色列表失败: {str(e)}'}), 500
    finally:
        session.close()


@permissions_bp.route('/roles/<int:role_id>', methods=['GET'])
@require_admin
def get_role(role_id):
    """Get single role with its permissions"""
    session = auth_models.AuthSessionLocal()
    try:
        role = session.query(Role).filter(Role.id == role_id).first()
        if not role:
            return jsonify({'error': '角色不存在'}), 404

        result = role.to_dict()
        result['permissions'] = [p.to_dict() for p in role.permissions]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'获取角色信息失败: {str(e)}'}), 500
    finally:
        session.close()


@permissions_bp.route('/roles', methods=['POST'])
@require_admin
def create_role():
    """Create a new role"""
    data = request.get_json()

    if not data.get('code') or not data.get('name'):
        return jsonify({'error': '角色代码和名称必填'}), 400

    session = auth_models.AuthSessionLocal()
    try:
        # Check if code already exists
        existing = session.query(Role).filter(Role.code == data['code']).first()
        if existing:
            return jsonify({'error': '角色代码已存在'}), 400

        role = Role(
            code=data['code'],
            name=data['name'],
            description=data.get('description'),
            role_type='custom',
            level=data.get('level', 0),
            module=data.get('module'),
            is_active=True,
            created_by=request.current_user_id
        )
        session.add(role)
        session.commit()

        return jsonify({
            'message': '角色创建成功',
            'role': role.to_dict()
        }), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'创建角色失败: {str(e)}'}), 500
    finally:
        session.close()


@permissions_bp.route('/roles/<int:role_id>', methods=['PUT'])
@require_admin
def update_role(role_id):
    """Update a role"""
    data = request.get_json()

    session = auth_models.AuthSessionLocal()
    try:
        role = session.query(Role).filter(Role.id == role_id).first()
        if not role:
            return jsonify({'error': '角色不存在'}), 404

        # Cannot modify system roles
        if role.role_type == 'system' and data.get('code') != role.code:
            return jsonify({'error': '不能修改系统角色代码'}), 400

        if 'name' in data:
            role.name = data['name']
        if 'description' in data:
            role.description = data['description']
        if 'level' in data:
            role.level = data['level']
        if 'module' in data:
            role.module = data['module']
        if 'is_active' in data:
            role.is_active = data['is_active']

        role.updated_at = datetime.utcnow()
        session.commit()

        return jsonify({
            'message': '角色更新成功',
            'role': role.to_dict()
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'更新角色失败: {str(e)}'}), 500
    finally:
        session.close()


@permissions_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@require_admin
def delete_role(role_id):
    """Delete a role"""
    session = auth_models.AuthSessionLocal()
    try:
        role = session.query(Role).filter(Role.id == role_id).first()
        if not role:
            return jsonify({'error': '角色不存在'}), 404

        if role.role_type == 'system':
            return jsonify({'error': '不能删除系统角色'}), 400

        session.delete(role)
        session.commit()

        # Clear cache
        RBACService.clear_cache()

        return jsonify({'message': '角色已删除'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'删除角色失败: {str(e)}'}), 500
    finally:
        session.close()


# ==================== Permission Management ====================

@permissions_bp.route('', methods=['GET'])
@require_admin
def get_permissions():
    """Get all permissions with optional filtering"""
    session = auth_models.AuthSessionLocal()
    try:
        module = request.args.get('module')
        category = request.args.get('category')
        action = request.args.get('action')

        query = session.query(Permission)
        if module:
            query = query.filter(Permission.module == module)
        if category:
            query = query.filter(Permission.category == category)
        if action:
            query = query.filter(Permission.action == action)

        permissions = query.order_by(Permission.module, Permission.resource, Permission.action).all()
        return jsonify([p.to_dict() for p in permissions])
    except Exception as e:
        return jsonify({'error': f'获取权限列表失败: {str(e)}'}), 500
    finally:
        session.close()


@permissions_bp.route('/tree', methods=['GET'])
@require_admin
def get_permission_tree():
    """Get permissions organized in tree structure by module"""
    session = auth_models.AuthSessionLocal()
    try:
        permissions = session.query(Permission).filter(
            Permission.is_active == True
        ).order_by(Permission.module, Permission.resource, Permission.action).all()

        # Organize into tree structure
        tree = {}
        for perm in permissions:
            if perm.module not in tree:
                tree[perm.module] = {
                    'key': perm.module,
                    'title': get_module_name(perm.module),
                    'children': {}
                }

            if perm.resource not in tree[perm.module]['children']:
                tree[perm.module]['children'][perm.resource] = {
                    'key': f'{perm.module}:{perm.resource}',
                    'title': perm.category or perm.resource,
                    'children': []
                }

            tree[perm.module]['children'][perm.resource]['children'].append({
                'key': perm.code,
                'title': perm.name,
                'id': perm.id,
                'action': perm.action
            })

        # Convert to list format
        result = []
        for module_key, module_data in tree.items():
            module_node = {
                'key': module_data['key'],
                'title': module_data['title'],
                'children': []
            }
            for resource_key, resource_data in module_data['children'].items():
                resource_node = {
                    'key': resource_data['key'],
                    'title': resource_data['title'],
                    'children': resource_data['children']
                }
                module_node['children'].append(resource_node)
            result.append(module_node)

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'获取权限树失败: {str(e)}'}), 500
    finally:
        session.close()


def get_module_name(module):
    """Get display name for module"""
    module_names = {
        'hr': '人力资源',
        'crm': 'CRM客户管理',
        'scm': '仓库管理',
        'quotation': '报价系统',
        'caigou': '采购系统',
        'eam': '设备管理',
        'mes': '生产执行',
        'shm': '出货管理',
        'portal': '门户系统',
        'account': '账户管理',
        'dashboard': '可视化看板'
    }
    return module_names.get(module, module)


@permissions_bp.route('/modules', methods=['GET'])
@require_admin
def get_modules():
    """Get list of available modules"""
    session = auth_models.AuthSessionLocal()
    try:
        modules = session.query(Permission.module).distinct().all()
        result = [{'code': m[0], 'name': get_module_name(m[0])} for m in modules if m[0]]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'获取模块列表失败: {str(e)}'}), 500
    finally:
        session.close()


# ==================== Role-Permission Assignment ====================

@permissions_bp.route('/roles/<int:role_id>/permissions', methods=['GET'])
@require_admin
def get_role_permissions(role_id):
    """Get all permission IDs for a role"""
    session = auth_models.AuthSessionLocal()
    try:
        role = session.query(Role).filter(Role.id == role_id).first()
        if not role:
            return jsonify({'error': '角色不存在'}), 404

        permission_ids = [p.id for p in role.permissions]
        permission_codes = [p.code for p in role.permissions]

        return jsonify({
            'role_id': role_id,
            'permission_ids': permission_ids,
            'permission_codes': permission_codes
        })
    except Exception as e:
        return jsonify({'error': f'获取角色权限失败: {str(e)}'}), 500
    finally:
        session.close()


@permissions_bp.route('/roles/<int:role_id>/permissions', methods=['PUT'])
@require_admin
def set_role_permissions(role_id):
    """Set all permissions for a role (replace existing)"""
    data = request.get_json()
    permission_ids = data.get('permission_ids', [])

    session = auth_models.AuthSessionLocal()
    try:
        role = session.query(Role).filter(Role.id == role_id).first()
        if not role:
            return jsonify({'error': '角色不存在'}), 404

        # Remove all existing permissions
        stmt = delete(role_permissions).where(role_permissions.c.role_id == role_id)
        session.execute(stmt)

        # Add new permissions
        for perm_id in permission_ids:
            stmt = insert(role_permissions).values(
                role_id=role_id,
                permission_id=perm_id,
                created_by=request.current_user_id
            )
            session.execute(stmt)

        session.commit()

        # Clear cache
        RBACService.clear_cache()

        return jsonify({
            'message': '角色权限已更新',
            'role_id': role_id,
            'permission_count': len(permission_ids)
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'更新角色权限失败: {str(e)}'}), 500
    finally:
        session.close()


# ==================== User-Role Assignment ====================

@permissions_bp.route('/users/<int:user_id>/roles', methods=['GET'])
@require_admin
def get_user_roles(user_id):
    """Get all roles assigned to a user"""
    session = auth_models.AuthSessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        roles = RBACService.get_user_roles(user_id)
        return jsonify({
            'user_id': user_id,
            'roles': [r.to_dict() for r in roles],
            'role_ids': [r.id for r in roles]
        })
    except Exception as e:
        return jsonify({'error': f'获取用户角色失败: {str(e)}'}), 500
    finally:
        session.close()


@permissions_bp.route('/users/<int:user_id>/roles', methods=['PUT'])
@require_admin
def set_user_roles(user_id):
    """Set all roles for a user (replace existing)"""
    data = request.get_json()
    role_ids = data.get('role_ids', [])

    session = auth_models.AuthSessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # Remove all existing role assignments
        stmt = delete(user_roles).where(user_roles.c.user_id == user_id)
        session.execute(stmt)

        # Add new role assignments
        for rid in role_ids:
            stmt = insert(user_roles).values(
                user_id=user_id,
                role_id=rid,
                created_by=request.current_user_id
            )
            session.execute(stmt)

        session.commit()

        # Clear cache for this user
        RBACService.clear_cache(user_id)

        return jsonify({
            'message': '用户角色已更新',
            'user_id': user_id,
            'role_count': len(role_ids)
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'更新用户角色失败: {str(e)}'}), 500
    finally:
        session.close()


# ==================== User Effective Permissions ====================

@permissions_bp.route('/users/<int:user_id>/effective-permissions', methods=['GET'])
@require_admin
def get_user_effective_permissions(user_id):
    """Get all effective permissions for a user (aggregated from all roles)"""
    session = auth_models.AuthSessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        permissions = RBACService.get_user_permissions(user_id)
        roles = RBACService.get_user_roles(user_id)

        return jsonify({
            'user_id': user_id,
            'username': user.username,
            'roles': [r.to_dict() for r in roles],
            'permission_codes': list(permissions),
            'permission_count': len(permissions)
        })
    except Exception as e:
        return jsonify({'error': f'获取用户权限失败: {str(e)}'}), 500
    finally:
        session.close()


@permissions_bp.route('/check', methods=['POST'])
@require_admin
def check_permission():
    """Check if a user has a specific permission"""
    data = request.get_json()
    user_id = data.get('user_id')
    permission_code = data.get('permission_code')

    if not user_id or not permission_code:
        return jsonify({'error': '缺少用户ID或权限代码'}), 400

    has_perm = RBACService.has_permission(user_id, permission_code)

    return jsonify({
        'user_id': user_id,
        'permission_code': permission_code,
        'has_permission': has_perm
    })


# ==================== Initialize Default Data ====================

@permissions_bp.route('/init-defaults', methods=['POST'])
@require_admin
def init_defaults():
    """Initialize default roles and permissions"""
    try:
        init_default_roles_and_permissions()
        return jsonify({'message': '默认角色和权限已初始化'})
    except Exception as e:
        return jsonify({'error': f'初始化失败: {str(e)}'}), 500


# ==================== Statistics ====================

@permissions_bp.route('/stats', methods=['GET'])
@require_admin
def get_stats():
    """Get RBAC statistics"""
    session = auth_models.AuthSessionLocal()
    try:
        role_count = session.query(Role).count()
        system_role_count = session.query(Role).filter(Role.role_type == 'system').count()
        custom_role_count = session.query(Role).filter(Role.role_type == 'custom').count()
        permission_count = session.query(Permission).count()

        # Count users with roles
        from sqlalchemy import func
        user_with_roles = session.execute(
            select(func.count(func.distinct(user_roles.c.user_id)))
        ).scalar()

        return jsonify({
            'role_count': role_count,
            'system_role_count': system_role_count,
            'custom_role_count': custom_role_count,
            'permission_count': permission_count,
            'users_with_roles': user_with_roles or 0
        })
    except Exception as e:
        return jsonify({'error': f'获取统计失败: {str(e)}'}), 500
    finally:
        session.close()
