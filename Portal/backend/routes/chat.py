"""
项目聊天 API Routes
提供项目级聊天和任务评论功能
"""
from flask import Blueprint, request, jsonify
from sqlalchemy import func, or_, and_
from datetime import datetime
import logging
import re
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token

from models import SessionLocal
from models.project import Project
from models.task import Task
from models.project_message import ProjectMessage, MessageReadStatus
from models.project_member import ProjectMember

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')


def get_current_user():
    """从请求头获取当前用户"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    parts = auth_header.split(' ')
    if len(parts) != 2:
        return None
    token = parts[1]
    payload = verify_token(token)
    return payload if payload else None


def extract_mentions(content):
    """从消息内容中提取 @提醒的用户ID"""
    # 匹配 @[用户名](user_id) 或 @用户名 格式
    pattern = r'@\[([^\]]+)\]\((\d+)\)'
    matches = re.findall(pattern, content)
    return [int(user_id) for _, user_id in matches]


# ============================================================
# 项目聊天 API
# ============================================================

@chat_bp.route('/project/<int:project_id>/messages', methods=['GET'])
def get_project_messages(project_id):
    """获取项目聊天消息（分页）

    Query参数:
        - page: 页码 (默认1)
        - page_size: 每页数量 (默认50)
        - since_id: 获取此ID之后的消息（用于轮询新消息）
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # 验证项目存在
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)
        since_id = request.args.get('since_id', type=int)

        # 构建查询 - 只获取项目级消息 (task_id is NULL)
        query = session.query(ProjectMessage).filter(
            ProjectMessage.project_id == project_id,
            ProjectMessage.task_id == None,
            ProjectMessage.is_deleted == False
        )

        # 如果指定了 since_id，获取该ID之后的消息
        if since_id:
            query = query.filter(ProjectMessage.id > since_id)
            messages = query.order_by(ProjectMessage.created_at.asc()).all()
            return jsonify({
                'messages': [m.to_dict() for m in messages],
                'new_count': len(messages)
            }), 200

        # 分页获取
        total = query.count()
        offset = (page - 1) * page_size
        messages = query.order_by(ProjectMessage.created_at.desc())\
                       .offset(offset).limit(page_size).all()

        # 反转顺序，让最新的在后面
        messages = list(reversed(messages))

        return jsonify({
            'messages': [m.to_dict() for m in messages],
            'total': total,
            'page': page,
            'page_size': page_size
        }), 200

    except Exception as e:
        logger.error(f"Get project messages failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@chat_bp.route('/project/<int:project_id>/messages', methods=['POST'])
def send_project_message(project_id):
    """发送项目聊天消息

    Request Body:
        {
            "content": "消息内容",
            "mentions": [1, 2, 3]  // 可选，@提醒的用户ID
        }
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data or not data.get('content', '').strip():
        return jsonify({'error': '消息内容不能为空'}), 400

    session = SessionLocal()
    try:
        # 验证项目存在
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        content = data['content'].strip()
        mentions = data.get('mentions') or extract_mentions(content)

        user_id = user.get('user_id') or user.get('id')
        username = user.get('username') or user.get('full_name') or 'Unknown'

        message = ProjectMessage(
            project_id=project_id,
            task_id=None,
            sender_id=user_id,
            sender_name=username,
            content=content,
            message_type='text',
            mentions=mentions if mentions else None
        )

        session.add(message)
        session.commit()
        session.refresh(message)

        # TODO: 如果有 @提醒，发送通知
        if mentions:
            logger.info(f"Message {message.id} mentions users: {mentions}")
            # 可以在这里调用通知服务发送 @提醒通知

        return jsonify({
            'message': '消息发送成功',
            'data': message.to_dict()
        }), 201

    except Exception as e:
        session.rollback()
        logger.error(f"Send project message failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 任务评论 API
# ============================================================

@chat_bp.route('/task/<int:task_id>/comments', methods=['GET'])
def get_task_comments(task_id):
    """获取任务评论"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # 验证任务存在
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)

        query = session.query(ProjectMessage).filter(
            ProjectMessage.task_id == task_id,
            ProjectMessage.is_deleted == False
        )

        total = query.count()
        offset = (page - 1) * page_size
        comments = query.order_by(ProjectMessage.created_at.asc())\
                       .offset(offset).limit(page_size).all()

        return jsonify({
            'comments': [c.to_dict() for c in comments],
            'total': total,
            'page': page,
            'page_size': page_size
        }), 200

    except Exception as e:
        logger.error(f"Get task comments failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@chat_bp.route('/task/<int:task_id>/comments', methods=['POST'])
def add_task_comment(task_id):
    """添加任务评论"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data or not data.get('content', '').strip():
        return jsonify({'error': '评论内容不能为空'}), 400

    session = SessionLocal()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        content = data['content'].strip()
        mentions = data.get('mentions') or extract_mentions(content)

        user_id = user.get('user_id') or user.get('id')
        username = user.get('username') or user.get('full_name') or 'Unknown'

        comment = ProjectMessage(
            project_id=task.project_id,
            task_id=task_id,
            sender_id=user_id,
            sender_name=username,
            content=content,
            message_type='text',
            mentions=mentions if mentions else None
        )

        session.add(comment)
        session.commit()
        session.refresh(comment)

        return jsonify({
            'message': '评论发送成功',
            'data': comment.to_dict()
        }), 201

    except Exception as e:
        session.rollback()
        logger.error(f"Add task comment failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 消息管理 API
# ============================================================

@chat_bp.route('/messages/<int:message_id>', methods=['PUT'])
def edit_message(message_id):
    """编辑消息"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data or not data.get('content', '').strip():
        return jsonify({'error': '消息内容不能为空'}), 400

    session = SessionLocal()
    try:
        message = session.query(ProjectMessage).filter_by(id=message_id).first()
        if not message:
            return jsonify({'error': '消息不存在'}), 404

        user_id = user.get('user_id') or user.get('id')
        if message.sender_id != user_id:
            return jsonify({'error': '只能编辑自己的消息'}), 403

        message.content = data['content'].strip()
        message.is_edited = True
        message.mentions = data.get('mentions') or extract_mentions(message.content)

        session.commit()
        session.refresh(message)

        return jsonify({
            'message': '消息已更新',
            'data': message.to_dict()
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Edit message failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@chat_bp.route('/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """删除消息（软删除）"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        message = session.query(ProjectMessage).filter_by(id=message_id).first()
        if not message:
            return jsonify({'error': '消息不存在'}), 404

        user_id = user.get('user_id') or user.get('id')
        role = user.get('role', '')
        is_admin = role in ['admin', 'super_admin', '管理员', '超级管理员']

        if message.sender_id != user_id and not is_admin:
            return jsonify({'error': '没有删除权限'}), 403

        message.is_deleted = True
        session.commit()

        return jsonify({'message': '消息已删除'}), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Delete message failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 已读状态 API
# ============================================================

@chat_bp.route('/project/<int:project_id>/read', methods=['POST'])
def mark_as_read(project_id):
    """标记项目消息已读"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        user_id = user.get('user_id') or user.get('id')

        # 获取最新消息ID
        latest_message = session.query(ProjectMessage).filter(
            ProjectMessage.project_id == project_id,
            ProjectMessage.task_id == None,
            ProjectMessage.is_deleted == False
        ).order_by(ProjectMessage.id.desc()).first()

        if not latest_message:
            return jsonify({'message': '没有消息需要标记'}), 200

        # 更新或创建已读状态
        read_status = session.query(MessageReadStatus).filter_by(
            user_id=user_id,
            project_id=project_id
        ).first()

        if read_status:
            read_status.last_read_message_id = latest_message.id
            read_status.last_read_at = datetime.now()
        else:
            read_status = MessageReadStatus(
                user_id=user_id,
                project_id=project_id,
                last_read_message_id=latest_message.id
            )
            session.add(read_status)

        session.commit()

        return jsonify({
            'message': '已标记已读',
            'last_read_message_id': latest_message.id
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Mark as read failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@chat_bp.route('/unread-summary', methods=['GET'])
def get_unread_summary():
    """获取用户所有项目的未读消息统计"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        user_id = user.get('user_id') or user.get('id')

        # 获取用户参与的项目
        member_projects = session.query(ProjectMember.project_id).filter_by(
            user_id=user_id
        ).subquery()

        # 获取用户创建的项目
        created_projects = session.query(Project.id).filter_by(
            created_by_id=user_id
        ).subquery()

        # 合并所有相关项目
        all_projects = session.query(Project).filter(
            or_(
                Project.id.in_(member_projects),
                Project.id.in_(created_projects)
            ),
            Project.deleted_at == None
        ).all()

        unread_by_project = []
        total_unread = 0

        for project in all_projects:
            # 获取已读状态
            read_status = session.query(MessageReadStatus).filter_by(
                user_id=user_id,
                project_id=project.id
            ).first()

            last_read_id = read_status.last_read_message_id if read_status else 0

            # 统计未读消息数
            unread_count = session.query(func.count(ProjectMessage.id)).filter(
                ProjectMessage.project_id == project.id,
                ProjectMessage.task_id == None,
                ProjectMessage.is_deleted == False,
                ProjectMessage.id > (last_read_id or 0),
                ProjectMessage.sender_id != user_id  # 排除自己发送的
            ).scalar() or 0

            if unread_count > 0:
                unread_by_project.append({
                    'project_id': project.id,
                    'project_name': project.name,
                    'unread_count': unread_count
                })
                total_unread += unread_count

        return jsonify({
            'total_unread': total_unread,
            'by_project': unread_by_project
        }), 200

    except Exception as e:
        logger.error(f"Get unread summary failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 项目成员列表 (用于@提醒)
# ============================================================

@chat_bp.route('/project/<int:project_id>/members', methods=['GET'])
def get_chat_members(project_id):
    """获取项目成员列表（用于@提醒选择）"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # 获取项目成员
        members = session.query(ProjectMember).filter_by(project_id=project_id).all()

        member_list = []
        for m in members:
            member_list.append({
                'user_id': m.user_id,
                'name': m.member_name or f'User {m.user_id}',
                'role': m.role
            })

        # 添加项目创建者
        if project.created_by_id:
            # 检查创建者是否已在成员列表
            if not any(m['user_id'] == project.created_by_id for m in member_list):
                member_list.insert(0, {
                    'user_id': project.created_by_id,
                    'name': project.created_by_name or f'User {project.created_by_id}',
                    'role': 'owner'
                })

        return jsonify({
            'members': member_list
        }), 200

    except Exception as e:
        logger.error(f"Get chat members failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
