# -*- coding: utf-8 -*-
"""
通知路由
Notification Routes
"""
from flask import Blueprint, jsonify, request
from services.notification_service import NotificationService
import sys
import os

# Add shared module to path for JWT verification
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', '..'))
from shared.auth import verify_token

URL_PREFIX = '/api/v1/notifications'
bp = Blueprint('notification', __name__)


@bp.before_request
def check_auth():
    """JWT认证检查"""
    if request.method == 'OPTIONS':
        return None

    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        if payload:
            request.current_user_id = payload.get('user_id')
            request.current_user_role = payload.get('role')
            request.current_supplier_id = payload.get('supplier_id')
            return None

    # 回退检查 User-ID 或 Supplier-ID header
    user_id = request.headers.get('User-ID')
    supplier_id = request.headers.get('Supplier-ID')
    if user_id or supplier_id:
        request.current_user_id = user_id
        request.current_supplier_id = supplier_id
        request.current_user_role = request.headers.get('User-Role')
        return None

    return jsonify({"error": "未授权：请先登录"}), 401


@bp.route('/unread', methods=['GET', 'OPTIONS'])
def get_unread_notifications():
    """
    获取未读通知

    GET /api/v1/notifications/unread

    Headers:
        Supplier-ID: 供应商ID (供应商端)
        User-ID: 用户ID (员工端)

    Query Parameters:
        type: recipient_type (supplier/user, default: supplier)
        limit: 数量限制 (default: 20)

    Returns:
        {
            "items": [通知列表],
            "unread_count": 未读数量
        }
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        recipient_type = request.args.get('type', 'supplier')
        limit = request.args.get('limit', 20, type=int)

        # 获取接收者ID
        if recipient_type == 'supplier':
            recipient_id = request.headers.get('Supplier-ID')
        else:
            recipient_id = request.headers.get('User-ID')

        if not recipient_id:
            return jsonify({'error': '缺少接收者ID'}), 400

        recipient_id = int(recipient_id)

        # 获取未读通知
        notifications = NotificationService.get_unread_notifications(
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            limit=limit
        )

        return jsonify({
            'items': notifications,
            'unread_count': len(notifications)
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/all', methods=['GET', 'OPTIONS'])
def get_all_notifications():
    """
    获取所有通知（分页）

    GET /api/v1/notifications/all?page=1&per_page=20

    Headers:
        Supplier-ID: 供应商ID (供应商端)
        User-ID: 用户ID (员工端)

    Query Parameters:
        type: recipient_type (supplier/user, default: supplier)
        page: 页码 (default: 1)
        per_page: 每页数量 (default: 20)

    Returns:
        {
            "items": [通知列表],
            "total": 总数,
            "page": 当前页,
            "per_page": 每页数量,
            "pages": 总页数
        }
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        recipient_type = request.args.get('type', 'supplier')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # 获取接收者ID
        if recipient_type == 'supplier':
            recipient_id = request.headers.get('Supplier-ID')
        else:
            recipient_id = request.headers.get('User-ID')

        if not recipient_id:
            return jsonify({'error': '缺少接收者ID'}), 400

        recipient_id = int(recipient_id)

        # 获取所有通知
        result = NotificationService.get_all_notifications(
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            page=page,
            per_page=per_page
        )

        return jsonify(result), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:notification_id>/read', methods=['POST', 'OPTIONS'])
def mark_notification_as_read(notification_id):
    """
    标记通知为已读

    POST /api/v1/notifications/<notification_id>/read

    Headers:
        Supplier-ID: 供应商ID (供应商端)
        User-ID: 用户ID (员工端)

    Query Parameters:
        type: recipient_type (supplier/user, default: supplier)

    Returns:
        {
            "success": true,
            "message": "通知已标记为已读"
        }
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        recipient_type = request.args.get('type', 'supplier')

        # 获取接收者ID
        if recipient_type == 'supplier':
            recipient_id = request.headers.get('Supplier-ID')
        else:
            recipient_id = request.headers.get('User-ID')

        if not recipient_id:
            return jsonify({'error': '缺少接收者ID'}), 400

        recipient_id = int(recipient_id)

        # 标记为已读
        success = NotificationService.mark_as_read(notification_id, recipient_id)

        if not success:
            return jsonify({'error': '通知不存在或无权访问'}), 404

        return jsonify({
            'success': True,
            'message': '通知已标记为已读'
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/mark-all-read', methods=['POST', 'OPTIONS'])
def mark_all_notifications_as_read():
    """
    标记所有通知为已读

    POST /api/v1/notifications/mark-all-read

    Headers:
        Supplier-ID: 供应商ID (供应商端)
        User-ID: 用户ID (员工端)

    Query Parameters:
        type: recipient_type (supplier/user, default: supplier)

    Returns:
        {
            "success": true,
            "count": 标记的数量,
            "message": "已标记 X 条通知为已读"
        }
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        recipient_type = request.args.get('type', 'supplier')

        # 获取接收者ID
        if recipient_type == 'supplier':
            recipient_id = request.headers.get('Supplier-ID')
        else:
            recipient_id = request.headers.get('User-ID')

        if not recipient_id:
            return jsonify({'error': '缺少接收者ID'}), 400

        recipient_id = int(recipient_id)

        # 批量标记为已读
        count = NotificationService.mark_all_as_read(recipient_id, recipient_type)

        return jsonify({
            'success': True,
            'count': count,
            'message': f'已标记 {count} 条通知为已读'
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
