from flask import Blueprint, request, jsonify
import sys
import os
import json

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.auth import User, hash_password, verify_token
import shared.auth.models as auth_models
from functools import wraps

users_bp = Blueprint('users', __name__, url_prefix='/users')


def require_admin(f):
    '''Decorator to require admin authentication'''
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


# ============ 批量操作 API ============

@users_bp.route('/batch/toggle-active', methods=['POST'])
@require_admin
def batch_toggle_active():
    '''批量启用/禁用用户'''
    data = request.get_json()

    if not data or 'user_ids' not in data or 'is_active' not in data:
        return jsonify({'error': '请提供用户ID列表和目标状态'}), 400

    user_ids = data['user_ids']
    is_active = data['is_active']
    current_user_id = request.current_user.get('user_id') or request.current_user.get('id')

    if not user_ids or not isinstance(user_ids, list):
        return jsonify({'error': '用户ID列表不能为空'}), 400

    # 不能禁用自己
    if not is_active and current_user_id in user_ids:
        return jsonify({'error': '不能禁用自己的账户'}), 400

    auth_session = auth_models.AuthSessionLocal()
    try:
        updated = 0
        for user_id in user_ids:
            user = auth_session.query(User).filter(User.id == user_id).first()
            if user and user.id != current_user_id:
                user.is_active = is_active
                updated += 1

        auth_session.commit()

        status = '启用' if is_active else '禁用'
        return jsonify({
            'message': f'成功{status} {updated} 个用户',
            'updated_count': updated
        })
    except Exception as e:
        auth_session.rollback()
        return jsonify({'error': f'操作失败: {str(e)}'}), 500
    finally:
        auth_session.close()


@users_bp.route('/batch/assign-role', methods=['POST'])
@require_admin
def batch_assign_role():
    '''批量分配角色'''
    data = request.get_json()

    if not data or 'user_ids' not in data or 'role' not in data:
        return jsonify({'error': '请提供用户ID列表和角色'}), 400

    user_ids = data['user_ids']
    role = data['role']
    current_user_id = request.current_user.get('user_id') or request.current_user.get('id')
    current_role = request.current_user.get('role', 'user')

    valid_roles = ['user', 'supervisor', 'admin', 'super_admin']
    if role not in valid_roles:
        return jsonify({'error': f'无效的角色，可选: {valid_roles}'}), 400

    # 只有 super_admin 可以分配 super_admin 角色
    if role == 'super_admin' and current_role != 'super_admin':
        return jsonify({'error': '只有超级管理员可以分配超级管理员角色'}), 403

    if not user_ids or not isinstance(user_ids, list):
        return jsonify({'error': '用户ID列表不能为空'}), 400

    auth_session = auth_models.AuthSessionLocal()
    try:
        updated = 0
        for user_id in user_ids:
            user = auth_session.query(User).filter(User.id == user_id).first()
            if user:
                # 不能降级 super_admin（除非自己是 super_admin）
                if user.role == 'super_admin' and current_role != 'super_admin':
                    continue
                user.role = role
                # 同步 is_admin 字段
                user.is_admin = role in ['admin', 'super_admin']
                updated += 1

        auth_session.commit()

        return jsonify({
            'message': f'成功为 {updated} 个用户分配角色',
            'updated_count': updated
        })
    except Exception as e:
        auth_session.rollback()
        return jsonify({'error': f'操作失败: {str(e)}'}), 500
    finally:
        auth_session.close()


@users_bp.route('/batch/assign-permissions', methods=['POST'])
@require_admin
def batch_assign_permissions():
    '''批量分配系统权限'''
    data = request.get_json()

    if not data or 'user_ids' not in data or 'permissions' not in data:
        return jsonify({'error': '请提供用户ID列表和权限列表'}), 400

    user_ids = data['user_ids']
    permissions = data['permissions']
    mode = data.get('mode', 'replace')  # replace: 替换, add: 追加, remove: 移除

    if not user_ids or not isinstance(user_ids, list):
        return jsonify({'error': '用户ID列表不能为空'}), 400

    if not isinstance(permissions, list):
        return jsonify({'error': '权限必须是数组'}), 400

    auth_session = auth_models.AuthSessionLocal()
    try:
        updated = 0
        for user_id in user_ids:
            user = auth_session.query(User).filter(User.id == user_id).first()
            if user:
                current_perms = []
                if user.permissions:
                    try:
                        current_perms = json.loads(user.permissions)
                    except (json.JSONDecodeError, TypeError):
                        current_perms = []

                if mode == 'replace':
                    new_perms = permissions
                elif mode == 'add':
                    new_perms = list(set(current_perms + permissions))
                elif mode == 'remove':
                    new_perms = [p for p in current_perms if p not in permissions]
                else:
                    new_perms = permissions

                user.permissions = json.dumps(new_perms)
                updated += 1

        auth_session.commit()

        mode_text = {'replace': '设置', 'add': '添加', 'remove': '移除'}.get(mode, '更新')
        return jsonify({
            'message': f'成功为 {updated} 个用户{mode_text}权限',
            'updated_count': updated
        })
    except Exception as e:
        auth_session.rollback()
        return jsonify({'error': f'操作失败: {str(e)}'}), 500
    finally:
        auth_session.close()


