"""
Portal Backend API - 统一认证服务
提供员工和供应商登录，生成JWT token用于SSO
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file before importing shared.auth
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from shared.auth import (
    User, init_auth_db,
    create_token_from_user, verify_password,
    AuditService
)
import shared.auth.models as auth_models
from routes.system import system_bp
from routes.projects import projects_bp
from routes.tasks import tasks_bp
from routes.files import files_bp
from routes.members import members_bp
from routes.notifications import notifications_bp
from routes.issues import issues_bp
from routes.phases import phases_bp
from routes.integration import integration_bp
from routes.audit import audit_bp
from routes.password import password_bp
from routes.rbac import rbac_bp
from routes.two_factor import two_factor_bp
from routes.sessions import sessions_bp
from routes.announcements import announcements_bp
from models import init_db

app = Flask(__name__)

# Configure CORS - 安全修复：仅允许已知域名
cors_origins = os.getenv('CORS_ORIGINS', '')
if cors_origins:
    cors_origins_list = [o.strip() for o in cors_origins.split(',') if o.strip()]
else:
    # 默认允许的域名（本地开发 + 生产环境）
    cors_origins_list = [
        # 本地开发 - 所有子系统前端端口
        'http://localhost:6000',   # Portal
        'http://localhost:6001',   # HR
        'http://localhost:6002',   # CRM
        'http://localhost:6003',   # Account
        'http://localhost:6005',   # 报价
        'http://localhost:7000',   # SCM
        'http://localhost:7100',   # SHM
        'http://localhost:7200',   # EAM
        'http://localhost:7300',   # MES
        'http://localhost:7500',   # 采购
        'http://127.0.0.1:6000',
        'http://127.0.0.1:6001',
        'http://127.0.0.1:6002',
        'http://127.0.0.1:6003',
        'http://127.0.0.1:6005',
        'http://127.0.0.1:7000',
        'http://127.0.0.1:7100',
        'http://127.0.0.1:7200',
        'http://127.0.0.1:7300',
        'http://127.0.0.1:7500',
        # 生产环境
        'http://61.145.212.28:3000',
        'http://61.145.212.28',
        'https://jzchardware.cn',
    ]

CORS(app, resources={
    r"/api/*": {
        "origins": cors_origins_list,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Initialize databases
init_auth_db()
init_db()

# Register blueprints
app.register_blueprint(system_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(files_bp)
app.register_blueprint(members_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(issues_bp)
app.register_blueprint(phases_bp)
app.register_blueprint(integration_bp)
app.register_blueprint(audit_bp)
app.register_blueprint(password_bp)
app.register_blueprint(rbac_bp)
app.register_blueprint(two_factor_bp)
app.register_blueprint(sessions_bp)
app.register_blueprint(announcements_bp)


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Employee login endpoint"""
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': '请提供用户名和密码'}), 400

    username = data['username']
    password = data['password']

    session = auth_models.AuthSessionLocal()
    try:
        # Find user by username
        user = session.query(User).filter_by(username=username).first()

        if not user:
            # Log failed login attempt (unknown user)
            AuditService.log_login(
                user_id=0,
                username=username,
                success=False,
                failure_reason='用户不存在',
                module='portal'
            )
            return jsonify({'error': '用户名或密码错误'}), 401

        # Check if account is locked
        # P2-17: is_account_locked() 会自动重置过期的锁定状态
        if user.is_account_locked():
            AuditService.log_login(
                user_id=user.id,
                username=username,
                success=False,
                failure_reason='账户已锁定',
                module='portal'
            )
            return jsonify({
                'error': '账户已被锁定，请稍后重试或联系管理员',
                'locked_until': user.locked_until.isoformat() if user.locked_until else None
            }), 423  # P3-27: 使用 423 Locked 状态码
        else:
            # P2-17: 如果锁定刚过期，保存重置的状态
            session.commit()

        # Check if user is active
        if not user.is_active:
            AuditService.log_login(
                user_id=user.id,
                username=username,
                success=False,
                failure_reason='账户已禁用',
                module='portal'
            )
            return jsonify({'error': '账户已被禁用，请联系管理员'}), 403

        # Verify password
        if not verify_password(password, user.hashed_password):
            # Increment failed login attempts
            user.increment_failed_login()
            session.commit()

            AuditService.log_login(
                user_id=user.id,
                username=username,
                success=False,
                failure_reason='密码错误',
                module='portal'
            )

            remaining = 5 - user.failed_login_attempts
            if remaining > 0:
                return jsonify({
                    'error': f'用户名或密码错误，还有 {remaining} 次尝试机会'
                }), 401
            else:
                return jsonify({
                    'error': '密码错误次数过多，账户已被锁定30分钟'
                }), 401

        # Only allow employees to login here
        if user.user_type != 'employee':
            return jsonify({'error': '请使用供应商登录入口'}), 403

        # Check if 2FA is required
        from shared.auth.two_factor_service import TwoFactorService
        two_fa_service = TwoFactorService(session)
        requires_2fa = two_fa_service.is_2fa_required(user.id)

        if requires_2fa:
            # Return partial login response requiring 2FA verification
            return jsonify({
                'message': '请输入双因素验证码',
                'requires_2fa': True,
                'user_id': user.id,
                'username': user.username
            }), 200

        # Check if password change is required
        password_change_required = user.password_change_required or user.is_password_expired()

        # Update last login info and reset failed attempts
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        user.update_last_login(ip_address=client_ip)
        session.commit()

        # Generate JWT token
        user_dict = user.to_dict()
        token = create_token_from_user(user_dict)

        # Log successful login
        AuditService.log_login(
            user_id=user.id,
            username=username,
            success=True,
            token=token,
            module='portal'
        )

        response_data = {
            'message': '登录成功',
            'token': token,
            'user': user_dict
        }

        # Add password change warning if needed
        if password_change_required:
            response_data['password_change_required'] = True
            response_data['password_warning'] = '您的密码已过期或需要修改，请尽快修改密码'

        return jsonify(response_data), 200

    except Exception as e:
        import logging
        logging.error(f"Login error: {e}")
        return jsonify({'error': '登录失败，请稍后重试'}), 500
    finally:
        session.close()


