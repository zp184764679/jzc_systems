"""
Notifications API Routes - 通知管理API
"""
from flask import Blueprint, request, jsonify
from models import SessionLocal
from models.project_notification import ProjectNotification, NotificationType
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


def get_current_user():
    """获取当前用户"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    parts = auth_header.split(' ')
    if len(parts) != 2:
        return None
    token = parts[1]
    payload = verify_token(token)
    return payload if payload else None


@notifications_bp.route('', methods=['GET'])
def get_notifications():
    """获取当前用户的通知列表"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        user_id = user.get('user_id') or user.get('id')

        # 获取查询参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        is_read = request.args.get('is_read')
        notification_type = request.args.get('notification_type')

        # 构建查询
        query = session.query(ProjectNotification).filter_by(recipient_id=user_id)

        # 筛选条件
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            query = query.filter_by(is_read=is_read_bool)

        if notification_type:
            query = query.filter_by(notification_type=notification_type)

        # 排序和分页
        total = query.count()
        notifications = query.order_by(
            ProjectNotification.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return jsonify({
            'notifications': [n.to_dict() for n in notifications],
            'total': total,
            'page': page,
            'page_size': page_size
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@notifications_bp.route('/unread-count', methods=['GET'])
def get_unread_count():
    """获取未读通知数量"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        user_id = user.get('user_id') or user.get('id')

        count = session.query(ProjectNotification).filter_by(
            recipient_id=user_id,
            is_read=False
        ).count()

        return jsonify({'count': count}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
def mark_as_read(notification_id):
    """标记通知为已读"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        user_id = user.get('user_id') or user.get('id')

        notification = session.query(ProjectNotification).filter_by(
            id=notification_id,
            recipient_id=user_id
        ).first()

        if not notification:
            return jsonify({'error': '通知不存在'}), 404

        notification.is_read = True
        notification.read_at = datetime.now()

        session.commit()
        session.refresh(notification)

        return jsonify(notification.to_dict()), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@notifications_bp.route('/mark-all-read', methods=['POST'])
def mark_all_as_read():
    """标记所有通知为已读"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        user_id = user.get('user_id') or user.get('id')

        session.query(ProjectNotification).filter_by(
            recipient_id=user_id,
            is_read=False
        ).update({
            'is_read': True,
            'read_at': datetime.now()
        })

        session.commit()

        return jsonify({'message': '所有通知已标记为已读'}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """删除通知"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        user_id = user.get('user_id') or user.get('id')

        notification = session.query(ProjectNotification).filter_by(
            id=notification_id,
            recipient_id=user_id
        ).first()

        if not notification:
            return jsonify({'error': '通知不存在'}), 404

        session.delete(notification)
        session.commit()

        return jsonify({'message': '通知已删除'}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# 工具函数：创建通知
def create_notification(
    recipient_id,
    notification_type,
    title=None,
    content=None,
    project_id=None,
    task_id=None,
    issue_id=None,
    related_data=None,
    channels=None,
    recipient_name=None
):
    """
    创建通知的工具函数

    Args:
        recipient_id: 接收者ID
        notification_type: 通知类型 (NotificationType)
        title: 标题 (可选，如果不提供会自动生成)
        content: 内容
        project_id: 关联项目ID
        task_id: 关联任务ID
        issue_id: 关联问题ID
        related_data: 相关数据 (dict)
        channels: 发送渠道列表 (默认 ['in_app'])
        recipient_name: 接收者姓名
    """
    session = SessionLocal()
    try:
        # 如果没有提供标题，自动生成
        if not title:
            title = ProjectNotification.get_notification_title(
                notification_type,
                **(related_data or {})
            )

        notification = ProjectNotification(
            recipient_id=recipient_id,
            recipient_name=recipient_name,
            notification_type=notification_type,
            title=title,
            content=content,
            project_id=project_id,
            task_id=task_id,
            issue_id=issue_id,
            related_data=related_data,
            channels=channels or ['in_app']
        )

        session.add(notification)
        session.commit()
        session.refresh(notification)

        return notification

    except Exception as e:
        session.rollback()
        print(f"创建通知失败: {str(e)}")
        return None
    finally:
        session.close()
