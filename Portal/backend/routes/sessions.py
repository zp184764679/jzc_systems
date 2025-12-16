# -*- coding: utf-8 -*-
"""
Session Management API - 会话管理
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from functools import wraps
import hashlib
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token, User, AuditService
import shared.auth.models as auth_models
from shared.auth.models import LoginHistory

sessions_bp = Blueprint('sessions', __name__, url_prefix='/api/sessions')


def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
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

        request.current_user = payload
        request.current_token = token
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = request.current_user
        role = user.get('role', 'user')
        if role not in ['admin', 'super_admin']:
            return jsonify({'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated_function


def get_token_hash(token):
    """获取 token 的哈希值用于标识会话"""
    return hashlib.sha256(token.encode()).hexdigest()[:32]


@sessions_bp.route('', methods=['GET'])
@require_auth
def get_my_sessions():
    """获取当前用户的活跃会话列表"""
    user = request.current_user
    user_id = user.get('user_id') or user.get('id')
    current_token_hash = get_token_hash(request.current_token)

    session = auth_models.AuthSessionLocal()
    try:
        # 获取该用户的登录历史（成功的登录且标记为当前会话）
        histories = session.query(LoginHistory).filter(
            LoginHistory.user_id == user_id,
            LoginHistory.is_success == True,
            LoginHistory.is_current == True
        ).order_by(LoginHistory.login_time.desc()).all()

        sessions_list = []
        for h in histories:
            is_current = h.session_token == current_token_hash if h.session_token else False
            sessions_list.append({
                'id': h.id,
                'device_type': h.device_type or 'unknown',
                'browser': h.browser or 'unknown',
                'os': h.os or 'unknown',
                'ip_address': h.ip_address,
                'location': h.location,
                'login_time': h.login_time.isoformat() if h.login_time else None,
                'is_current': is_current
            })

        return jsonify({
            'sessions': sessions_list,
            'total': len(sessions_list)
        })
    finally:
        session.close()


@sessions_bp.route('/all', methods=['GET'])
@require_auth
@require_admin
def get_all_sessions():
    """管理员获取所有用户的活跃会话"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    username = request.args.get('username', '')
    user_id_filter = request.args.get('user_id', type=int)

    session = auth_models.AuthSessionLocal()
    try:
        query = session.query(LoginHistory).filter(
            LoginHistory.is_success == True,
            LoginHistory.is_current == True
        )

        if username:
            query = query.filter(LoginHistory.username.ilike(f'%{username}%'))
        if user_id_filter:
            query = query.filter(LoginHistory.user_id == user_id_filter)

        total = query.count()
        histories = query.order_by(LoginHistory.login_time.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        sessions_list = []
        for h in histories:
            sessions_list.append({
                'id': h.id,
                'user_id': h.user_id,
                'username': h.username,
                'device_type': h.device_type or 'unknown',
                'browser': h.browser or 'unknown',
                'os': h.os or 'unknown',
                'ip_address': h.ip_address,
                'location': h.location,
                'login_time': h.login_time.isoformat() if h.login_time else None,
                'login_type': h.login_type
            })

        return jsonify({
            'sessions': sessions_list,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size if page_size else 1
        })
    finally:
        session.close()


@sessions_bp.route('/<int:session_id>', methods=['DELETE'])
@require_auth
def revoke_session(session_id):
    """注销特定会话"""
    user = request.current_user
    user_id = user.get('user_id') or user.get('id')
    role = user.get('role', 'user')
    current_token_hash = get_token_hash(request.current_token)

    session = auth_models.AuthSessionLocal()
    try:
        login_history = session.query(LoginHistory).filter_by(id=session_id).first()

        if not login_history:
            return jsonify({'error': '会话不存在'}), 404

        # 检查权限：只能注销自己的会话，或管理员可以注销任何会话
        if login_history.user_id != user_id and role not in ['admin', 'super_admin']:
            return jsonify({'error': '无权操作此会话'}), 403

        # 不能注销当前会话
        if login_history.session_token == current_token_hash:
            return jsonify({'error': '不能注销当前会话，请使用退出登录'}), 400

        # 标记会话为已注销
        login_history.is_current = False
        login_history.logout_time = datetime.utcnow()
        if login_history.login_time:
            duration = (login_history.logout_time - login_history.login_time).total_seconds() / 60
            login_history.session_duration_minutes = int(duration)

        session.commit()

        # 记录审计日志
        AuditService.log_action(
            user_id=user_id,
            username=user.get('username'),
            action_type='session_revoke',
            resource_type='session',
            resource_id=str(session_id),
            description=f'注销会话 (用户: {login_history.username})',
            module='portal'
        )

        return jsonify({'message': '会话已注销'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@sessions_bp.route('/other', methods=['DELETE'])
@require_auth
def revoke_other_sessions():
    """注销当前用户的其他所有会话"""
    user = request.current_user
    user_id = user.get('user_id') or user.get('id')
    current_token_hash = get_token_hash(request.current_token)

    session = auth_models.AuthSessionLocal()
    try:
        # 获取该用户的所有活跃会话（除了当前会话）
        other_sessions = session.query(LoginHistory).filter(
            LoginHistory.user_id == user_id,
            LoginHistory.is_current == True,
            LoginHistory.session_token != current_token_hash
        ).all()

        revoked_count = 0
        now = datetime.utcnow()
        for h in other_sessions:
            h.is_current = False
            h.logout_time = now
            if h.login_time:
                duration = (now - h.login_time).total_seconds() / 60
                h.session_duration_minutes = int(duration)
            revoked_count += 1

        session.commit()

        # 记录审计日志
        AuditService.log_action(
            user_id=user_id,
            username=user.get('username'),
            action_type='session_revoke_other',
            description=f'注销其他 {revoked_count} 个会话',
            module='portal'
        )

        return jsonify({
            'message': f'已注销 {revoked_count} 个其他会话',
            'revoked_count': revoked_count
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@sessions_bp.route('/revoke-all/<int:target_user_id>', methods=['POST'])
@require_auth
@require_admin
def revoke_all_user_sessions(target_user_id):
    """管理员强制下线某用户的所有会话"""
    user = request.current_user
    admin_id = user.get('user_id') or user.get('id')

    session = auth_models.AuthSessionLocal()
    try:
        # 获取目标用户信息
        target_user = session.query(User).filter_by(id=target_user_id).first()
        if not target_user:
            return jsonify({'error': '用户不存在'}), 404

        # 不能强制下线自己
        if target_user_id == admin_id:
            return jsonify({'error': '不能强制下线自己'}), 400

        # 获取该用户的所有活跃会话
        active_sessions = session.query(LoginHistory).filter(
            LoginHistory.user_id == target_user_id,
            LoginHistory.is_current == True
        ).all()

        revoked_count = 0
        now = datetime.utcnow()
        for h in active_sessions:
            h.is_current = False
            h.logout_time = now
            if h.login_time:
                duration = (now - h.login_time).total_seconds() / 60
                h.session_duration_minutes = int(duration)
            revoked_count += 1

        session.commit()

        # 记录审计日志
        AuditService.log_action(
            user_id=admin_id,
            username=user.get('username'),
            action_type='session_revoke_all',
            resource_type='user',
            resource_id=str(target_user_id),
            description=f'强制下线用户 {target_user.username} 的 {revoked_count} 个会话',
            module='portal'
        )

        return jsonify({
            'message': f'已强制下线用户 {target_user.username} 的 {revoked_count} 个会话',
            'revoked_count': revoked_count
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@sessions_bp.route('/statistics', methods=['GET'])
@require_auth
@require_admin
def get_session_statistics():
    """获取会话统计信息"""
    session = auth_models.AuthSessionLocal()
    try:
        from sqlalchemy import func, distinct

        # 当前活跃会话数
        active_sessions = session.query(func.count(LoginHistory.id)).filter(
            LoginHistory.is_current == True
        ).scalar() or 0

        # 活跃用户数
        active_users = session.query(func.count(distinct(LoginHistory.user_id))).filter(
            LoginHistory.is_current == True
        ).scalar() or 0

        # 今日登录次数
        from datetime import date
        today = date.today()
        today_logins = session.query(func.count(LoginHistory.id)).filter(
            LoginHistory.is_success == True,
            func.date(LoginHistory.login_time) == today
        ).scalar() or 0

        # 按设备类型统计
        device_stats = session.query(
            LoginHistory.device_type,
            func.count(LoginHistory.id).label('count')
        ).filter(
            LoginHistory.is_current == True
        ).group_by(LoginHistory.device_type).all()

        device_distribution = {}
        for device_type, count in device_stats:
            device_distribution[device_type or 'unknown'] = count

        return jsonify({
            'active_sessions': active_sessions,
            'active_users': active_users,
            'today_logins': today_logins,
            'device_distribution': device_distribution
        })
    finally:
        session.close()
