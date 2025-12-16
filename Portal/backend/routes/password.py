"""
Password Management API Routes - Change password, reset password
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import sys
import os
import secrets
import re

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.auth import (
    User, PasswordHistory, AuditService,
    verify_token, verify_password, hash_password
)
import shared.auth.models as auth_models

password_bp = Blueprint('password', __name__, url_prefix='/api/auth')


# Password policy constants
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL = True
PASSWORD_HISTORY_COUNT = 5  # Cannot reuse last N passwords
PASSWORD_EXPIRY_DAYS = 90  # Password expires after N days


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password against policy

    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, '密码不能为空'

    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f'密码长度至少 {PASSWORD_MIN_LENGTH} 个字符'

    if len(password) > PASSWORD_MAX_LENGTH:
        return False, f'密码长度不能超过 {PASSWORD_MAX_LENGTH} 个字符'

    if PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        return False, '密码必须包含至少一个大写字母'

    if PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        return False, '密码必须包含至少一个小写字母'

    if PASSWORD_REQUIRE_NUMBERS and not re.search(r'\d', password):
        return False, '密码必须包含至少一个数字'

    if PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        return False, '密码必须包含至少一个特殊字符 (!@#$%^&*等)'

    return True, ''


def check_password_history(user_id: int, new_password: str, session) -> bool:
    """
    Check if password was used recently

    Returns:
        True if password is OK (not in history), False if it was used recently
    """
    # Get recent password hashes
    recent_passwords = session.query(PasswordHistory).filter(
        PasswordHistory.user_id == user_id
    ).order_by(
        PasswordHistory.created_at.desc()
    ).limit(PASSWORD_HISTORY_COUNT).all()

    # Check if new password matches any recent one
    for history in recent_passwords:
        if verify_password(new_password, history.password_hash):
            return False

    return True


def save_password_history(user_id: int, password_hash: str, session):
    """Save password to history"""
    history = PasswordHistory(
        user_id=user_id,
        password_hash=password_hash,
        created_at=datetime.utcnow()
    )
    session.add(history)


def get_current_user_from_token():
    """Get current user from Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ')[1]
    return verify_token(token)


@password_bp.route('/change-password', methods=['POST'])
def change_password():
    """
    Change password for current user

    Request body:
    {
        "current_password": "string",
        "new_password": "string",
        "confirm_password": "string"
    }
    """
    user_payload = get_current_user_from_token()
    if not user_payload:
        return jsonify({'error': '请先登录'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'error': '请提供必要参数'}), 400

    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not all([current_password, new_password, confirm_password]):
        return jsonify({'error': '请填写所有密码字段'}), 400

    if new_password != confirm_password:
        return jsonify({'error': '两次输入的新密码不一致'}), 400

    # Validate new password against policy
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    user_id = user_payload.get('user_id') or user_payload.get('id')
    username = user_payload.get('username')

    session = auth_models.AuthSessionLocal()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            AuditService.log(
                action_type=AuditService.ACTION_PASSWORD_CHANGE,
                user_id=user_id,
                username=username,
                description='修改密码失败：当前密码错误',
                status='failed',
                error_message='当前密码错误',
                module='portal'
            )
            return jsonify({'error': '当前密码错误'}), 400

        # Check password history
        if not check_password_history(user_id, new_password, session):
            return jsonify({
                'error': f'不能使用最近 {PASSWORD_HISTORY_COUNT} 次使用过的密码'
            }), 400

        # Update password
        new_hash = hash_password(new_password)
        user.hashed_password = new_hash
        user.last_password_change = datetime.utcnow()
        user.password_change_required = False
        user.password_expires_at = datetime.utcnow() + timedelta(days=PASSWORD_EXPIRY_DAYS)

        # Save to password history
        save_password_history(user_id, new_hash, session)

        session.commit()

        # Log success
        AuditService.log(
            action_type=AuditService.ACTION_PASSWORD_CHANGE,
            user_id=user_id,
            username=username,
            description='用户修改密码成功',
            status='success',
            module='portal'
        )

        return jsonify({
            'message': '密码修改成功',
            'password_expires_at': user.password_expires_at.isoformat()
        }), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': f'密码修改失败: {str(e)}'}), 500
    finally:
        session.close()


