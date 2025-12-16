"""
Project Notification Model - 项目通知
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from models import Base


class NotificationType(str, enum.Enum):
    """通知类型"""
    TASK_ASSIGNED = 'task_assigned'              # 任务分配
    TASK_DUE_SOON = 'task_due_soon'              # 截止日期临近（24h）
    TASK_OVERDUE = 'task_overdue'                # 任务逾期
    TASK_COMPLETED = 'task_completed'            # 任务完成
    PHASE_COMPLETED = 'phase_completed'          # 阶段完成
    MILESTONE_REACHED = 'milestone_reached'      # 里程碑达成
    FILE_UPLOADED = 'file_uploaded'              # 文件上传
    FILE_VERSION_UPDATED = 'file_version_updated'  # 文件版本更新
    MEMBER_ADDED = 'member_added'                # 成员加入
    MEMBER_REMOVED = 'member_removed'            # 成员移除
    PROJECT_DELAYED = 'project_delayed'          # 项目延期
    ISSUE_CREATED = 'issue_created'              # 问题创建
    ISSUE_RESOLVED = 'issue_resolved'            # 问题解决
    COMMENT_ADDED = 'comment_added'              # 评论添加
    APPROVAL_REQUIRED = 'approval_required'      # 需要审批
    PROJECT_STATUS_CHANGED = 'project_status_changed'  # 项目状态变更
    MENTION = 'mention'                          # @提及


class NotificationChannel(str, enum.Enum):
    """通知渠道"""
    IN_APP = 'in_app'      # 应用内通知
    EMAIL = 'email'        # 邮件
    WECHAT = 'wechat'      # 企业微信


class ProjectNotification(Base):
    """项目通知模型"""
    __tablename__ = 'project_notifications'

    id = Column(Integer, primary_key=True, index=True)

    # 接收者
    recipient_id = Column(Integer, nullable=False, index=True)
    recipient_name = Column(String(100))

    # 关联
    project_id = Column(Integer, ForeignKey('projects.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True)
    issue_id = Column(Integer, nullable=True)  # 暂时不用外键，等 Issue 模型创建后再添加

    # 通知内容
    notification_type = Column(Enum(NotificationType), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)

    # 关联数据（JSON）
    related_data = Column(JSON, nullable=True)  # 存储额外的相关数据，如任务ID、文件名等

    # 状态
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # 发送渠道
    channels = Column(JSON, default=list)  # ['in_app', 'email', 'wechat']

    # 时间
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    project = relationship('Project', backref='notifications', foreign_keys=[project_id])
    task = relationship('Task', backref='notifications', foreign_keys=[task_id])

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'recipient_id': self.recipient_id,
            'recipient_name': self.recipient_name,
            'project_id': self.project_id,
            'task_id': self.task_id,
            'issue_id': self.issue_id,
            'notification_type': self.notification_type.value if self.notification_type else None,
            'title': self.title,
            'content': self.content,
            'related_data': self.related_data,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'channels': self.channels,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @staticmethod
    def get_notification_title(notification_type, **kwargs):
        """根据通知类型生成标题"""
        titles = {
            NotificationType.TASK_ASSIGNED: f"新任务分配：{kwargs.get('task_name', '未知任务')}",
            NotificationType.TASK_DUE_SOON: f"任务即将到期：{kwargs.get('task_name', '未知任务')}",
            NotificationType.TASK_OVERDUE: f"任务已逾期：{kwargs.get('task_name', '未知任务')}",
            NotificationType.TASK_COMPLETED: f"任务已完成：{kwargs.get('task_name', '未知任务')}",
            NotificationType.PHASE_COMPLETED: f"阶段已完成：{kwargs.get('phase_name', '未知阶段')}",
            NotificationType.MILESTONE_REACHED: f"里程碑达成：{kwargs.get('milestone_name', '未知里程碑')}",
            NotificationType.FILE_UPLOADED: f"新文件上传：{kwargs.get('file_name', '未知文件')}",
            NotificationType.FILE_VERSION_UPDATED: f"文件版本更新：{kwargs.get('file_name', '未知文件')}",
            NotificationType.MEMBER_ADDED: f"新成员加入：{kwargs.get('member_name', '未知成员')}",
            NotificationType.MEMBER_REMOVED: f"成员移除：{kwargs.get('member_name', '未知成员')}",
            NotificationType.PROJECT_DELAYED: f"项目延期：{kwargs.get('project_name', '未知项目')}",
            NotificationType.ISSUE_CREATED: f"新问题创建：{kwargs.get('issue_title', '未知问题')}",
            NotificationType.ISSUE_RESOLVED: f"问题已解决：{kwargs.get('issue_title', '未知问题')}",
            NotificationType.COMMENT_ADDED: f"新评论：{kwargs.get('commenter_name', '未知用户')}",
            NotificationType.APPROVAL_REQUIRED: f"需要审批：{kwargs.get('approval_type', '未知审批')}",
            NotificationType.PROJECT_STATUS_CHANGED: f"项目状态变更：{kwargs.get('project_name', '未知项目')}",
            NotificationType.MENTION: f"{kwargs.get('mentioner_name', '未知用户')} 提到了你",
        }
        return titles.get(notification_type, '新通知')
