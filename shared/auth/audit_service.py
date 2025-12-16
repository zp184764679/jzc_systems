"""
Audit Service - Centralized audit logging for all subsystems
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, g
import json
import hashlib
import re

from .models import AuditLog, LoginHistory, AuthSessionLocal

logger = logging.getLogger(__name__)


# Sensitive fields to redact in request body
SENSITIVE_FIELDS = {
    'password', 'hashed_password', 'token', 'secret', 'api_key',
    'credit_card', 'card_number', 'cvv', 'ssn', 'id_card'
}


def sanitize_request_body(body: Dict) -> str:
    """Remove sensitive data from request body before logging"""
    if not body:
        return None

    def redact_sensitive(obj, path=''):
        if isinstance(obj, dict):
            return {
                k: '***REDACTED***' if k.lower() in SENSITIVE_FIELDS
                else redact_sensitive(v, f'{path}.{k}')
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [redact_sensitive(item, f'{path}[]') for item in obj]
        return obj

    try:
        sanitized = redact_sensitive(body)
        return json.dumps(sanitized, ensure_ascii=False, default=str)[:2000]  # Limit size
    except Exception:
        return None


def parse_user_agent(ua_string: str) -> Dict[str, str]:
    """Parse user agent string to extract device info"""
    if not ua_string:
        return {'device_type': 'unknown', 'browser': 'unknown', 'os': 'unknown'}

    # Simple parsing - can be enhanced with user-agents library
    ua_lower = ua_string.lower()

    # Device type
    if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
        device_type = 'mobile'
    elif 'tablet' in ua_lower or 'ipad' in ua_lower:
        device_type = 'tablet'
    else:
        device_type = 'desktop'

    # Browser
    if 'chrome' in ua_lower and 'edg' not in ua_lower:
        browser = 'Chrome'
    elif 'firefox' in ua_lower:
        browser = 'Firefox'
    elif 'safari' in ua_lower and 'chrome' not in ua_lower:
        browser = 'Safari'
    elif 'edg' in ua_lower:
        browser = 'Edge'
    elif 'msie' in ua_lower or 'trident' in ua_lower:
        browser = 'IE'
    else:
        browser = 'Other'

    # OS
    if 'windows' in ua_lower:
        os_name = 'Windows'
    elif 'mac os' in ua_lower or 'macos' in ua_lower:
        os_name = 'macOS'
    elif 'linux' in ua_lower and 'android' not in ua_lower:
        os_name = 'Linux'
    elif 'android' in ua_lower:
        os_name = 'Android'
    elif 'iphone' in ua_lower or 'ipad' in ua_lower:
        os_name = 'iOS'
    else:
        os_name = 'Other'

    return {
        'device_type': device_type,
        'browser': browser,
        'os': os_name
    }


def get_client_ip() -> str:
    """Get client IP address from request"""
    if not request:
        return None

    # Check for proxy headers
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr


def hash_token(token: str) -> str:
    """Hash token for storage (don't store raw tokens)"""
    if not token:
        return None
    return hashlib.sha256(token.encode()).hexdigest()[:32]


class AuditService:
    """Service for recording audit logs and login history"""

    # Action type constants
    ACTION_LOGIN = 'login'
    ACTION_LOGIN_FAILED = 'login_failed'
    ACTION_LOGOUT = 'logout'
    ACTION_PASSWORD_CHANGE = 'password_change'
    ACTION_PASSWORD_RESET = 'password_reset'
    ACTION_USER_CREATE = 'user_create'
    ACTION_USER_UPDATE = 'user_update'
    ACTION_USER_DELETE = 'user_delete'
    ACTION_DATA_ACCESS = 'data_access'
    ACTION_DATA_CREATE = 'data_create'
    ACTION_DATA_UPDATE = 'data_update'
    ACTION_DATA_DELETE = 'data_delete'
    ACTION_PERMISSION_CHANGE = 'permission_change'
    ACTION_EXPORT = 'export'
    ACTION_IMPORT = 'import'

    @staticmethod
    def log(
        action_type: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        status: str = 'success',
        error_message: Optional[str] = None,
        module: Optional[str] = None,
        request_body: Optional[Dict] = None
    ) -> Optional[AuditLog]:
        """
        Log an audit event

        Args:
            action_type: Type of action (login, data_access, etc.)
            user_id: ID of the user performing the action
            username: Username (for display purposes)
            resource_type: Type of resource being accessed
            resource_id: ID of the resource
            description: Human-readable description
            status: success, failed, or error
            error_message: Error message if failed
            module: Which subsystem (portal, hr, crm, etc.)
            request_body: Request body dict (will be sanitized)
        """
        session = AuthSessionLocal()
        try:
            audit = AuditLog(
                user_id=user_id,
                username=username,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                description=description,
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent') if request else None,
                request_method=request.method if request else None,
                request_path=request.path if request else None,
                request_body=sanitize_request_body(request_body),
                status=status,
                error_message=error_message,
                module=module,
                created_at=datetime.utcnow()
            )
            session.add(audit)
            session.commit()
            return audit
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    @staticmethod
    def log_login(
        user_id: int,
        username: str,
        success: bool,
        login_type: str = 'password',
        failure_reason: Optional[str] = None,
        token: Optional[str] = None,
        module: str = 'portal'
    ) -> Optional[LoginHistory]:
        """
        Log a login attempt

        Args:
            user_id: User ID
            username: Username
            success: Whether login was successful
            login_type: password, sso, 2fa, etc.
            failure_reason: Reason for failure if not successful
            token: JWT token (will be hashed)
            module: Which subsystem
        """
        session = AuthSessionLocal()
        try:
            ua_info = parse_user_agent(
                request.headers.get('User-Agent') if request else None
            )

            login_record = LoginHistory(
                user_id=user_id,
                username=username,
                login_time=datetime.utcnow(),
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent') if request else None,
                device_type=ua_info['device_type'],
                browser=ua_info['browser'],
                os=ua_info['os'],
                is_success=success,
                failure_reason=failure_reason,
                login_type=login_type,
                session_token=hash_token(token),
                is_current=success
            )
            session.add(login_record)

            # Also log to audit log
            AuditService.log(
                action_type=AuditService.ACTION_LOGIN if success else AuditService.ACTION_LOGIN_FAILED,
                user_id=user_id,
                username=username,
                description=f"用户 {username} {'登录成功' if success else '登录失败: ' + (failure_reason or '未知原因')}",
                status='success' if success else 'failed',
                error_message=failure_reason,
                module=module
            )

            session.commit()
            return login_record
        except Exception as e:
            logger.error(f"Failed to write login history: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    @staticmethod
    def log_logout(user_id: int, username: str, module: str = 'portal'):
        """Log a logout event"""
        session = AuthSessionLocal()
        try:
            # Update current session to mark as logged out
            session.query(LoginHistory).filter(
                LoginHistory.user_id == user_id,
                LoginHistory.is_current == True
            ).update({
                'is_current': False,
                'logout_time': datetime.utcnow()
            })

            AuditService.log(
                action_type=AuditService.ACTION_LOGOUT,
                user_id=user_id,
                username=username,
                description=f"用户 {username} 退出登录",
                module=module
            )

            session.commit()
        except Exception as e:
            logger.error(f"Failed to log logout: {e}")
            session.rollback()
        finally:
            session.close()

    @staticmethod
    def get_user_login_history(
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get login history for a user"""
        session = AuthSessionLocal()
        try:
            query = session.query(LoginHistory).filter(
                LoginHistory.user_id == user_id
            )

            if start_date:
                query = query.filter(LoginHistory.login_time >= start_date)
            if end_date:
                query = query.filter(LoginHistory.login_time <= end_date)

            total = query.count()
            records = query.order_by(LoginHistory.login_time.desc())\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()

            return {
                'total': total,
                'page': page,
                'per_page': per_page,
                'data': [r.to_dict() for r in records]
            }
        finally:
            session.close()

    @staticmethod
    def get_audit_logs(
        page: int = 1,
        per_page: int = 50,
        user_id: Optional[int] = None,
        action_type: Optional[str] = None,
        module: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get audit logs with filters"""
        session = AuthSessionLocal()
        try:
            query = session.query(AuditLog)

            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if action_type:
                query = query.filter(AuditLog.action_type == action_type)
            if module:
                query = query.filter(AuditLog.module == module)
            if status:
                query = query.filter(AuditLog.status == status)
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            if search:
                search_pattern = f'%{search}%'
                query = query.filter(
                    (AuditLog.username.like(search_pattern)) |
                    (AuditLog.description.like(search_pattern)) |
                    (AuditLog.ip_address.like(search_pattern))
                )

            total = query.count()
            logs = query.order_by(AuditLog.created_at.desc())\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()

            return {
                'total': total,
                'page': page,
                'per_page': per_page,
                'data': [log.to_dict() for log in logs]
            }
        finally:
            session.close()

    @staticmethod
    def get_security_events(
        page: int = 1,
        per_page: int = 50,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get security-related events (failed logins, password changes, etc.)"""
        from datetime import timedelta
        session = AuthSessionLocal()
        try:
            security_actions = [
                AuditService.ACTION_LOGIN_FAILED,
                AuditService.ACTION_PASSWORD_CHANGE,
                AuditService.ACTION_PASSWORD_RESET,
                AuditService.ACTION_PERMISSION_CHANGE,
                AuditService.ACTION_USER_CREATE,
                AuditService.ACTION_USER_DELETE
            ]

            start_date = datetime.utcnow() - timedelta(days=days)

            query = session.query(AuditLog).filter(
                AuditLog.action_type.in_(security_actions),
                AuditLog.created_at >= start_date
            )

            total = query.count()
            events = query.order_by(AuditLog.created_at.desc())\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()

            return {
                'total': total,
                'page': page,
                'per_page': per_page,
                'data': [e.to_dict() for e in events]
            }
        finally:
            session.close()


def audit_action(action_type: str, resource_type: str = None, module: str = None):
    """
    Decorator for auditing API actions

    Usage:
        @audit_action('data_update', 'employee', 'hr')
        def update_employee(id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Get user info from Flask g or request
            user_id = getattr(g, 'user_id', None) or getattr(g, 'current_user', {}).get('id')
            username = getattr(g, 'username', None) or getattr(g, 'current_user', {}).get('username')

            resource_id = kwargs.get('id') or kwargs.get('user_id') or kwargs.get('employee_id')

            try:
                result = f(*args, **kwargs)

                # Log successful action
                AuditService.log(
                    action_type=action_type,
                    user_id=user_id,
                    username=username,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    description=f"{action_type} on {resource_type or 'resource'} {resource_id or ''}",
                    status='success',
                    module=module,
                    request_body=request.get_json(silent=True)
                )

                return result
            except Exception as e:
                # Log failed action
                AuditService.log(
                    action_type=action_type,
                    user_id=user_id,
                    username=username,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    description=f"Failed {action_type} on {resource_type or 'resource'}",
                    status='failed',
                    error_message=str(e),
                    module=module,
                    request_body=request.get_json(silent=True)
                )
                raise

        return wrapper
    return decorator
