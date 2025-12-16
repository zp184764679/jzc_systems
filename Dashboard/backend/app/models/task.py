from app import db
from datetime import datetime
from sqlalchemy import func


class Task(db.Model):
    """待办事项表"""
    __tablename__ = 'dashboard_tasks'

    id = db.Column(db.Integer, primary_key=True)

    # 关联
    order_id = db.Column(db.Integer, index=True)
    order_no = db.Column(db.String(50))
    plan_id = db.Column(db.Integer, db.ForeignKey('dashboard_production_plans.id'), index=True)
    step_id = db.Column(db.Integer, db.ForeignKey('dashboard_production_steps.id'))

    # 任务信息
    task_no = db.Column(db.String(50), unique=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    task_type = db.Column(db.String(50), index=True)  # quote_review, production_start, quality_check, shipment, procurement

    # 时间
    due_date = db.Column(db.DateTime, nullable=False, index=True)
    remind_before_hours = db.Column(db.Integer, default=24)
    reminded_at = db.Column(db.DateTime)

    # 负责人
    assigned_to_user_id = db.Column(db.Integer, index=True)
    assigned_to_name = db.Column(db.String(100))
    assigned_to_dept = db.Column(db.String(64))

    # 创建者
    created_by_user_id = db.Column(db.Integer)
    created_by_name = db.Column(db.String(100))

    # 状态: pending, in_progress, completed, cancelled
    status = db.Column(db.String(20), default='pending', index=True)
    # 优先级: low, normal, high, urgent
    priority = db.Column(db.String(20), default='normal', index=True)

    # 时间戳
    created_at = db.Column(db.DateTime, default=func.now())
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    # 关系
    plan = db.relationship('ProductionPlan', backref='tasks')

    @property
    def is_overdue(self):
        """是否逾期"""
        if self.status in ['completed', 'cancelled']:
            return False
        return datetime.now() > self.due_date

    @property
    def hours_until_due(self):
        """距离截止还有多少小时"""
        if not self.due_date:
            return None
        delta = self.due_date - datetime.now()
        return delta.total_seconds() / 3600

    @property
    def should_remind(self):
        """是否应该发送提醒"""
        if self.status in ['completed', 'cancelled']:
            return False
        if self.reminded_at:
            return False
        hours = self.hours_until_due
        if hours is None:
            return False
        return hours <= self.remind_before_hours

    def to_timeline_item(self):
        """转换为时间轴项目（里程碑形式）"""
        return {
            'id': f'task-{self.id}',
            'group': f'dept-{self.assigned_to_dept}' if self.assigned_to_dept else 'unassigned',
            'title': self.title,
            'start_time': int(self.due_date.timestamp() * 1000) if self.due_date else None,
            'end_time': int(self.due_date.timestamp() * 1000) if self.due_date else None,  # 里程碑只有一个时间点
            'type': 'task',
            'status': self.status,
            'priority': self.priority,
            'is_overdue': self.is_overdue,
            'is_milestone': True,
            'metadata': {
                'task_no': self.task_no,
                'task_type': self.task_type,
                'description': self.description,
                'assigned_to': self.assigned_to_name,
                'department': self.assigned_to_dept,
                'order_no': self.order_no
            }
        }

    def to_dict(self):
        return {
            'id': self.id,
            'task_no': self.task_no,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type,
            'order_id': self.order_id,
            'order_no': self.order_no,
            'plan_id': self.plan_id,
            'step_id': self.step_id,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'remind_before_hours': self.remind_before_hours,
            'assigned_to_user_id': self.assigned_to_user_id,
            'assigned_to_name': self.assigned_to_name,
            'assigned_to_dept': self.assigned_to_dept,
            'created_by_name': self.created_by_name,
            'status': self.status,
            'priority': self.priority,
            'is_overdue': self.is_overdue,
            'hours_until_due': self.hours_until_due,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


# Priority mapping for sorting
PRIORITY_ORDER = {
    'urgent': 1,
    'high': 2,
    'normal': 3,
    'low': 4
}
