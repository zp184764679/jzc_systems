"""
Project Model - 项目管理核心模型
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from models import Base
import enum


class ProjectStatus(str, enum.Enum):
    """项目状态枚举"""
    PLANNING = 'planning'           # 规划中
    IN_PROGRESS = 'in_progress'     # 进行中
    ON_HOLD = 'on_hold'             # 暂停
    COMPLETED = 'completed'         # 已完成
    CANCELLED = 'cancelled'         # 已取消


class ProjectPriority(str, enum.Enum):
    """项目优先级枚举"""
    LOW = 'low'           # 低
    NORMAL = 'normal'     # 普通
    HIGH = 'high'         # 高
    URGENT = 'urgent'     # 紧急


class Project(Base):
    """项目表"""
    __tablename__ = 'projects'

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    project_no = Column(String(50), unique=True, nullable=False, index=True, comment='项目编号')
    name = Column(String(200), nullable=False, comment='项目名称')
    description = Column(Text, comment='项目描述')
    customer = Column(String(200), comment='客户名称（冗余字段，兼容旧数据）')
    customer_id = Column(Integer, index=True, comment='CRM 客户 ID')
    customer_name = Column(String(200), comment='客户名称（从 CRM 同步）')
    order_no = Column(String(100), index=True, comment='订单号')

    # 时间字段
    planned_start_date = Column(Date, comment='计划开始日期')
    planned_end_date = Column(Date, comment='计划结束日期')
    actual_start_date = Column(Date, comment='实际开始日期')
    actual_end_date = Column(Date, comment='实际结束日期')

    # 状态和优先级
    status = Column(
        Enum(ProjectStatus),
        default=ProjectStatus.PLANNING,
        nullable=False,
        comment='项目状态'
    )
    priority = Column(
        Enum(ProjectPriority),
        default=ProjectPriority.NORMAL,
        nullable=False,
        comment='优先级'
    )

    # 进度
    progress_percentage = Column(Integer, default=0, comment='进度百分比(0-100)')

    # 负责人 - 外键关联 shared.auth.User
    created_by_id = Column(Integer, nullable=False, comment='创建者ID')
    manager_id = Column(Integer, comment='项目经理ID')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 关系
    # Note: These relationships will be defined after all models are created
    # tasks = relationship('Task', back_populates='project')
    # files = relationship('ProjectFile', back_populates='project')
    # members = relationship('ProjectMember', back_populates='project')
    # phases = relationship('ProjectPhase', back_populates='project')
    # issues = relationship('Issue', back_populates='project')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_no': self.project_no,
            'name': self.name,
            'description': self.description,
            'customer': self.customer_name or self.customer,  # 优先使用 CRM 同步的名称
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'order_no': self.order_no,
            'planned_start_date': self.planned_start_date.isoformat() if self.planned_start_date else None,
            'planned_end_date': self.planned_end_date.isoformat() if self.planned_end_date else None,
            'actual_start_date': self.actual_start_date.isoformat() if self.actual_start_date else None,
            'actual_end_date': self.actual_end_date.isoformat() if self.actual_end_date else None,
            'status': self.status.value if isinstance(self.status, ProjectStatus) else self.status,
            'priority': self.priority.value if isinstance(self.priority, ProjectPriority) else self.priority,
            'progress_percentage': self.progress_percentage,
            'created_by_id': self.created_by_id,
            'manager_id': self.manager_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Project {self.project_no}: {self.name}>"
