"""
Issue Model - 问题/改善跟踪
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from models import Base


class IssueType(str, enum.Enum):
    """问题类型"""
    QUALITY_ISSUE = 'quality_issue'           # 质量问题
    DELAY = 'delay'                           # 延期
    COST_OVERRUN = 'cost_overrun'             # 成本超支
    REQUIREMENT_CHANGE = 'requirement_change'  # 需求变更
    RESOURCE_SHORTAGE = 'resource_shortage'   # 资源不足
    COMMUNICATION = 'communication'           # 沟通问题
    TECHNICAL = 'technical'                   # 技术问题
    OTHER = 'other'                           # 其他


class IssueSeverity(str, enum.Enum):
    """严重程度"""
    LOW = 'low'           # 低 - 轻微影响
    MEDIUM = 'medium'     # 中 - 中等影响
    HIGH = 'high'         # 高 - 严重影响
    CRITICAL = 'critical' # 紧急 - 阻塞项目


class IssueStatus(str, enum.Enum):
    """问题状态"""
    OPEN = 'open'             # 待处理
    IN_PROGRESS = 'in_progress'  # 处理中
    RESOLVED = 'resolved'     # 已解决
    CLOSED = 'closed'         # 已关闭
    REOPENED = 'reopened'     # 重新打开


class Issue(Base):
    """问题/改善模型"""
    __tablename__ = 'project_issues'

    id = Column(Integer, primary_key=True, index=True)

    # 关联项目
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)

    # 问题编号（自动生成）
    issue_no = Column(String(50), unique=True, nullable=False, index=True)

    # 基本信息
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # 分类和严重程度
    issue_type = Column(Enum(IssueType), default=IssueType.OTHER)
    severity = Column(Enum(IssueSeverity), default=IssueSeverity.MEDIUM)
    status = Column(Enum(IssueStatus), default=IssueStatus.OPEN, index=True)

    # 影响范围
    affected_phase_id = Column(Integer, ForeignKey('project_phases.id'), nullable=True)
    affected_task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True)

    # 人员
    reported_by_id = Column(Integer, nullable=False)  # 报告人
    reported_by_name = Column(String(100))
    assigned_to_id = Column(Integer, nullable=True)   # 负责人
    assigned_to_name = Column(String(100))

    # 改善措施
    root_cause = Column(Text)           # 根本原因分析
    corrective_action = Column(Text)    # 纠正措施
    preventive_action = Column(Text)    # 预防措施
    resolution_notes = Column(Text)     # 解决备注

    # 时间
    due_date = Column(DateTime, nullable=True)      # 期望解决日期
    resolved_at = Column(DateTime, nullable=True)   # 实际解决时间
    closed_at = Column(DateTime, nullable=True)     # 关闭时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    project = relationship('Project', backref='issues', foreign_keys=[project_id])
    affected_phase = relationship('ProjectPhase', backref='issues', foreign_keys=[affected_phase_id])
    affected_task = relationship('Task', backref='issues', foreign_keys=[affected_task_id])

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'issue_no': self.issue_no,
            'title': self.title,
            'description': self.description,
            'issue_type': self.issue_type.value if self.issue_type else None,
            'severity': self.severity.value if self.severity else None,
            'status': self.status.value if self.status else None,
            'affected_phase_id': self.affected_phase_id,
            'affected_task_id': self.affected_task_id,
            'reported_by_id': self.reported_by_id,
            'reported_by_name': self.reported_by_name,
            'assigned_to_id': self.assigned_to_id,
            'assigned_to_name': self.assigned_to_name,
            'root_cause': self.root_cause,
            'corrective_action': self.corrective_action,
            'preventive_action': self.preventive_action,
            'resolution_notes': self.resolution_notes,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def generate_issue_no(session):
        """生成问题编号 ISS-YYYYMMDD-XXX"""
        from datetime import datetime
        today = datetime.now().strftime('%Y%m%d')
        prefix = f'ISS-{today}-'

        # 获取今天最大的编号
        last_issue = session.query(Issue).filter(
            Issue.issue_no.like(f'{prefix}%')
        ).order_by(Issue.issue_no.desc()).first()

        if last_issue:
            last_num = int(last_issue.issue_no.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f'{prefix}{new_num:03d}'
