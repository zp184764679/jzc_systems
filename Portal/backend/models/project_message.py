"""
Project Message Model - 项目聊天消息模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from models import Base
import enum


class MessageType(str, enum.Enum):
    """消息类型枚举"""
    TEXT = 'text'       # 普通文本消息
    SYSTEM = 'system'   # 系统消息


class ProjectMessage(Base):
    """项目聊天消息表"""
    __tablename__ = 'project_messages'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True, comment='所属项目ID')
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), index=True, comment='关联任务ID')
    sender_id = Column(Integer, nullable=False, index=True, comment='发送者用户ID')
    sender_name = Column(String(100), nullable=False, comment='发送者姓名')
    content = Column(Text, nullable=False, comment='消息内容')
    message_type = Column(
        Enum(MessageType),
        default=MessageType.TEXT,
        nullable=False,
        comment='消息类型'
    )
    mentions = Column(JSON, comment='@提醒的用户ID列表')
    is_edited = Column(Boolean, default=False, comment='是否已编辑')
    is_deleted = Column(Boolean, default=False, comment='是否已删除')
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def to_dict(self):
        """Convert to dictionary"""
        message_type_val = self.message_type.value if hasattr(self.message_type, 'value') else str(self.message_type)

        return {
            'id': self.id,
            'project_id': self.project_id,
            'task_id': self.task_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender_name,
            'content': self.content,
            'message_type': message_type_val,
            'mentions': self.mentions or [],
            'is_edited': self.is_edited,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<ProjectMessage {self.id} by {self.sender_name}>"


class MessageReadStatus(Base):
    """消息已读状态表"""
    __tablename__ = 'message_read_status'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True, comment='用户ID')
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True, comment='项目ID')
    last_read_message_id = Column(Integer, comment='最后已读消息ID')
    last_read_at = Column(DateTime, default=datetime.now, comment='最后已读时间')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'last_read_message_id': self.last_read_message_id,
            'last_read_at': self.last_read_at.isoformat() if self.last_read_at else None,
        }