@password_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Reset password for a user (admin only)

    Request body:
    {
        "user_id": int,
        "new_password": "string" (optional, will generate random if not provided)
    }
    """
    admin_payload = get_current_user_from_token()
    if not admin_payload:
        return jsonify({'error': '请先登录'}), 401

    # Check admin permission
    from shared.auth import is_admin
    if not is_admin(admin_payload.get('role', 'user')):
        return jsonify({'error': '需要管理员权限'}), 403

    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({'error': '请提供用户ID'}), 400

    target_user_id = data['user_id']
    new_password = data.get('new_password')

    # Generate random password if not provided
    if not new_password:
        new_password = secrets.token_urlsafe(12)
        generated = True
    else:
        generated = False
        # Validate provided password
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': error_msg}), 400

    admin_id = admin_payload.get('user_id') or admin_payload.get('id')
    admin_username = admin_payload.get('username')

    session = auth_models.AuthSessionLocal()
    try:
        user = session.query(User).filter_by(id=target_user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # Update password
        new_hash = hash_password(new_password)
        user.hashed_password = new_hash
        user.last_password_change = datetime.utcnow()
        user.password_change_required = True  # Force change on next login
        user.password_expires_at = datetime.utcnow() + timedelta(days=PASSWORD_EXPIRY_DAYS)

        # Reset failed login attempts and unlock
        user.failed_login_attempts = 0
        user.locked_until = None

        # Save to password history
        save_password_history(target_user_id, new_hash, session)

        session.commit()

        # Log success
        AuditService.log(
            action_type=AuditService.ACTION_PASSWORD_RESET,
            user_id=admin_id,
            username=admin_username,
            resource_type='user',
            resource_id=target_user_id,
            description=f'管理员 {admin_username} 重置了用户 {user.username} 的密码',
            status='success',
            module='portal'
        )

        response = {
            'message': '密码重置成功',
            'user_id': target_user_id,
            'username': user.username,
            'password_change_required': True
        }

        if generated:
            response['new_password'] = new_password
            response['note'] = '请将此临时密码安全地传达给用户，用户首次登录后需要修改密码'

        return jsonify(response), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': f'密码重置失败: {str(e)}'}), 500
    finally:
        session.close()


@password_bp.route('/unlock-account', methods=['POST'])
def unlock_account():
    """
    Unlock a locked user account (admin only)

    Request body:
    {
        "user_id": int
    }
    """
    admin_payload = get_current_user_from_token()
    if not admin_payload:
        return jsonify({'error': '请先登录'}), 401

    from shared.auth import is_admin
    if not is_admin(admin_payload.get('role', 'user')):
        return jsonify({'error': '需要管理员权限'}), 403

    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({'error': '请提供用户ID'}), 400

    target_user_id = data['user_id']
    admin_id = admin_payload.get('user_id') or admin_payload.get('id')
    admin_username = admin_payload.get('username')

    session = auth_models.AuthSessionLocal()
    try:
        user = session.query(User).filter_by(id=target_user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # Unlock account
        user.failed_login_attempts = 0
        user.locked_until = None

        session.commit()

        # Log success
        AuditService.log(
            action_type='account_unlock',
            user_id=admin_id,
            username=admin_username,
            resource_type='user',
            resource_id=target_user_id,
            description=f'管理员 {admin_username} 解锁了用户 {user.username} 的账户',
            status='success',
            module='portal'
        )

        return jsonify({
            'message': '账户解锁成功',
            'user_id': target_user_id,
            'username': user.username
        }), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': f'解锁失败: {str(e)}'}), 500
    finally:
        session.close()


@password_bp.route('/password-policy', methods=['GET'])
def get_password_policy():
    """Get current password policy"""
    return jsonify({
        'min_length': PASSWORD_MIN_LENGTH,
        'max_length': PASSWORD_MAX_LENGTH,
        'require_uppercase': PASSWORD_REQUIRE_UPPERCASE,
        'require_lowercase': PASSWORD_REQUIRE_LOWERCASE,
        'require_numbers': PASSWORD_REQUIRE_NUMBERS,
        'require_special': PASSWORD_REQUIRE_SPECIAL,
        'history_count': PASSWORD_HISTORY_COUNT,
        'expiry_days': PASSWORD_EXPIRY_DAYS
    }), 200


@password_bp.route('/password-status', methods=['GET'])
def get_password_status():
    """Get password status for current user"""
    user_payload = get_current_user_from_token()
    if not user_payload:
        return jsonify({'error': '请先登录'}), 401

    user_id = user_payload.get('user_id') or user_payload.get('id')

    session = auth_models.AuthSessionLocal()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        is_expired = user.is_password_expired()
        days_until_expiry = None

        if user.password_expires_at:
            delta = user.password_expires_at - datetime.utcnow()
            days_until_expiry = max(0, delta.days)

        return jsonify({
            'password_change_required': user.password_change_required or False,
            'password_expired': is_expired,
            'password_expires_at': user.password_expires_at.isoformat() if user.password_expires_at else None,
            'days_until_expiry': days_until_expiry,
            'last_password_change': user.last_password_change.isoformat() if user.last_password_change else None,
            'account_locked': user.is_account_locked(),
            'locked_until': user.locked_until.isoformat() if user.locked_until else None,
            'failed_login_attempts': user.failed_login_attempts or 0
        }), 200

    finally:
        session.close()
