"""
Audit API Routes - Audit logs and login history management
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.auth import (
    AuditService, AuditLog, LoginHistory,
    verify_token, is_admin, is_super_admin
)
import shared.auth.models as auth_models

audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit')


def require_admin(f):
    """Decorator to require admin access"""
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

        return f(*args, **kwargs)
    return decorated


def get_current_user():
    """Get current user from request"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ')[1]
    return verify_token(token)


@audit_bp.route('/logs', methods=['GET'])
@require_admin
def get_audit_logs():
    """
    Get audit logs with filters

    Query params:
    - page: Page number (default 1)
    - per_page: Items per page (default 50, max 100)
    - user_id: Filter by user ID
    - action_type: Filter by action type
    - module: Filter by module
    - status: Filter by status (success/failed)
    - start_date: Filter from date (YYYY-MM-DD)
    - end_date: Filter to date (YYYY-MM-DD)
    - search: Search in username, description, IP
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        user_id = request.args.get('user_id', type=int)
        action_type = request.args.get('action_type')
        module = request.args.get('module')
        status = request.args.get('status')
        search = request.args.get('search')

        start_date = None
        end_date = None
        if request.args.get('start_date'):
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
        if request.args.get('end_date'):
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
            end_date = end_date + timedelta(days=1)  # Include the end date

        result = AuditService.get_audit_logs(
            page=page,
            per_page=per_page,
            user_id=user_id,
            action_type=action_type,
            module=module,
            status=status,
            start_date=start_date,
            end_date=end_date,
            search=search
        )

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audit_bp.route('/login-history', methods=['GET'])
@require_admin
def get_all_login_history():
    """
    Get login history for all users (admin only)

    Query params:
    - page: Page number (default 1)
    - per_page: Items per page (default 50, max 100)
    - user_id: Filter by user ID
    - success: Filter by success (true/false)
    - start_date: Filter from date (YYYY-MM-DD)
    - end_date: Filter to date (YYYY-MM-DD)
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        user_id = request.args.get('user_id', type=int)
        success = request.args.get('success')

        start_date = None
        end_date = None
        if request.args.get('start_date'):
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
        if request.args.get('end_date'):
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
            end_date = end_date + timedelta(days=1)

        session = auth_models.AuthSessionLocal()
        try:
            query = session.query(LoginHistory)

            if user_id:
                query = query.filter(LoginHistory.user_id == user_id)
            if success is not None:
                is_success = success.lower() == 'true'
                query = query.filter(LoginHistory.is_success == is_success)
            if start_date:
                query = query.filter(LoginHistory.login_time >= start_date)
            if end_date:
                query = query.filter(LoginHistory.login_time <= end_date)

            total = query.count()
            records = query.order_by(LoginHistory.login_time.desc())\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()

            return jsonify({
                'total': total,
                'page': page,
                'per_page': per_page,
                'data': [r.to_dict() for r in records]
            }), 200
        finally:
            session.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audit_bp.route('/my-login-history', methods=['GET'])
def get_my_login_history():
    """
    Get login history for current user

    Query params:
    - page: Page number (default 1)
    - per_page: Items per page (default 20, max 50)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '请先登录'}), 401

    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 50)
        user_id = user.get('user_id') or user.get('id')

        result = AuditService.get_user_login_history(
            user_id=user_id,
            page=page,
            per_page=per_page
        )

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audit_bp.route('/security-events', methods=['GET'])
@require_admin
def get_security_events():
    """
    Get security-related events

    Query params:
    - page: Page number (default 1)
    - per_page: Items per page (default 50, max 100)
    - days: Number of days to look back (default 7)
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        days = int(request.args.get('days', 7))

        result = AuditService.get_security_events(
            page=page,
            per_page=per_page,
            days=days
        )

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audit_bp.route('/stats', methods=['GET'])
@require_admin
def get_audit_stats():
    """
    Get audit statistics

    Query params:
    - days: Number of days to look back (default 7)
    """
    try:
        days = int(request.args.get('days', 7))
        start_date = datetime.utcnow() - timedelta(days=days)

        session = auth_models.AuthSessionLocal()
        try:
            # Login stats
            total_logins = session.query(LoginHistory).filter(
                LoginHistory.login_time >= start_date
            ).count()

            successful_logins = session.query(LoginHistory).filter(
                LoginHistory.login_time >= start_date,
                LoginHistory.is_success == True
            ).count()

            failed_logins = session.query(LoginHistory).filter(
                LoginHistory.login_time >= start_date,
                LoginHistory.is_success == False
            ).count()

            # Action stats by type
            from sqlalchemy import func
            action_stats = session.query(
                AuditLog.action_type,
                func.count(AuditLog.id).label('count')
            ).filter(
                AuditLog.created_at >= start_date
            ).group_by(AuditLog.action_type).all()

            # Module stats
            module_stats = session.query(
                AuditLog.module,
                func.count(AuditLog.id).label('count')
            ).filter(
                AuditLog.created_at >= start_date,
                AuditLog.module != None
            ).group_by(AuditLog.module).all()

            # Active users (unique users with activity)
            active_users = session.query(
                func.count(func.distinct(AuditLog.user_id))
            ).filter(
                AuditLog.created_at >= start_date,
                AuditLog.user_id != None
            ).scalar()

            return jsonify({
                'period_days': days,
                'login_stats': {
                    'total': total_logins,
                    'successful': successful_logins,
                    'failed': failed_logins,
                    'success_rate': round(successful_logins / total_logins * 100, 2) if total_logins > 0 else 0
                },
                'action_stats': {
                    item.action_type: item.count for item in action_stats
                },
                'module_stats': {
                    item.module: item.count for item in module_stats
                },
                'active_users': active_users
            }), 200
        finally:
            session.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audit_bp.route('/action-types', methods=['GET'])
def get_action_types():
    """Get list of available action types"""
    return jsonify({
        'action_types': [
            {'code': 'login', 'name': '登录'},
            {'code': 'login_failed', 'name': '登录失败'},
            {'code': 'logout', 'name': '退出登录'},
            {'code': 'password_change', 'name': '修改密码'},
            {'code': 'password_reset', 'name': '重置密码'},
            {'code': 'user_create', 'name': '创建用户'},
            {'code': 'user_update', 'name': '更新用户'},
            {'code': 'user_delete', 'name': '删除用户'},
            {'code': 'permission_change', 'name': '权限变更'},
            {'code': 'data_access', 'name': '数据访问'},
            {'code': 'data_create', 'name': '创建数据'},
            {'code': 'data_update', 'name': '更新数据'},
            {'code': 'data_delete', 'name': '删除数据'},
            {'code': 'export', 'name': '导出数据'},
            {'code': 'import', 'name': '导入数据'}
        ]
    }), 200


@audit_bp.route('/modules', methods=['GET'])
def get_modules():
    """Get list of available modules"""
    return jsonify({
        'modules': [
            {'code': 'portal', 'name': '门户系统'},
            {'code': 'hr', 'name': '人力资源'},
            {'code': 'account', 'name': '账户管理'},
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