@app.route('/api/auth/supplier-login', methods=['POST'])
def supplier_login():
    """Supplier login endpoint"""
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': '请提供用户名和密码'}), 400

    username = data['username']
    password = data['password']

    session = auth_models.AuthSessionLocal()
    try:
        # Find user by username
        user = session.query(User).filter_by(username=username).first()

        if not user:
            # Log failed login attempt (unknown user)
            AuditService.log_login(
                user_id=0,
                username=username,
                success=False,
                failure_reason='用户不存在',
                module='portal'
            )
            return jsonify({'error': '用户名或密码错误'}), 401

        # Check if account is locked
        # P2-17: is_account_locked() 会自动重置过期的锁定状态
        if user.is_account_locked():
            AuditService.log_login(
                user_id=user.id,
                username=username,
                success=False,
                failure_reason='账户已锁定',
                module='portal'
            )
            return jsonify({
                'error': '账户已被锁定，请稍后重试或联系管理员',
                'locked_until': user.locked_until.isoformat() if user.locked_until else None
            }), 423  # P3-27: 使用 423 Locked 状态码
        else:
            # P2-17: 如果锁定刚过期，保存重置的状态
            session.commit()

        # Check if user is active
        if not user.is_active:
            AuditService.log_login(
                user_id=user.id,
                username=username,
                success=False,
                failure_reason='账户已禁用',
                module='portal'
            )
            return jsonify({'error': '账户已被禁用，请联系管理员'}), 403

        # Verify password
        if not verify_password(password, user.hashed_password):
            # Increment failed login attempts
            user.increment_failed_login()
            session.commit()

            AuditService.log_login(
                user_id=user.id,
                username=username,
                success=False,
                failure_reason='密码错误',
                module='portal'
            )

            remaining = 5 - user.failed_login_attempts
            if remaining > 0:
                return jsonify({
                    'error': f'用户名或密码错误，还有 {remaining} 次尝试机会'
                }), 401
            else:
                return jsonify({
                    'error': '密码错误次数过多，账户已被锁定30分钟'
                }), 401

        # Only allow suppliers to login here
        if user.user_type != 'supplier':
            return jsonify({'error': '请使用员工登录入口'}), 403

        # Update last login info and reset failed attempts
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        user.update_last_login(ip_address=client_ip)
        session.commit()

        # Generate JWT token
        user_dict = user.to_dict()
        token = create_token_from_user(user_dict)

        # Log successful login
        AuditService.log_login(
            user_id=user.id,
            username=username,
            success=True,
            token=token,
            module='portal'
        )

        return jsonify({
            'message': '登录成功',
            'token': token,
            'user': user_dict
        }), 200

    except Exception as e:
        import logging
        logging.error(f"Supplier login error: {e}")
        return jsonify({'error': '登录失败，请稍后重试'}), 500
    finally:
        session.close()


