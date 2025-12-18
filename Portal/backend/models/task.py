"""
Task Model - 任务管理模型
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from models import Base
import enum


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = 'pending'             # 待开始
    IN_PROGRESS = 'in_progress'     # 进行中
    COMPLETED = 'completed'         # 已完成
    CANCELLED = 'cancelled'         # 已取消
    BLOCKED = 'blocked'             # 受阻


class TaskPriority(str, enum.Enum):
    """任务优先级枚举"""
    LOW = 'low'           # 低
    NORMAL = 'normal'     # 普通
    HIGH = 'high'         # 高
    URGENT = 'urgent'     # 紧急


class TaskType(str, enum.Enum):
    """任务类型枚举"""
    GENERAL = 'general'             # 常规任务
    DESIGN = 'design'               # 设计
    DEVELOPMENT = 'development'     # 开发
    TESTING = 'testing'             # 测试
    REVIEW = 'review'               # 审查
    DEPLOYMENT = 'deployment'       # 部署
    DOCUMENTATION = 'documentation' # 文档
    MEETING = 'meeting'             # 会议
    OTHER = 'other'                 # 其他


class Task(Base):
    """任务表"""
    __tablename__ = 'tasks'

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 关联项目
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True, comment='所属项目ID')

    # 任务信息
    task_no = Column(String(50), unique=True, nullable=False, index=True, comment='任务编号')
    title = Column(String(200), nullable=False, comment='任务标题')
    description = Column(Text, comment='任务描述')
    task_type = Column(
        Enum(TaskType, values_callable=lambda x: [e.value for e in x]),
        default=TaskType.GENERAL,
        nullable=False,
        comment='任务类型'
    )

    # 时间字段
    start_date = Column(Date, comment='开始日期')
    due_date = Column(Date, comment='截止日期')
    completed_at = Column(DateTime, comment='完成时间')

    # 状态和优先级
    status = Column(
        Enum(TaskStatus, values_callable=lambda x: [e.value for e in x]),
        default=TaskStatus.PENDING,
        nullable=False,
        comment='任务状态'
    )
    priority = Column(
        Enum(TaskPriority, values_callable=lambda x: [e.value for e in x]),
        default=TaskPriority.NORMAL,
        nullable=False,
        comment='优先级'
    )

    # 分配和创建
    assigned_to_id = Column(Integer, comment='分配给(用户ID)')
    created_by_id = Column(Integer, nullable=False, comment='创建者ID')

    # 依赖关系
    depends_on_task_id = Column(Integer, ForeignKey('tasks.id'), comment='依赖的任务ID')

    # 提醒设置
    reminder_enabled = Column(Boolean, default=False, comment='是否启用提醒')
    reminder_days_before = Column(Integer, default=1, comment='提前提醒天数')

    # 里程碑标记
    is_milestone = Column(Boolean, default=False, comment='是否为里程碑')

    # 阶段关联（任务导向管理）
    phase_id = Column(Integer, ForeignKey('project_phases.id'), comment='所属阶段ID')

    # 任务权重和完成度（用于进度计算）
    weight = Column(Integer, default=1, comment='任务权重(1-10)')
    completion_percentage = Column(Integer, default=0, comment='完成百分比(0-100)')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 关系
    # project = relationship('Project', back_populates='tasks')
    # depends_on = relationship('Task', remote_side=[id], foreign_keys=[depends_on_task_id])

    def to_dict(self):
        """Convert to dictionary"""
        # Get task_type value (convert to lowercase for frontend)
        if isinstance(self.task_type, TaskType):
            task_type_val = self.task_type.value
        elif self.task_type:
            task_type_val = str(self.task_type).lower()
        else:
            task_type_val = 'general'

        # Get status value (convert to lowercase for frontend)
        if isinstance(self.status, TaskStatus):
            status_val = self.status.value
        elif self.status:
            status_val = str(self.status).lower()
        else:
            status_val = 'pending'

        # Get priority value (convert to lowercase for frontend)
        if isinstance(self.priority, TaskPriority):
            priority_val = self.priority.value
        elif self.priority:
            priority_val = str(self.priority).lower()
        else:
            priority_val = 'normal'

        return {
            'id': self.id,
            'project_id': self.project_id,
            'task_no': self.task_no,
            'title': self.title,
            'description': self.description,
            'task_type': task_type_val,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': status_val,
            'priority': priority_val,
            'assigned_to_id': self.assigned_to_id,
            'created_by_id': self.created_by_id,
            'depends_on_task_id': self.depends_on_task_id,
            'reminder_enabled': self.reminder_enabled,
            'reminder_days_before': self.reminder_days_before,
            'is_milestone': self.is_milestone,
            'phase_id': self.phase_id,
            'weight': self.weight or 1,
            'completion_percentage': self.completion_percentage or 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Task {self.task_no}: {self.title}>"
