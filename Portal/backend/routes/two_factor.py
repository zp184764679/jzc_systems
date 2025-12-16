"""
Two-Factor Authentication Routes
Provides endpoints for 2FA setup, verification, and management
"""
from flask import Blueprint, request, jsonify, g
from functools import wraps
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.auth.models import User, TwoFactorAuth, TwoFactorBackupCode, init_auth_db, AuthSessionLocal
from shared.auth.two_factor_service import TwoFactorService
from shared.auth.jwt_utils import verify_token, create_token_from_user


two_factor_bp = Blueprint('two_factor', __name__, url_prefix='/api/2fa')


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未授权'}), 401

        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        if not payload:
            return jsonify({'code': 401, 'message': 'Token 无效或已过期'}), 401

        g.user = payload
        return f(*args, **kwargs)
    return decorated


def get_db_session():
    """Get database session"""
    if AuthSessionLocal is None:
        init_auth_db()
    return AuthSessionLocal()


@two_factor_bp.route('/status', methods=['GET'])
@require_auth
def get_2fa_status():
    """Get current 2FA status for the logged-in user"""
    session = get_db_session()
    try:
        service = TwoFactorService(session)
        status = service.get_2fa_status(g.user['user_id'])
        return jsonify({
            'code': 0,
            'data': status
        })
    finally:
        session.close()


@two_factor_bp.route('/setup', methods=['POST'])
@require_auth
def setup_2fa():
    """
    Set up 2FA for the current user
    Generates a new secret and backup codes
    Returns QR code URI for authenticator app setup
    """
    session = get_db_session()
    try:
        service = TwoFactorService(session)
        result = service.setup_2fa(g.user['user_id'], g.user['username'])

        return jsonify({
            'code': 0,
            'message': '2FA 设置已生成，请使用验证码完成启用',
            'data': {
                'qr_uri': result['qr_uri'],
                'secret': result['secret'],  # For manual entry
                'backup_codes': result['backup_codes']
            }
        })
    except ValueError as e:
        return jsonify({
            'code': 1,
            'message': str(e)
        }), 400
    finally:
        session.close()


@two_factor_bp.route('/verify-setup', methods=['POST'])
@require_auth
def verify_and_enable_2fa():
    """
    Verify the TOTP code and enable 2FA
    This should be called after setup with the code from the authenticator app
    """
    data = request.get_json()
    code = data.get('code')

    if not code:
        return jsonify({
            'code': 1,
            'message': '请输入验证码'
        }), 400

    session = get_db_session()
    try:
        service = TwoFactorService(session)
        if service.verify_and_enable(g.user['user_id'], code):
            return jsonify({
                'code': 0,
                'message': '双因素认证已成功启用'
            })
        else:
            return jsonify({
                'code': 1,
                'message': '验证码错误，请重试'
            }), 400
    except ValueError as e:
        return jsonify({
            'code': 1,
            'message': str(e)
        }), 400
    finally:
        session.close()


@two_factor_bp.route('/verify', methods=['POST'])
def verify_2fa_code():
    """
    Verify a TOTP code during login
    Called after initial password authentication
    """
    data = request.get_json()
    user_id = data.get('user_id')
    code = data.get('code')
    is_backup = data.get('is_backup', False)

    if not user_id or not code:
        return jsonify({
            'code': 1,
            'message': '缺少必要参数'
        }), 400

    session = get_db_session()
    try:
        service = TwoFactorService(session)

        if is_backup:
            # Verify backup code
            if service.verify_backup_code_for_login(user_id, code):
                # Get user and generate token
                user = session.query(User).filter_by(id=user_id).first()
                if user:
                    token = create_token_from_user(user.to_dict())
                    return jsonify({
                        'code': 0,
                        'message': '验证成功（备用码）',
                        'data': {
                            'token': token,
                            'user': user.to_dict()
                        }
                    })
            return jsonify({
                'code': 1,
                'message': '备用码无效或已使用'
            }), 400
        else:
            # Verify TOTP code
            if service.verify_code(user_id, code):
                # Get user and generate token
                user = session.query(User).filter_by(id=user_id).first()
                if user:
                    token = create_token_from_user(user.to_dict())
                    return jsonify({
                        'code': 0,
                        'message': '验证成功',
                        'data': {
                            'token': token,
                            'user': user.to_dict()
                        }
                    })
            return jsonify({
                'code': 1,
                'message': '验证码错误，请重试'
            }), 400
    finally:
        session.close()


@two_factor_bp.route('/disable', methods=['POST'])
@require_auth
def disable_2fa():
    """
    Disable 2FA for the current user
    Requires current password verification
    """
    data = request.get_json()
    password = data.get('password')
    code = data.get('code')

    if not password:
        return jsonify({
            'code': 1,
            'message': '请输入密码'
        }), 400

    session = get_db_session()
    try:
        # Verify password
        user = session.query(User).filter_by(id=g.user['user_id']).first()
        if not user:
            return jsonify({
                'code': 1,
                'message': '用户不存在'
            }), 404

        from shared.auth.password_utils import verify_password
        if not verify_password(password, user.hashed_password):
            return jsonify({
                'code': 1,
                'message': '密码错误'
            }), 400

        # Verify 2FA code if provided
        service = TwoFactorService(session)
        if code:
            if not service.verify_code(g.user['user_id'], code):
                return jsonify({
                    'code': 1,
                    'message': '验证码错误'
                }), 400

        # Disable 2FA
        if service.disable_2fa(g.user['user_id']):
            return jsonify({
                'code': 0,
                'message': '双因素认证已禁用'
            })
        else:
            return jsonify({
                'code': 1,
                'message': '禁用失败，2FA 可能未启用'
            }), 400
    finally:
        session.close()


@two_factor_bp.route('/backup-codes', methods=['GET'])
@require_auth
def get_backup_codes_status():
    """Get the count of remaining backup codes"""
    session = get_db_session()
    try:
        remaining = session.query(TwoFactorBackupCode).filter_by(
            user_id=g.user['user_id'],
            is_used=False
        ).count()

        return jsonify({
            'code': 0,
            'data': {
                'remaining': remaining,
                'total': 10
            }
        })
    finally:
        session.close()


@two_factor_bp.route('/backup-codes/regenerate', methods=['POST'])
@require_auth
def regenerate_backup_codes():
    """
    Regenerate backup codes
    Requires current TOTP code verification
    """
    data = request.get_json()
    code = data.get('code')

    if not code:
        return jsonify({
            'code': 1,
            'message': '请输入当前验证码'
        }), 400

    session = get_db_session()
    try:
        service = TwoFactorService(session)

        # Verify current TOTP code
        if not service.verify_code(g.user['user_id'], code):
            return jsonify({
                'code': 1,
                'message': '验证码错误'
            }), 400

        # Regenerate backup codes
        new_codes = service.regenerate_backup_codes(g.user['user_id'])

        return jsonify({
            'code': 0,
            'message': '备用码已重新生成',
            'data': {
                'backup_codes': new_codes
            }
        })
    except ValueError as e:
        return jsonify({
            'code': 1,
            'message': str(e)
        }), 400
    finally:
        session.close()


@two_factor_bp.route('/check-required/<int:user_id>', methods=['GET'])
def check_2fa_required(user_id):
    """
    Check if 2FA is required for a user
    Called during login process
    """
    session = get_db_session()
    try:
        service = TwoFactorService(session)
        required = service.is_2fa_required(user_id)

        return jsonify({
            'code': 0,
            'data': {
                'required': required
            }
        })
    finally:
        session.close()
