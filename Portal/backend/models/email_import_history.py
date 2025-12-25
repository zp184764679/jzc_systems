"""
EmailImportHistory Model - 邮件导入历史模型
用于记录从邮件翻译系统导入任务/项目的历史记录，支持重复检测和审计追踪
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON
from datetime import datetime
from models import Base
import enum


class ImportMode(str, enum.Enum):
    """导入模式枚举"""
    TASK = 'task'                       # 仅导入为任务
    PROJECT = 'project'                 # 仅导入为项目
    TASK_AND_PROJECT = 'task_and_project'  # 同时创建任务和项目


class EmailImportHistory(Base):
    """邮件导入历史表"""
    __tablename__ = 'email_import_history'

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 邮件信息（来自邮件翻译系统）
    email_id = Column(Integer, nullable=False, index=True, comment='邮件翻译系统的邮件ID')
    email_message_id = Column(String(255), index=True, comment='邮件 Message-ID 头（用于去重）')
    email_subject = Column(String(500), comment='导入时的邮件主题')
    email_from = Column(String(200), comment='发件人')
    email_received_at = Column(DateTime, comment='邮件接收时间')

    # 创建的实体
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='SET NULL'), index=True, comment='创建的任务ID')
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), index=True, comment='创建的项目ID')
    import_mode = Column(
        Enum(ImportMode, values_callable=lambda x: [e.value for e in x]),
        default=ImportMode.TASK,
        comment='导入模式'
    )

    # 导入者信息
    imported_by = Column(Integer, nullable=False, index=True, comment='导入用户ID')
    imported_by_name = Column(String(100), comment='导入用户姓名')
    imported_at = Column(DateTime, default=datetime.now, index=True, comment='导入时间')

    # 提取数据快照（用于审计和问题排查）
    extraction_data = Column(JSON, comment='AI提取的原始数据快照')
    matched_project_id = Column(Integer, comment='智能匹配的项目ID')
    matched_employee_id = Column(Integer, comment='智能匹配的员工ID')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'email_id': self.email_id,
            'email_message_id': self.email_message_id,
            'email_subject': self.email_subject,
            'email_from': self.email_from,
            'email_received_at': self.email_received_at.isoformat() if self.email_received_at else None,
            'task_id': self.task_id,
            'project_id': self.project_id,
            'import_mode': self.import_mode.value if self.import_mode else 'task',
            'imported_by': self.imported_by,
            'imported_by_name': self.imported_by_name,
            'imported_at': self.imported_at.isoformat() if self.imported_at else None,
            'extraction_data': self.extraction_data,
            'matched_project_id': self.matched_project_id,
            'matched_employee_id': self.matched_employee_id,
        }

    def __repr__(self):
        return f"<EmailImportHistory email_id={self.email_id} task_id={self.task_id}>"
