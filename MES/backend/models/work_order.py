# 工单模型
from database import db
from datetime import datetime


class WorkOrder(db.Model):
    """工单 - 生产任务单"""
    __tablename__ = 'mes_work_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False, comment='工单编号')

    # 产品信息（来自PDM）
    product_id = db.Column(db.Integer, comment='产品ID（PDM）')
    product_code = db.Column(db.String(100), comment='产品编码')
    product_name = db.Column(db.String(200), comment='产品名称')

    # 生产计划
    planned_quantity = db.Column(db.Integer, nullable=False, comment='计划数量')
    completed_quantity = db.Column(db.Integer, default=0, comment='完成数量')
    defect_quantity = db.Column(db.Integer, default=0, comment='不良数量')

    # 时间安排
    planned_start = db.Column(db.DateTime, comment='计划开始时间')
    planned_end = db.Column(db.DateTime, comment='计划结束时间')
    actual_start = db.Column(db.DateTime, comment='实际开始时间')
    actual_end = db.Column(db.DateTime, comment='实际结束时间')

    # 状态
    status = db.Column(db.String(20), default='pending', comment='状态: pending/in_progress/completed/cancelled')
    priority = db.Column(db.Integer, default=3, comment='优先级: 1-最高, 5-最低')

    # 来源信息
    source_type = db.Column(db.String(20), comment='来源类型: pm/crm/manual')
    source_id = db.Column(db.Integer, comment='来源ID（项目ID/订单ID）')

    # 工艺路线（来自PDM）
    process_route_id = db.Column(db.Integer, comment='工艺路线ID')
    current_step = db.Column(db.Integer, default=0, comment='当前工序步骤')

    # 备注
    notes = db.Column(db.Text, comment='备注')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(50), comment='创建人')

    def to_dict(self):
        return {
            'id': self.id,
            'order_no': self.order_no,
            'product_id': self.product_id,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'planned_quantity': self.planned_quantity,
            'completed_quantity': self.completed_quantity,
            'defect_quantity': self.defect_quantity,
            'planned_start': self.planned_start.isoformat() if self.planned_start else None,
            'planned_end': self.planned_end.isoformat() if self.planned_end else None,
            'actual_start': self.actual_start.isoformat() if self.actual_start else None,
            'actual_end': self.actual_end.isoformat() if self.actual_end else None,
            'status': self.status,
            'priority': self.priority,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'current_step': self.current_step,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'completion_rate': round(self.completed_quantity / self.planned_quantity * 100, 2) if self.planned_quantity > 0 else 0,
            'defect_rate': round(self.defect_quantity / (self.completed_quantity + self.defect_quantity) * 100, 2) if (self.completed_quantity + self.defect_quantity) > 0 else 0
        }