@app.route('/api/auth/verify', methods=['POST'])
def verify_token_endpoint():
    """Verify JWT token"""
    from shared.auth import verify_token

    data = request.get_json()
    if not data or 'token' not in data:
        return jsonify({'error': '缺少token'}), 400

    token = data['token']
    payload = verify_token(token)

    if not payload:
        return jsonify({'error': 'Token无效或已过期'}), 401

    return jsonify({
        'valid': True,
        'user': payload
    }), 200


@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current user info from token"""
    from shared.auth import verify_token

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': '缺少认证信息'}), 401

    parts = auth_header.split(' ')
    if len(parts) != 2:
        return jsonify({'error': '无效的认证头格式'}), 401
    token = parts[1]
    payload = verify_token(token)

    if not payload:
        return jsonify({'error': 'Token无效或已过期'}), 401

    # 从数据库获取最新用户信息
    session = auth_models.AuthSessionLocal()
    try:
        user_id = payload.get('user_id') or payload.get('id')
        user = session.query(User).filter_by(id=user_id).first()

        if not user:
            return jsonify({'error': '用户不存在'}), 404

        if not user.is_active:
            return jsonify({'error': '账户已被禁用'}), 403

        return jsonify(user.to_dict()), 200
    finally:
        session.close()


@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh JWT token"""
    from shared.auth import verify_token

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': '缺少认证信息'}), 401

    parts = auth_header.split(' ')
    if len(parts) != 2:
        return jsonify({'error': '无效的认证头格式'}), 401
    token = parts[1]
    payload = verify_token(token)

    if not payload:
        return jsonify({'error': 'Token无效或已过期'}), 401

    # 从数据库获取最新用户信息并生成新 token
    session = auth_models.AuthSessionLocal()
    try:
        user_id = payload.get('user_id') or payload.get('id')
        user = session.query(User).filter_by(id=user_id).first()

        if not user:
            return jsonify({'error': '用户不存在'}), 404

        if not user.is_active:
            return jsonify({'error': '账户已被禁用'}), 403

        # 生成新 token
        user_dict = user.to_dict()
        new_token = create_token_from_user(user_dict)

        return jsonify({
            'token': new_token,
            'user': user_dict
        }), 200
    finally:
        session.close()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'portal-backend'}), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'Portal Backend API',
        'version': '1.0.0',
        'endpoints': {
            'employee_login': '/api/auth/login',
            'supplier_login': '/api/auth/supplier-login',
            'verify_token': '/api/auth/verify',
            'get_current_user': '/api/auth/me',
            'refresh_token': '/api/auth/refresh',
            'health': '/health'
        }
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 3002))
    # 安全修复：从环境变量读取 debug 模式，默认关闭
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"Portal Backend API starting on port {port}")
    print(f"Employee Login: http://localhost:{port}/api/auth/login")
    print(f"Supplier Login: http://localhost:{port}/api/auth/supplier-login")
    print(f"Debug mode: {debug_mode}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
