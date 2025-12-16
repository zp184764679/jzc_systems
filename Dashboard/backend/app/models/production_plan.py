from app import db
from datetime import date, datetime
from sqlalchemy import func


class ProductionPlan(db.Model):
    """生产计划表 - 连接订单和工序"""
    __tablename__ = 'dashboard_production_plans'

    id = db.Column(db.Integer, primary_key=True)

    # 关联
    order_id = db.Column(db.Integer, nullable=False, index=True)
    order_no = db.Column(db.String(50), index=True)
    customer_id = db.Column(db.Integer, index=True)
    customer_name = db.Column(db.String(200))

    # 计划信息
    plan_no = db.Column(db.String(50), unique=True, nullable=False)
    product_code = db.Column(db.String(100))
    product_name = db.Column(db.String(200))

    # 时间规划
    plan_start_date = db.Column(db.Date, nullable=False)
    plan_end_date = db.Column(db.Date, nullable=False)
    actual_start_date = db.Column(db.Date)
    actual_end_date = db.Column(db.Date)

    # 数量
    plan_quantity = db.Column(db.Integer, nullable=False, default=0)
    completed_quantity = db.Column(db.Integer, default=0)
    defect_quantity = db.Column(db.Integer, default=0)

    # 状态: pending, in_progress, completed, delayed, cancelled
    status = db.Column(db.String(20), default='pending', index=True)
    priority = db.Column(db.Integer, default=3)  # 1-5, 1 is highest

    # 负责人
    department = db.Column(db.String(64))
    responsible_person = db.Column(db.String(100))
    responsible_user_id = db.Column(db.Integer)

    # 备注
    remark = db.Column(db.Text)

    # 时间戳
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    # 关系
    steps = db.relationship('ProductionStep', backref='plan', cascade='all, delete-orphan', lazy='dynamic')

    @property
    def progress_percentage(self):
        """计算完成进度百分比"""
        if self.plan_quantity == 0:
            return 0
        return round((self.completed_quantity / self.plan_quantity) * 100, 2)

    @property
    def is_delayed(self):
        """判断是否延期"""
        if not self.plan_end_date or self.status == 'completed':
            return False
        return date.today() > self.plan_end_date

    @property
    def days_remaining(self):
        """剩余天数"""
        if not self.plan_end_date:
            return None
        delta = self.plan_end_date - date.today()
        return delta.days

    def to_timeline_item(self):
        """转换为时间轴项目格式"""
        return {
            'id': f'plan-{self.id}',
            'group': f'customer-{self.customer_id}' if self.customer_id else f'order-{self.order_id}',
            'title': f'{self.product_name or self.plan_no}',
            'start_time': int(datetime.combine(self.plan_start_date, datetime.min.time()).timestamp() * 1000) if self.plan_start_date else None,
            'end_time': int(datetime.combine(self.plan_end_date, datetime.min.time()).timestamp() * 1000) if self.plan_end_date else None,
            'type': 'production',
            'status': self.status,
            'progress': self.progress_percentage,
            'is_delayed': self.is_delayed,
            'days_remaining': self.days_remaining,
            'priority': self.priority,
            'metadata': {
                'plan_no': self.plan_no,
                'order_no': self.order_no,
                'product_name': self.product_name,
                'customer_name': self.customer_name,
                'quantity': self.plan_quantity,
                'completed': self.completed_quantity,
                'department': self.department,
                'responsible': self.responsible_person
            }
        }

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'order_no': self.order_no,
            'plan_no': self.plan_no,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'plan_start_date': self.plan_start_date.isoformat() if self.plan_start_date else None,
            'plan_end_date': self.plan_end_date.isoformat() if self.plan_end_date else None,
            'actual_start_date': self.actual_start_date.isoformat() if self.actual_start_date else None,
            'actual_end_date': self.actual_end_date.isoformat() if self.actual_end_date else None,
            'plan_quantity': self.plan_quantity,
            'completed_quantity': self.completed_quantity,
            'defect_quantity': self.defect_quantity,
            'status': self.status,
            'priority': self.priority,
            'progress_percentage': self.progress_percentage,
            'is_delayed': self.is_delayed,
            'days_remaining': self.days_remaining,
            'department': self.department,
            'responsible_person': self.responsible_person,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ProductionStep(db.Model):
    """生产工序步骤 - 时间轴子项"""
    __tablename__ = 'dashboard_production_steps'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('dashboard_production_plans.id'), nullable=False, index=True)

    # 工序信息
    step_name = db.Column(db.String(100), nullable=False)  # CNC车削、铣扁、电镀等
    step_code = db.Column(db.String(50))
    step_sequence = db.Column(db.Integer, nullable=False, default=1)

    # 时间
    plan_start = db.Column(db.DateTime, nullable=False)
    plan_end = db.Column(db.DateTime, nullable=False)
    actual_start = db.Column(db.DateTime)
    actual_end = db.Column(db.DateTime)

    # 设备和人员
    machine_id = db.Column(db.Integer)
    machine_name = db.Column(db.String(100))
    operator_id = db.Column(db.Integer)
    operator_name = db.Column(db.String(100))

    # 数量
    plan_quantity = db.Column(db.Integer, default=0)
    completed_quantity = db.Column(db.Integer, default=0)

    # 状态
    status = db.Column(db.String(20), default='pending', index=True)
    completion_rate = db.Column(db.Numeric(5, 2), default=0)  # 0-100

    # 质量
    defect_count = db.Column(db.Integer, default=0)
    defect_rate = db.Column(db.Numeric(5, 2), default=0)

    # 依赖关系
    depends_on_step_id = db.Column(db.Integer, db.ForeignKey('dashboard_production_steps.id'))

    # 备注
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    # 关系
    depends_on = db.relationship('ProductionStep', remote_side=[id], backref='dependents')

    @property
    def is_delayed(self):
        if not self.plan_end or self.status == 'completed':
            return False
        return datetime.now() > self.plan_end

    def to_timeline_item(self, group_prefix='plan'):
        """转换为时间轴项目格式"""
        return {
            'id': f'step-{self.id}',
            'group': f'{group_prefix}-{self.plan_id}',
            'title': self.step_name,
            'start_time': int(self.plan_start.timestamp() * 1000) if self.plan_start else None,
            'end_time': int(self.plan_end.timestamp() * 1000) if self.plan_end else None,
            'type': 'step',
            'status': self.status,
            'progress': float(self.completion_rate) if self.completion_rate else 0,
            'is_delayed': self.is_delayed,
            'sequence': self.step_sequence,
            'depends_on': f'step-{self.depends_on_step_id}' if self.depends_on_step_id else None,
            'metadata': {
                'step_name': self.step_name,
                'machine': self.machine_name,
                'operator': self.operator_name,
                'quantity': self.plan_quantity,
                'completed': self.completed_quantity,
                'defect_count': self.defect_count
            }
        }

    def to_dict(self):
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'step_name': self.step_name,
            'step_code': self.step_code,
            'step_sequence': self.step_sequence,
            'plan_start': self.plan_start.isoformat() if self.plan_start else None,
            'plan_end': self.plan_end.isoformat() if self.plan_end else None,
            'actual_start': self.actual_start.isoformat() if self.actual_start else None,
            'actual_end': self.actual_end.isoformat() if self.actual_end else None,
            'machine_name': self.machine_name,
            'operator_name': self.operator_name,
            'plan_quantity': self.plan_quantity,
            'completed_quantity': self.completed_quantity,
            'status': self.status,
            'completion_rate': float(self.completion_rate) if self.completion_rate else 0,
            'defect_count': self.defect_count,
            'defect_rate': float(self.defect_rate) if self.defect_rate else 0,
            'is_delayed': self.is_delayed,
            'depends_on_step_id': self.depends_on_step_id,
            'remark': self.remark
        }
