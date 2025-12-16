"""
RBAC Service - Role-Based Access Control Service
Provides permission checking and role management functions
"""
from typing import List, Dict, Any, Optional, Set
from functools import wraps
from flask import request, jsonify, g
import json

from .models import User, AuthSessionLocal
from .rbac_models import (
    Role, Permission, DataPermissionRule, MenuPermission,
    role_permissions, user_roles, role_menus
)
from .jwt_utils import verify_token


class RBACService:
    """Service for RBAC operations"""

    # Cache for permission lookups (simple in-memory cache)
    _permission_cache: Dict[int, Set[str]] = {}
    _role_cache: Dict[int, List[str]] = {}

    @staticmethod
    def clear_cache(user_id: Optional[int] = None):
        """Clear permission cache for a user or all users"""
        if user_id:
            RBACService._permission_cache.pop(user_id, None)
            RBACService._role_cache.pop(user_id, None)
        else:
            RBACService._permission_cache.clear()
            RBACService._role_cache.clear()

    @staticmethod
    def get_user_roles(user_id: int) -> List[Role]:
        """Get all roles assigned to a user"""
        session = AuthSessionLocal()
        try:
            # Get roles through user_roles association
            from sqlalchemy import select
            stmt = select(Role).join(user_roles).where(
                user_roles.c.user_id == user_id,
                Role.is_active == True
            )
            roles = session.execute(stmt).scalars().all()

            # Also include the legacy role from User model
            user = session.query(User).filter_by(id=user_id).first()
            if user and user.role:
                legacy_role = session.query(Role).filter_by(code=user.role).first()
                if legacy_role and legacy_role not in roles:
                    roles = list(roles) + [legacy_role]

            return list(roles)
        finally:
            session.close()

    @staticmethod
    def get_user_role_codes(user_id: int) -> List[str]:
        """Get role codes for a user (cached)"""
        if user_id in RBACService._role_cache:
            return RBACService._role_cache[user_id]

        roles = RBACService.get_user_roles(user_id)
        role_codes = [r.code for r in roles]

        RBACService._role_cache[user_id] = role_codes
        return role_codes

    @staticmethod
    def get_user_permissions(user_id: int) -> Set[str]:
        """
        Get all permission codes for a user (cached)
        Aggregates permissions from all user's roles
        """
        if user_id in RBACService._permission_cache:
            return RBACService._permission_cache[user_id]

        session = AuthSessionLocal()
        try:
            permissions = set()

            # Get all roles for user
            roles = RBACService.get_user_roles(user_id)

            # Get permissions for each role
            for role in roles:
                for perm in role.permissions:
                    if perm.is_active:
                        permissions.add(perm.code)

            # Super admin has all permissions
            role_codes = [r.code for r in roles]
            if 'super_admin' in role_codes:
                # Add all active permissions
                all_perms = session.query(Permission).filter_by(is_active=True).all()
                for perm in all_perms:
                    permissions.add(perm.code)

            RBACService._permission_cache[user_id] = permissions
            return permissions
        finally:
            session.close()

    @staticmethod
    def has_permission(user_id: int, permission_code: str) -> bool:
        """Check if user has a specific permission"""
        permissions = RBACService.get_user_permissions(user_id)
        return permission_code in permissions

    @staticmethod
    def has_any_permission(user_id: int, permission_codes: List[str]) -> bool:
        """Check if user has any of the given permissions"""
        permissions = RBACService.get_user_permissions(user_id)
        return any(code in permissions for code in permission_codes)

    @staticmethod
    def has_all_permissions(user_id: int, permission_codes: List[str]) -> bool:
        """Check if user has all of the given permissions"""
        permissions = RBACService.get_user_permissions(user_id)
        return all(code in permissions for code in permission_codes)

    @staticmethod
    def has_module_access(user_id: int, module: str) -> bool:
        """Check if user has any permission for a module"""
        permissions = RBACService.get_user_permissions(user_id)
        return any(perm.startswith(f"{module}:") for perm in permissions)

    @staticmethod
    def get_user_menus(user_id: int, module: Optional[str] = None) -> List[Dict]:
        """Get menu permissions for a user"""
        session = AuthSessionLocal()
        try:
            roles = RBACService.get_user_roles(user_id)
            role_ids = [r.id for r in roles]

            if not role_ids:
                return []

            # Get menus through role_menus
            from sqlalchemy import select
            stmt = select(MenuPermission).join(role_menus).where(
                role_menus.c.role_id.in_(role_ids),
                MenuPermission.is_active == True
            )
            if module:
                stmt = stmt.where(MenuPermission.module == module)

            stmt = stmt.order_by(MenuPermission.sort_order)

            menus = session.execute(stmt).scalars().all()

            # Remove duplicates while preserving order
            seen = set()
            unique_menus = []
            for menu in menus:
                if menu.id not in seen:
                    seen.add(menu.id)
                    unique_menus.append(menu.to_dict())

            return unique_menus
        finally:
            session.close()

    @staticmethod
    def get_data_filter(user_id: int, module: str, resource: str) -> Optional[Dict]:
        """
        Get data permission filter for a user
        Returns filter condition to apply to queries
        """
        session = AuthSessionLocal()
        try:
            # Get user info for dynamic conditions
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return None

            # Check if super admin (no filter)
            role_codes = RBACService.get_user_role_codes(user_id)
            if 'super_admin' in role_codes:
                return None  # No filter for super admin

            # Get data permission rules for user
            user_rules = session.query(DataPermissionRule).filter(
                DataPermissionRule.user_id == user_id,
                DataPermissionRule.module == module,
                DataPermissionRule.resource == resource,
                DataPermissionRule.is_active == True
            ).order_by(DataPermissionRule.priority.desc()).all()

            # Get data permission rules for user's roles
            roles = RBACService.get_user_roles(user_id)
            role_ids = [r.id for r in roles]

            role_rules = session.query(DataPermissionRule).filter(
                DataPermissionRule.role_id.in_(role_ids),
                DataPermissionRule.module == module,
                DataPermissionRule.resource == resource,
                DataPermissionRule.is_active == True
            ).order_by(DataPermissionRule.priority.desc()).all()

            # User rules take precedence over role rules
            all_rules = user_rules + role_rules

            if not all_rules:
                return None  # No specific filter

            # Merge conditions (OR logic for multiple rules)
            merged_condition = {}
            for rule in all_rules:
                condition = rule.condition
                if isinstance(condition, dict):
                    # Replace dynamic placeholders
                    resolved = RBACService._resolve_condition(condition, user)
                    for key, value in resolved.items():
                        if key in merged_condition:
                            # Merge values (OR)
                            existing = merged_condition[key]
                            if isinstance(existing, list) and isinstance(value, list):
                                merged_condition[key] = list(set(existing + value))
                            elif isinstance(existing, list):
                                merged_condition[key] = list(set(existing + [value]))
                            elif isinstance(value, list):
                                merged_condition[key] = list(set([existing] + value))
                            else:
                                merged_condition[key] = [existing, value]
                        else:
                            merged_condition[key] = value

            return merged_condition if merged_condition else None
        finally:
            session.close()

    @staticmethod
    def _resolve_condition(condition: Dict, user: User) -> Dict:
        """Resolve dynamic placeholders in condition"""
        resolved = {}
        for key, value in condition.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                # Dynamic value from user
                path = value[2:-1]  # Remove ${ and }
                parts = path.split('.')
                if parts[0] == 'user' and len(parts) > 1:
                    attr = parts[1]
                    resolved[key] = getattr(user, attr, None)
            elif isinstance(value, dict):
                resolved[key] = RBACService._resolve_condition(value, user)
            else:
                resolved[key] = value
        return resolved

    @staticmethod
    def assign_role_to_user(user_id: int, role_id: int, created_by: Optional[int] = None):
        """Assign a role to a user"""
        session = AuthSessionLocal()
        try:
            from sqlalchemy import insert
            stmt = insert(user_roles).values(
                user_id=user_id,
                role_id=role_id,
                created_by=created_by
            )
            session.execute(stmt)
            session.commit()

            # Clear cache
            RBACService.clear_cache(user_id)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def remove_role_from_user(user_id: int, role_id: int):
        """Remove a role from a user"""
        session = AuthSessionLocal()
        try:
            from sqlalchemy import delete
            stmt = delete(user_roles).where(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role_id
            )
            session.execute(stmt)
            session.commit()

            # Clear cache
            RBACService.clear_cache(user_id)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def assign_permission_to_role(role_id: int, permission_id: int, created_by: Optional[int] = None):
        """Assign a permission to a role"""
        session = AuthSessionLocal()
        try:
            from sqlalchemy import insert
            stmt = insert(role_permissions).values(
                role_id=role_id,
                permission_id=permission_id,
                created_by=created_by
            )
            session.execute(stmt)
            session.commit()

            # Clear all cache (role permissions affect multiple users)
            RBACService.clear_cache()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def remove_permission_from_role(role_id: int, permission_id: int):
        """Remove a permission from a role"""
        session = AuthSessionLocal()
        try:
            from sqlalchemy import delete
            stmt = delete(role_permissions).where(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id == permission_id
            )
            session.execute(stmt)
            session.commit()

            # Clear all cache
            RBACService.clear_cache()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


