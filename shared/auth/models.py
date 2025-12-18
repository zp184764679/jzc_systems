"""
Shared user model for authentication
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index, BigInteger, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import json

Base = declarative_base()

# Export Base as AuthBase for RBAC models
AuthBase = Base

# Global engine reference for RBAC models
AuthEngine = None


class User(Base):
    """User model for authentication"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    emp_no = Column(String(50))  # Employee number

    # User type: 'employee' or 'supplier'
    user_type = Column(String(20), default='employee', nullable=False)

    # Role levels (for employees): user, supervisor, admin, super_admin
    # For suppliers, this field is not used
    role = Column(String(20), default='user')

    # System permissions: JSON array of accessible systems ['hr', 'quotation', '采购', 'account']
    # For suppliers, only ['采购'] is meaningful
    permissions = Column(String)

    # Supplier-specific field: reference to supplier ID in caigou system
    supplier_id = Column(Integer, nullable=True)

    # Organization structure fields (reference to HR system)
    department_id = Column(Integer, nullable=True)  # 部门ID
    department_name = Column(String(100), nullable=True)  # 部门名称（冗余存储便于查询）
    position_id = Column(Integer, nullable=True)  # 岗位ID
    position_name = Column(String(100), nullable=True)  # 岗位名称
    team_id = Column(Integer, nullable=True)  # 团队ID
    team_name = Column(String(100), nullable=True)  # 团队名称

    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # Deprecated, kept for backward compatibility
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Password policy fields
    password_expires_at = Column(DateTime, nullable=True)  # 密码过期时间
    last_password_change = Column(DateTime, nullable=True)  # 上次修改密码时间
    password_change_required = Column(Boolean, default=False)  # 是否需要修改密码

    # Login security fields
    failed_login_attempts = Column(Integer, default=0)  # 登录失败次数
    locked_until = Column(DateTime, nullable=True)  # 账户锁定截止时间
    last_failed_attempt_at = Column(DateTime, nullable=True)  # P2-22: 最后一次失败尝试时间
    last_login_at = Column(DateTime, nullable=True)  # 上次登录时间
    last_login_ip = Column(String(45), nullable=True)  # 上次登录 IP

    def to_dict(self):
        """Convert user to dictionary (excluding password)"""
        # Parse permissions JSON
        try:
            perms = json.loads(self.permissions) if self.permissions else []
        except (json.JSONDecodeError, TypeError, ValueError):
            perms = []

        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'emp_no': self.emp_no,
            'user_type': self.user_type,
            'role': self.role,
            'permissions': perms,
            'supplier_id': self.supplier_id,
            'department_id': self.department_id,
            'department_name': self.department_name,
            'position_id': self.position_id,
            'position_name': self.position_name,
            'team_id': self.team_id,
            'team_name': self.team_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # Password policy fields
            'password_expires_at': self.password_expires_at.isoformat() if self.password_expires_at else None,
            'last_password_change': self.last_password_change.isoformat() if self.last_password_change else None,
            'password_change_required': self.password_change_required,
            # Login security fields
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'is_locked': self.is_account_locked()
        }

    def is_supplier(self):
        """Check if user is a supplier"""
        return self.user_type == 'supplier'

    def is_employee(self):
        """Check if user is an employee"""
        return self.user_type == 'employee'

    def has_permission(self, system_name):
        """Check if user has permission to access a system"""
        try:
            perms = json.loads(self.permissions) if self.permissions else []
            return system_name in perms
        except (json.JSONDecodeError, TypeError, ValueError):
            return False

    def get_role_level(self):
        """Get role level (higher number = higher privilege)"""
        ROLE_LEVELS = {
            'user': 0,
            'supervisor': 0.5,
            'admin': 1,
            'super_admin': 2
        }
        return ROLE_LEVELS.get(self.role, 0)

    def is_account_locked(self):
        """Check if account is currently locked
        P2-17: 如果锁定已过期，自动重置失败计数
        """
        if self.locked_until is None:
            return False
        if datetime.utcnow() >= self.locked_until:
            # P2-17: 锁定已过期，重置失败计数
            self.failed_login_attempts = 0
            self.locked_until = None
            return False
        return True

    def is_password_expired(self):
        """Check if password has expired"""
        if self.password_expires_at is None:
            return False
        return datetime.utcnow() > self.password_expires_at

    def increment_failed_login(self, lockout_threshold=5, lockout_minutes=30):
        """Increment failed login attempts and lock if threshold reached"""
        self.failed_login_attempts = (self.failed_login_attempts or 0) + 1
        self.last_failed_attempt_at = datetime.utcnow()  # P2-22: 记录失败时间
        if self.failed_login_attempts >= lockout_threshold:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
        return self.failed_login_attempts

    def reset_failed_login(self):
        """Reset failed login attempts after successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None

    def update_last_login(self, ip_address=None):
        """Update last login timestamp and IP"""
        self.last_login_at = datetime.utcnow()
        if ip_address:
            self.last_login_ip = ip_address
        self.reset_failed_login()


# Database setup - MySQL configuration
# 注意: 配置在 init_auth_db() 调用时读取环境变量，支持 load_dotenv 延迟加载
AUTH_DB_USER = None
AUTH_DB_PASSWORD = None
AUTH_DB_HOST = None
AUTH_DB_NAME = None


def _get_db_config():
    """Get database configuration from environment variables (reads at call time)"""
    import logging
    logger = logging.getLogger(__name__)

    db_user = os.getenv('AUTH_DB_USER')
    db_password = os.getenv('AUTH_DB_PASSWORD')
    db_host = os.getenv('AUTH_DB_HOST', 'localhost')
    db_name = os.getenv('AUTH_DB_NAME', 'account')

    # 验证必须的数据库凭证
    if not db_user or not db_password:
        if os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG", "").lower() == "true":
            logger.warning("AUTH_DB_USER/AUTH_DB_PASSWORD 未设置，使用开发默认值")
            db_user = db_user or "app"
            db_password = db_password or "app"
        else:
            raise RuntimeError("AUTH_DB_USER 和 AUTH_DB_PASSWORD 环境变量必须设置（生产环境）")

    # P2-21: 移除敏感信息日志打印，仅在调试模式下打印非敏感信息
    logger.debug(f"[Auth] Database config: host={db_host}, db={db_name}")
    return db_user, db_password, db_host, db_name

auth_engine = None
AuthSessionLocal = None


def init_auth_db():
    """Initialize authentication database (MySQL)"""
    global auth_engine, AuthSessionLocal, AuthEngine, AUTH_DB_USER, AUTH_DB_PASSWORD, AUTH_DB_HOST, AUTH_DB_NAME

    # Get database configuration from environment (reads at call time, after load_dotenv)
    AUTH_DB_USER, AUTH_DB_PASSWORD, AUTH_DB_HOST, AUTH_DB_NAME = _get_db_config()

    # Create MySQL engine
    db_url = f'mysql+pymysql://{AUTH_DB_USER}:{AUTH_DB_PASSWORD}@{AUTH_DB_HOST}/{AUTH_DB_NAME}?charset=utf8mb4'
    auth_engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )

    # Set global engine reference for RBAC models
    AuthEngine = auth_engine

    # Create session
    AuthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)

    # Create tables if they don't exist
    Base.metadata.create_all(bind=auth_engine)

    # Initialize RBAC tables
    try:
        from .rbac_models import init_rbac_tables, init_default_roles_and_permissions
        init_rbac_tables()
        init_default_roles_and_permissions()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"RBAC tables init: {e}")

    # 安全修复：仅在开发环境创建默认管理员，生产环境需手动创建
    from .password_utils import hash_password
    import secrets
    import logging
    init_logger = logging.getLogger(__name__)

    session = AuthSessionLocal()
    try:
        # 使用原始 SQL 查询避免 ORM 映射问题
        from sqlalchemy import text
        result = session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()

        if user_count == 0:
            is_dev = os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG", "").lower() == "true"

            if is_dev:
                # 开发环境：使用固定密码便于测试
                admin_password = "admin123"
                # P3-49: 安全修复 - 不在日志中打印密码明文
                init_logger.warning("[开发环境] 创建默认管理员: admin (密码见代码)")
            else:
                # 生产环境：生成随机密码，要求首次登录后修改
                admin_password = secrets.token_urlsafe(16)
                init_logger.critical("[生产环境] 创建初始管理员账户")
                init_logger.critical("用户名: admin")
                # P3-49: 安全修复 - 将密码写入临时文件而非日志
                try:
                    import tempfile
                    cred_file = os.path.join(tempfile.gettempdir(), 'jzc_admin_credentials.txt')
                    with open(cred_file, 'w') as f:
                        f.write(f"JZC Systems 初始管理员凭据\n")
                        f.write(f"用户名: admin\n")
                        f.write(f"临时密码: {admin_password}\n")
                        f.write(f"请登录后立即修改密码并删除此文件!\n")
                    # 设置文件权限（仅所有者可读写）
                    os.chmod(cred_file, 0o600)
                    init_logger.critical(f"临时密码已写入: {cred_file}")
                    init_logger.critical("请查看文件获取密码，使用后删除该文件！")
                except Exception as e:
                    # 如果文件写入失败，回退到日志（但添加警告）
                    init_logger.critical(f"无法写入凭据文件: {e}")
                    init_logger.critical(f"临时密码: {admin_password} (请立即记录并修改)")
                init_logger.critical("请立即登录并修改密码！")

            admin_user = User(
                username='admin',
                email='admin@jzchardware.cn',
                hashed_password=hash_password(admin_password),
                full_name='系统管理员',
                role='super_admin',
                permissions=json.dumps(['hr', 'quotation', '采购', 'account', 'shm', 'crm', 'scm', 'eam', 'mes']),
                is_active=True,
                is_admin=True
            )
            session.add(admin_user)
            session.commit()
    except Exception as e:
        init_logger.error(f"Auth DB init warning: {e}")
        session.rollback()
    finally:
        session.close()

    return auth_engine


def get_auth_db():
    """Get database session"""
    if AuthSessionLocal is None:
        init_auth_db()
    session = AuthSessionLocal()
    try:
        yield session
    finally:
        session.close()

class RegistrationRequest(Base):
    """Registration request model for user account creation approval"""
    __tablename__ = 'registration_requests'

    id = Column(Integer, primary_key=True, index=True)
    emp_no = Column(String(50), nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    username = Column(String(50), nullable=False, index=True)  # 用户设置的用户名
    email = Column(String(100), nullable=False, index=True)  # 用户设置的邮箱
    hashed_password = Column(String(255), nullable=False)  # 用户设置的密码(哈希后)
    department = Column(String(100))
    title = Column(String(100))
    factory_name = Column(String(100))
    status = Column(String(20), default='pending')  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_by = Column(Integer)  # User ID of admin who reviewed
    reviewed_at = Column(DateTime)
    rejection_reason = Column(String(500))
    processed_at = Column(DateTime)  # When request was approved/rejected

    def to_dict(self):
        """Convert request to dictionary"""
        return {
            'id': self.id,
            'emp_no': self.emp_no,
            'full_name': self.full_name,
            'email': self.email,
            'department': self.department,
            'title': self.title,
            'factory_name': self.factory_name,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'rejection_reason': self.rejection_reason
        }


class AuditLog(Base):
    """Audit log for tracking user operations"""
    __tablename__ = 'audit_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, index=True)  # 操作用户 ID
    username = Column(String(50), nullable=True)  # 操作用户名（冗余存储）

    # Action details
    action_type = Column(String(50), nullable=False, index=True)  # login, logout, login_failed, password_change, data_access, data_modify, etc.
    resource_type = Column(String(50), nullable=True)  # 资源类型: user, employee, customer, order, etc.
    resource_id = Column(String(50), nullable=True)  # 资源 ID
    description = Column(Text, nullable=True)  # 操作描述

    # Request details
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 地址
    user_agent = Column(Text, nullable=True)  # 浏览器/设备信息
    request_method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    request_path = Column(String(500), nullable=True)  # API 路径
    request_body = Column(Text, nullable=True)  # 请求体 (脱敏后)

    # Result
    status = Column(String(20), nullable=False, default='success')  # success, failed, error
    error_message = Column(Text, nullable=True)  # 错误信息
    response_code = Column(Integer, nullable=True)  # HTTP 响应码

    # Metadata
    module = Column(String(50), nullable=True)  # 所属模块: portal, hr, crm, etc.
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action_type'),
        Index('idx_audit_created_at', 'created_at'),
        Index('idx_audit_module_action', 'module', 'action_type'),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action_type': self.action_type,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'description': self.description,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'request_method': self.request_method,
            'request_path': self.request_path,
            'status': self.status,
            'error_message': self.error_message,
            'response_code': self.response_code,
            'module': self.module,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class LoginHistory(Base):
    """Login history for tracking user login sessions"""
    __tablename__ = 'login_history'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(50), nullable=True)

    # Login details
    login_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    logout_time = Column(DateTime, nullable=True)
    session_duration_minutes = Column(Integer, nullable=True)  # 会话时长(分钟)

    # Device information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    location = Column(String(200), nullable=True)  # 地理位置（可选）

    # Status
    is_success = Column(Boolean, default=True)  # 登录是否成功
    failure_reason = Column(String(255), nullable=True)  # 失败原因
    login_type = Column(String(20), default='password')  # password, sso, 2fa, etc.

    # Session tracking
    session_token = Column(String(255), nullable=True)  # Token 标识（哈希后）
    is_current = Column(Boolean, default=False)  # 是否当前活跃会话

    __table_args__ = (
        Index('idx_login_user_time', 'user_id', 'login_time'),
        Index('idx_login_ip', 'ip_address'),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'login_time': self.login_time.isoformat() if self.login_time else None,
            'logout_time': self.logout_time.isoformat() if self.logout_time else None,
            'session_duration_minutes': self.session_duration_minutes,
            'ip_address': self.ip_address,
            'device_type': self.device_type,
            'browser': self.browser,
            'os': self.os,
            'location': self.location,
            'is_success': self.is_success,
            'failure_reason': self.failure_reason,
            'login_type': self.login_type,
            'is_current': self.is_current
        }


class PasswordHistory(Base):
    """Password history for preventing password reuse"""
    __tablename__ = 'password_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_pwd_history_user', 'user_id', 'created_at'),
    )


class TwoFactorAuth(Base):
    """Two-factor authentication settings for users"""
    __tablename__ = 'two_factor_auth'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)

    # TOTP settings
    secret_key = Column(String(64), nullable=False)  # Base32 encoded secret
    is_enabled = Column(Boolean, default=False)  # 是否已启用 2FA
    is_verified = Column(Boolean, default=False)  # 是否已验证（首次设置时验证）

    # Recovery options
    recovery_email = Column(String(100), nullable=True)  # 备用邮箱
    recovery_phone = Column(String(50), nullable=True)  # 备用手机

    # Metadata
    enabled_at = Column(DateTime, nullable=True)  # 启用时间
    last_used_at = Column(DateTime, nullable=True)  # 上次使用时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_secret=False):
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'is_enabled': self.is_enabled,
            'is_verified': self.is_verified,
            'recovery_email': self.recovery_email,
            'recovery_phone': self.recovery_phone,
            'enabled_at': self.enabled_at.isoformat() if self.enabled_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_secret:
            result['secret_key'] = self.secret_key
        return result


class TwoFactorBackupCode(Base):
    """Backup codes for two-factor authentication"""
    __tablename__ = 'two_factor_backup_codes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    code_hash = Column(String(255), nullable=False)  # 哈希后的备用码
    is_used = Column(Boolean, default=False)  # 是否已使用
    used_at = Column(DateTime, nullable=True)  # 使用时间
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_backup_code_user', 'user_id'),
    )

    def to_dict(self):
        """Convert to dictionary (never expose code_hash)"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'is_used': self.is_used,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
