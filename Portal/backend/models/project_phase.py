"""
ProjectPhase Model - 项目阶段模型
按业务流程：客户订单 → 报价 → 采购 → 生产 → 质检 → 出货 → 签收
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from models import Base
import enum


class PhaseType(str, enum.Enum):
    """阶段类型枚举 - 按业务流程顺序"""
    CUSTOMER_ORDER = 'customer_order'   # 客户订单
    QUOTATION = 'quotation'             # 报价
    PROCUREMENT = 'procurement'         # 采购
    PRODUCTION = 'production'           # 生产
    QC = 'qc'                           # 质检
    SHIPPING = 'shipping'               # 出货
    RECEIPT = 'receipt'                 # 签收


class PhaseStatus(str, enum.Enum):
    """阶段状态枚举"""
    PENDING = 'pending'             # 待开始
    IN_PROGRESS = 'in_progress'     # 进行中
    COMPLETED = 'completed'         # 已完成
    BLOCKED = 'blocked'             # 受阻


class ProjectPhase(Base):
    """项目阶段表"""
    __tablename__ = 'project_phases'

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 关联项目
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True, comment='所属项目ID')

    # 阶段信息
    phase_type = Column(
        Enum(PhaseType),
        nullable=False,
        comment='阶段类型'
    )
    phase_order = Column(Integer, nullable=False, comment='阶段顺序(1-7)')
    name = Column(String(100), nullable=False, comment='阶段名称')
    description = Column(Text, comment='阶段描述')

    # 时间字段
    planned_start_date = Column(Date, comment='计划开始日期')
    planned_end_date = Column(Date, comment='计划结束日期')
    actual_start_date = Column(Date, comment='实际开始日期')
    actual_end_date = Column(Date, comment='实际结束日期')

    # 状态和完成度
    status = Column(
        Enum(PhaseStatus),
        default=PhaseStatus.PENDING,
        nullable=False,
        comment='阶段状态'
    )
    completion_percentage = Column(Integer, default=0, comment='完成百分比(0-100)')

    # 负责人和部门
    responsible_user_id = Column(Integer, comment='负责人ID')
    department = Column(String(100), comment='负责部门')

    # 依赖关系
    depends_on_phase_id = Column(Integer, ForeignKey('project_phases.id'), comment='依赖的前置阶段ID')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 关系
    # project = relationship('Project', back_populates='phases')
    # depends_on = relationship('ProjectPhase', remote_side=[id], foreign_keys=[depends_on_phase_id])

    @staticmethod
    def get_default_phases():
        """获取默认的7个阶段配置"""
        return [
            {
                'phase_type': PhaseType.CUSTOMER_ORDER,
                'phase_order': 1,
                'name': '客户订单',
                'description': '接收并确认客户订单'
            },
            {
                'phase_type': PhaseType.QUOTATION,
                'phase_order': 2,
                'name': '报价',
                'description': '提供产品报价和成本估算'
            },
            {
                'phase_type': PhaseType.PROCUREMENT,
                'phase_order': 3,
                'name': '采购',
                'description': '采购所需原材料和物料'
            },
            {
                'phase_type': PhaseType.PRODUCTION,
                'phase_order': 4,
                'name': '生产',
                'description': '生产制造产品'
            },
            {
                'phase_type': PhaseType.QC,
                'phase_order': 5,
                'name': '质检',
                'description': '质量检验和测试'
            },
            {
                'phase_type': PhaseType.SHIPPING,
                'phase_order': 6,
                'name': '出货',
                'description': '包装并发货'
            },
            {
                'phase_type': PhaseType.RECEIPT,
                'phase_order': 7,
                'name': '签收',
                'description': '客户签收确认'
            },
        ]

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'phase_type': self.phase_type.value if isinstance(self.phase_type, PhaseType) else self.phase_type,
            'phase_order': self.phase_order,
            'name': self.name,
            'description': self.description,
            'planned_start_date': self.planned_start_date.isoformat() if self.planned_start_date else None,
            'planned_end_date': self.planned_end_date.isoformat() if self.planned_end_date else None,
            'actual_start_date': self.actual_start_date.isoformat() if self.actual_start_date else None,
            'actual_end_date': self.actual_end_date.isoformat() if self.actual_end_date else None,
            'status': self.status.value if isinstance(self.status, PhaseStatus) else self.status,
            'completion_percentage': self.completion_percentage,
            'responsible_user_id': self.responsible_user_id,
            'department': self.department,
            'depends_on_phase_id': self.depends_on_phase_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<ProjectPhase {self.name} (Order {self.phase_order})>"