def require_permission(permission_code: str):
    """
    Decorator to require a specific permission

    Usage:
        @require_permission('hr:employee:read')
        def get_employees():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Get token from header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': '缺少认证信息'}), 401

            token = auth_header.split(' ')[1]
            payload = verify_token(token)

            if not payload:
                return jsonify({'error': 'Token无效或已过期'}), 401

            user_id = payload.get('user_id') or payload.get('id')

            # Check permission
            if not RBACService.has_permission(user_id, permission_code):
                return jsonify({
                    'error': '权限不足',
                    'required_permission': permission_code
                }), 403

            # Store user info in g
            g.current_user = payload
            g.user_id = user_id
            g.username = payload.get('username')

            return f(*args, **kwargs)
        return decorated
    return decorator


def require_any_permission(*permission_codes):
    """
    Decorator to require any of the given permissions

    Usage:
        @require_any_permission('hr:employee:read', 'hr:employee:update')
        def get_or_update_employees():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': '缺少认证信息'}), 401

            token = auth_header.split(' ')[1]
            payload = verify_token(token)

            if not payload:
                return jsonify({'error': 'Token无效或已过期'}), 401

            user_id = payload.get('user_id') or payload.get('id')

            if not RBACService.has_any_permission(user_id, list(permission_codes)):
                return jsonify({
                    'error': '权限不足',
                    'required_permissions': list(permission_codes)
                }), 403

            g.current_user = payload
            g.user_id = user_id
            g.username = payload.get('username')

            return f(*args, **kwargs)
        return decorated
    return decorator


def require_module_access(module: str):
    """
    Decorator to require access to a module

    Usage:
        @require_module_access('hr')
        def hr_api():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': '缺少认证信息'}), 401

            token = auth_header.split(' ')[1]
            payload = verify_token(token)

            if not payload:
                return jsonify({'error': 'Token无效或已过期'}), 401

            user_id = payload.get('user_id') or payload.get('id')

            # Check legacy permissions array first
            permissions = payload.get('permissions', [])
            if isinstance(permissions, str):
                try:
                    permissions = json.loads(permissions)
                except:
                    permissions = []

            has_legacy = module in permissions

            # Then check RBAC
            has_rbac = RBACService.has_module_access(user_id, module)

            if not has_legacy and not has_rbac:
                return jsonify({
                    'error': '无权访问此模块',
                    'module': module
                }), 403

            g.current_user = payload
            g.user_id = user_id
            g.username = payload.get('username')

            return f(*args, **kwargs)
        return decorated
    return decorator
