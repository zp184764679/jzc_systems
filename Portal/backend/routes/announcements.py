# -*- coding: utf-8 -*-
"""
Announcements API - 系统公告管理
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from functools import wraps
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token, User, AuditService
import shared.auth.models as auth_models
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index, BigInteger
from sqlalchemy.orm import sessionmaker

announcements_bp = Blueprint('announcements', __name__, url_prefix='/api/announcements')

# 使用共享的数据库引擎
from shared.auth.models import AuthBase, AuthEngine, AuthSessionLocal


class Announcement(AuthBase):
    """系统公告模型"""
    __tablename__ = 'announcements'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), default='general')  # general, urgent, maintenance, update
    priority = Column(Integer, default=0)  # 0=普通, 1=重要, 2=紧急
    status = Column(String(20), default='draft')  # draft, published, archived

    # 发布时间控制
    publish_at = Column(DateTime, nullable=True)  # 定时发布
    expire_at = Column(DateTime, nullable=True)  # 过期时间

    # 目标受众
    target_roles = Column(String(200), nullable=True)  # JSON: ["user", "admin"] 或 null 表示全部
    target_departments = Column(String(500), nullable=True)  # JSON: 部门ID列表

    # 元数据
    author_id = Column(Integer, nullable=False)
    author_name = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    # 统计
    view_count = Column(Integer, default=0)

    __table_args__ = (
        Index('idx_announcement_status', 'status'),
        Index('idx_announcement_publish', 'publish_at'),
    )

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'priority': self.priority,
            'status': self.status,
            'publish_at': self.publish_at.isoformat() if self.publish_at else None,
            'expire_at': self.expire_at.isoformat() if self.expire_at else None,
            'target_roles': json.loads(self.target_roles) if self.target_roles else None,
            'target_departments': json.loads(self.target_departments) if self.target_departments else None,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'view_count': self.view_count
        }


class AnnouncementRead(AuthBase):
    """公告已读记录"""
    __tablename__ = 'announcement_reads'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    announcement_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    read_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_announcement_read_unique', 'announcement_id', 'user_id', unique=True),
    )


# 确保表存在
def init_announcement_tables():
    """初始化公告相关表"""
    if AuthEngine:
        AuthBase.metadata.create_all(bind=AuthEngine)


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


@announcements_bp.route('', methods=['GET'])
@require_auth
def get_announcements():
    """获取公告列表"""
    user = request.current_user
    user_id = user.get('user_id') or user.get('id')
    role = user.get('role', 'user')
    is_admin = role in ['admin', 'super_admin']

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    include_read = request.args.get('include_read', 'true').lower() == 'true'

    session = AuthSessionLocal()
    try:
        # 初始化表
        init_announcement_tables()

        query = session.query(Announcement)

        # 非管理员只能看已发布的公告
        if not is_admin or not status_filter:
            if not is_admin:
                query = query.filter(Announcement.status == 'published')
                # 过滤过期公告
                query = query.filter(
                    (Announcement.expire_at.is_(None)) |
                    (Announcement.expire_at > datetime.utcnow())
                )
        elif status_filter:
            query = query.filter(Announcement.status == status_filter)

        if category_filter:
            query = query.filter(Announcement.category == category_filter)

        total = query.count()
        announcements = query.order_by(
            Announcement.priority.desc(),
            Announcement.published_at.desc().nulls_last(),
            Announcement.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        # 获取已读状态
        read_ids = set()
        if include_read:
            reads = session.query(AnnouncementRead.announcement_id).filter(
                AnnouncementRead.user_id == user_id,
                AnnouncementRead.announcement_id.in_([a.id for a in announcements])
            ).all()
            read_ids = {r[0] for r in reads}

        result = []
        for a in announcements:
            data = a.to_dict()
            data['is_read'] = a.id in read_ids
            result.append(data)

        return jsonify({
            'items': result,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size if page_size else 1
        })
    finally:
        session.close()


@announcements_bp.route('/unread-count', methods=['GET'])
@require_auth
def get_unread_count():
    """获取未读公告数量"""
    user = request.current_user
    user_id = user.get('user_id') or user.get('id')

    session = AuthSessionLocal()
    try:
        init_announcement_tables()

        # 获取已发布且未过期的公告数
        total_query = session.query(Announcement).filter(
            Announcement.status == 'published',
            (Announcement.expire_at.is_(None)) | (Announcement.expire_at > datetime.utcnow())
        )
        total = total_query.count()

        # 获取已读数
        read_count = session.query(AnnouncementRead).filter(
            AnnouncementRead.user_id == user_id,
            AnnouncementRead.announcement_id.in_(
                total_query.with_entities(Announcement.id)
            )
        ).count()

        return jsonify({
            'unread_count': total - read_count,
            'total': total
        })
    finally:
        session.close()


@announcements_bp.route('/<int:announcement_id>', methods=['GET'])
@require_auth
def get_announcement(announcement_id):
    """获取单个公告详情"""
    user = request.current_user
    user_id = user.get('user_id') or user.get('id')
    role = user.get('role', 'user')
    is_admin = role in ['admin', 'super_admin']

    session = AuthSessionLocal()
    try:
        init_announcement_tables()

        announcement = session.query(Announcement).filter_by(id=announcement_id).first()
        if not announcement:
            return jsonify({'error': '公告不存在'}), 404

        # 非管理员只能查看已发布的公告
        if not is_admin and announcement.status != 'published':
            return jsonify({'error': '公告不存在'}), 404

        # 增加浏览次数
        announcement.view_count = (announcement.view_count or 0) + 1
        session.commit()

        # 检查是否已读
        is_read = session.query(AnnouncementRead).filter_by(
            announcement_id=announcement_id,
            user_id=user_id
        ).first() is not None

        data = announcement.to_dict()
        data['is_read'] = is_read

        return jsonify(data)
    finally:
        session.close()


@announcements_bp.route('', methods=['POST'])
@require_auth
@require_admin
def create_announcement():
    """创建公告"""
    import json
    user = request.current_user
    user_id = user.get('user_id') or user.get('id')
    data = request.get_json()

    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': '标题和内容不能为空'}), 400

    session = AuthSessionLocal()
    try:
        init_announcement_tables()

        announcement = Announcement(
            title=data['title'],
            content=data['content'],
            category=data.get('category', 'general'),
            priority=data.get('priority', 0),
            status='draft',
            author_id=user_id,
            author_name=user.get('full_name') or user.get('username'),
            target_roles=json.dumps(data['target_roles']) if data.get('target_roles') else None,
            target_departments=json.dumps(data['target_departments']) if data.get('target_departments') else None
        )

        # 处理发布时间
        if data.get('publish_at'):
            announcement.publish_at = datetime.fromisoformat(data['publish_at'].replace('Z', '+00:00'))
        if data.get('expire_at'):
            announcement.expire_at = datetime.fromisoformat(data['expire_at'].replace('Z', '+00:00'))

        session.add(announcement)
        session.commit()

        # 审计日志
        AuditService.log_action(
            user_id=user_id,
            username=user.get('username'),
            action_type='data_create',
            resource_type='announcement',
            resource_id=str(announcement.id),
            description=f'创建公告: {announcement.title}',
            module='portal'
        )

        return jsonify({
            'message': '公告创建成功',
            'announcement': announcement.to_dict()
        }), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@announcements_bp.route('/<int:announcement_id>', methods=['PUT'])
@require_auth
@require_admin
def update_announcement(announcement_id):
    """更新公告"""
    import json
    user = request.current_user
    user_id = user.get('user_id') or user.get('id')
    data = request.get_json()

    session = AuthSessionLocal()
    try:
        init_announcement_tables()

        announcement = session.query(Announcement).filter_by(id=announcement_id).first()
        if not announcement:
            return jsonify({'error': '公告不存在'}), 404

        if 'title' in data:
            announcement.title = data['title']
        if 'content' in data:
            announcement.content = data['content']
        if 'category' in data:
            announcement.category = data['category']
        if 'priority' in data:
            announcement.priority = data['priority']
        if 'target_roles' in data:
            announcement.target_roles = json.dumps(data['target_roles']) if data['target_roles'] else None
        if 'target_departments' in data:
            announcement.target_departments = json.dumps(data['target_departments']) if data['target_departments'] else None
        if 'publish_at' in data:
            announcement.publish_at = datetime.fromisoformat(data['publish_at'].replace('Z', '+00:00')) if data['publish_at'] else None
        if 'expire_at' in data:
            announcement.expire_at = datetime.fromisoformat(data['expire_at'].replace('Z', '+00:00')) if data['expire_at'] else None

        session.commit()

        # 审计日志
        AuditService.log_action(
            user_id=user_id,
            username=user.get('username'),
            action_type='data_update',
            resource_type='announcement',
            resource_id=str(announcement_id),
            description=f'更新公告: {announcement.title}',
            module='portal'
        )

        return jsonify({
            'message': '公告更新成功',
            'announcement': announcement.to_dict()
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@announcements_bp.route('/<int:announcement_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_announcement(announcement_id):
    """删除公告"""
    user = request.current_user
    user_id = user.get('user_id') or user.get('id')

    session = AuthSessionLocal()
    try:
        init_announcement_tables()

        announcement = session.query(Announcement).filter_by(id=announcement_id).first()
        if not announcement:
            return jsonify({'error': '公告不存在'}), 404

        title = announcement.title

        # 删除已读记录
        session.query(AnnouncementRead).filter_by(announcement_id=announcement_id).delete()
        # 删除公告
        session.delete(announcement)
        session.commit()

        # 审计日志
        AuditService.log_action(
            user_id=user_id,
            username=user.get('username'),
            action_type='data_delete',
            resource_type='announcement',
            resource_id=str(announcement_id),
            description=f'删除公告: {title}',
            module='portal'
        )

        return jsonify({'message': '公告已删除'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@announcements_bp.route('/<int:announcement_id>/publish', methods=['POST'])
@require_auth
@require_admin
def publish_announcement(announcement_id):
    """发布公告"""
    user = request.current_user
    user_id = user.get('user_id') or user.get('id')

    session = AuthSessionLocal()
    try:
        init_announcement_tables()

        announcement = session.query(Announcement).filter_by(id=announcement_id).first()
        if not announcement:
            return jsonify({'error': '公告不存在'}), 404

        if announcement.status == 'published':
            return jsonify({'error': '公告已发布'}), 400

        announcement.status = 'published'
        announcement.published_at = datetime.utcnow()
        session.commit()

        # 审计日志
        AuditService.log_action(
            user_id=user_id,
            username=user.get('username'),
            action_type='data_update',
            resource_type='announcement',
            resource_id=str(announcement_id),
            description=f'发布公告: {announcement.title}',
            module='portal'
        )

        return jsonify({
            'message': '公告已发布',
            'announcement': announcement.to_dict()
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@announcements_bp.route('/<int:announcement_id>/archive', methods=['POST'])
@require_auth
@require_admin
def archive_announcement(announcement_id):
    """归档公告"""
    user = request.current_user
    user_id = user.get('user_id') or user.get('id')

    session = AuthSessionLocal()
    try:
        init_announcement_tables()

        announcement = session.query(Announcement).filter_by(id=announcement_id).first()
        if not announcement:
            return jsonify({'error': '公告不存在'}), 404

        announcement.status = 'archived'
        session.commit()

        return jsonify({
            'message': '公告已归档',
            'announcement': announcement.to_dict()
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@announcements_bp.route('/<int:announcement_id>/read', methods=['POST'])
@require_auth
def mark_as_read(announcement_id):
    """标记公告为已读"""
    user = request.current_user
    user_id = user.get('user_id') or user.get('id')

    session = AuthSessionLocal()
    try:
        init_announcement_tables()

        # 检查公告是否存在
        announcement = session.query(Announcement).filter_by(id=announcement_id).first()
        if not announcement:
            return jsonify({'error': '公告不存在'}), 404

        # 检查是否已读
        existing = session.query(AnnouncementRead).filter_by(
            announcement_id=announcement_id,
            user_id=user_id
        ).first()

        if not existing:
            read_record = AnnouncementRead(
                announcement_id=announcement_id,
                user_id=user_id
            )
            session.add(read_record)
            session.commit()

        return jsonify({'message': '已标记为已读'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@announcements_bp.route('/mark-all-read', methods=['POST'])
@require_auth
def mark_all_as_read():
    """标记所有公告为已读"""
    user = request.current_user
    user_id = user.get('user_id') or user.get('id')

    session = AuthSessionLocal()
    try:
        init_announcement_tables()

        # 获取所有已发布且未过期的公告ID
        published = session.query(Announcement.id).filter(
            Announcement.status == 'published',
            (Announcement.expire_at.is_(None)) | (Announcement.expire_at > datetime.utcnow())
        ).all()

        # 获取已读的公告ID
        already_read = session.query(AnnouncementRead.announcement_id).filter(
            AnnouncementRead.user_id == user_id
        ).all()
        already_read_ids = {r[0] for r in already_read}

        # 标记未读的为已读
        marked = 0
        for (ann_id,) in published:
            if ann_id not in already_read_ids:
                read_record = AnnouncementRead(
                    announcement_id=ann_id,
                    user_id=user_id
                )
                session.add(read_record)
                marked += 1

        session.commit()

        return jsonify({
            'message': f'已将 {marked} 条公告标记为已读',
            'marked_count': marked
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@announcements_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取公告分类"""
    return jsonify({
        'categories': [
            {'value': 'general', 'label': '普通公告', 'color': '#1890ff'},
            {'value': 'urgent', 'label': '紧急通知', 'color': '#f5222d'},
            {'value': 'maintenance', 'label': '系统维护', 'color': '#faad14'},
            {'value': 'update', 'label': '功能更新', 'color': '#52c41a'},
        ],
        'priorities': [
            {'value': 0, 'label': '普通'},
            {'value': 1, 'label': '重要'},
            {'value': 2, 'label': '紧急'},
        ],
        'statuses': [
            {'value': 'draft', 'label': '草稿'},
            {'value': 'published', 'label': '已发布'},
            {'value': 'archived', 'label': '已归档'},
        ]
    })