@users_bp.route('/batch/delete', methods=['POST'])
@require_admin
def batch_delete():
    '''批量删除用户'''
    data = request.get_json()

    if not data or 'user_ids' not in data:
        return jsonify({'error': '请提供用户ID列表'}), 400

    user_ids = data['user_ids']
    current_user_id = request.current_user.get('user_id') or request.current_user.get('id')
    current_role = request.current_user.get('role', 'user')

    if not user_ids or not isinstance(user_ids, list):
        return jsonify({'error': '用户ID列表不能为空'}), 400

    # 不能删除自己
    if current_user_id in user_ids:
        return jsonify({'error': '不能删除自己的账户'}), 400

    auth_session = auth_models.AuthSessionLocal()
    try:
        deleted = 0
        skipped = []

        for user_id in user_ids:
            user = auth_session.query(User).filter(User.id == user_id).first()
            if user:
                # 不能删除 super_admin（除非自己是 super_admin）
                if user.role == 'super_admin' and current_role != 'super_admin':
                    skipped.append({'id': user_id, 'username': user.username, 'reason': '无权删除超级管理员'})
                    continue
                auth_session.delete(user)
                deleted += 1

        auth_session.commit()

        result = {
            'message': f'成功删除 {deleted} 个用户',
            'deleted_count': deleted
        }
        if skipped:
            result['skipped'] = skipped

        return jsonify(result)
    except Exception as e:
        auth_session.rollback()
        return jsonify({'error': f'操作失败: {str(e)}'}), 500
    finally:
        auth_session.close()


@users_bp.route('/batch/reset-password', methods=['POST'])
@require_admin
def batch_reset_password():
    '''批量重置密码'''
    data = request.get_json()

    if not data or 'user_ids' not in data:
        return jsonify({'error': '请提供用户ID列表'}), 400

    user_ids = data['user_ids']
    new_password = data.get('new_password', 'jzc123456')  # 默认密码

    if len(new_password) < 6:
        return jsonify({'error': '密码至少6个字符'}), 400

    if not user_ids or not isinstance(user_ids, list):
        return jsonify({'error': '用户ID列表不能为空'}), 400

    auth_session = auth_models.AuthSessionLocal()
    try:
        updated = 0
        hashed = hash_password(new_password)

        for user_id in user_ids:
            user = auth_session.query(User).filter(User.id == user_id).first()
            if user:
                user.hashed_password = hashed
                # 标记需要修改密码
                user.password_change_required = True
                updated += 1

        auth_session.commit()

        return jsonify({
            'message': f'成功重置 {updated} 个用户的密码',
            'updated_count': updated,
            'default_password': new_password
        })
    except Exception as e:
        auth_session.rollback()
        return jsonify({'error': f'操作失败: {str(e)}'}), 500
    finally:
        auth_session.close()


@users_bp.route('/batch/update-org', methods=['POST'])
@require_admin
def batch_update_org():
    '''批量更新组织架构信息'''
    data = request.get_json()

    if not data or 'user_ids' not in data:
        return jsonify({'error': '请提供用户ID列表'}), 400

    user_ids = data['user_ids']

    if not user_ids or not isinstance(user_ids, list):
        return jsonify({'error': '用户ID列表不能为空'}), 400

    # 至少提供一项组织信息
    org_fields = ['department_id', 'department_name', 'position_id', 'position_name', 'team_id', 'team_name']
    has_org_data = any(field in data for field in org_fields)
    if not has_org_data:
        return jsonify({'error': '请至少提供一项组织架构信息'}), 400

    auth_session = auth_models.AuthSessionLocal()
    try:
        updated = 0

        for user_id in user_ids:
            user = auth_session.query(User).filter(User.id == user_id).first()
            if user:
                if 'department_id' in data:
                    user.department_id = data['department_id']
                if 'department_name' in data:
                    user.department_name = data['department_name']
                if 'position_id' in data:
                    user.position_id = data['position_id']
                if 'position_name' in data:
                    user.position_name = data['position_name']
                if 'team_id' in data:
                    user.team_id = data['team_id']
                if 'team_name' in data:
                    user.team_name = data['team_name']
                updated += 1

        auth_session.commit()

        return jsonify({
            'message': f'成功更新 {updated} 个用户的组织信息',
            'updated_count': updated
        })
    except Exception as e:
        auth_session.rollback()
        return jsonify({'error': f'操作失败: {str(e)}'}), 500
    finally:
        auth_session.close()
