# 质量检验模型
from database import db
from datetime import datetime


class QualityInspection(db.Model):
    """质量检验记录"""
    __tablename__ = 'mes_quality_inspections'

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('mes_work_orders.id'), nullable=False)
    production_record_id = db.Column(db.Integer, db.ForeignKey('mes_production_records.id'))

    # 检验类型
    inspection_type = db.Column(db.String(20), comment='检验类型: incoming/process/final')
    inspection_no = db.Column(db.String(50), comment='检验单号')

    # 检验结果
    sample_size = db.Column(db.Integer, comment='抽样数量')
    pass_quantity = db.Column(db.Integer, comment='合格数量')
    fail_quantity = db.Column(db.Integer, comment='不合格数量')
    result = db.Column(db.String(20), comment='检验结果: pass/fail/conditional')

    # 检验项目
    inspection_items = db.Column(db.JSON, comment='检验项目及结果')

    # 检验人
    inspector_id = db.Column(db.Integer, comment='检验员ID')
    inspector_name = db.Column(db.String(50), comment='检验员姓名')

    # 处理结果
    disposition = db.Column(db.String(100), comment='处置方式: accept/reject/rework/concession')

    # 备注
    notes = db.Column(db.Text, comment='备注')

    # 时间戳
    inspection_time = db.Column(db.DateTime, default=datetime.utcnow, comment='检验时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'work_order_id': self.work_order_id,
            'production_record_id': self.production_record_id,
            'inspection_type': self.inspection_type,
            'inspection_no': self.inspection_no,
            'sample_size': self.sample_size,
            'pass_quantity': self.pass_quantity,
            'fail_quantity': self.fail_quantity,
            'result': self.result,
            'inspection_items': self.inspection_items,
            'inspector_id': self.inspector_id,
            'inspector_name': self.inspector_name,
            'disposition': self.disposition,
            'notes': self.notes,
            'inspection_time': self.inspection_time.isoformat() if self.inspection_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
