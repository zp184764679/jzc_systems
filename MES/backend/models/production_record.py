# 生产记录/报工模型
from database import db
from datetime import datetime


class ProductionRecord(db.Model):
    """生产记录 - 报工数据"""
    __tablename__ = 'mes_production_records'

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('mes_work_orders.id'), nullable=False)

    # 工序信息
    process_step = db.Column(db.Integer, comment='工序步骤')
    process_name = db.Column(db.String(100), comment='工序名称')

    # 生产数据
    quantity = db.Column(db.Integer, nullable=False, comment='生产数量')
    good_quantity = db.Column(db.Integer, default=0, comment='合格数量')
    defect_quantity = db.Column(db.Integer, default=0, comment='不良数量')

    # 设备信息（来自EAM）
    equipment_id = db.Column(db.Integer, comment='设备ID')
    equipment_code = db.Column(db.String(50), comment='设备编码')
    equipment_name = db.Column(db.String(100), comment='设备名称')

    # 物料消耗（来自SCM）
    material_batch = db.Column(db.String(100), comment='物料批次')

    # 操作员信息
    operator_id = db.Column(db.Integer, comment='操作员ID')
    operator_name = db.Column(db.String(50), comment='操作员姓名')

    # 时间记录
    start_time = db.Column(db.DateTime, comment='开始时间')
    end_time = db.Column(db.DateTime, comment='结束时间')
    work_hours = db.Column(db.Float, comment='工时（小时）')

    # 备注
    notes = db.Column(db.Text, comment='备注')
    defect_reason = db.Column(db.String(500), comment='不良原因')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'work_order_id': self.work_order_id,
            'process_step': self.process_step,
            'process_name': self.process_name,
            'quantity': self.quantity,
            'good_quantity': self.good_quantity,
            'defect_quantity': self.defect_quantity,
            'equipment_id': self.equipment_id,
            'equipment_code': self.equipment_code,
            'equipment_name': self.equipment_name,
            'material_batch': self.material_batch,
            'operator_id': self.operator_id,
            'operator_name': self.operator_name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'work_hours': self.work_hours,
            'notes': self.notes,
            'defect_reason': self.defect_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
