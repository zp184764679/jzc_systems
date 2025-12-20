"""
ProcessDocument 工艺文件模型
"""
from datetime import datetime
from . import db


class ProcessDocument(db.Model):
    """工艺文件表"""
    __tablename__ = 'tdm_process_documents'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    product_id = db.Column(db.BigInteger, db.ForeignKey('tdm_product_master.id'), nullable=False, index=True)
    part_number = db.Column(db.String(100), nullable=False, index=True, comment='品番号(冗余)')

    # 工艺信息
    process_code = db.Column(db.String(50), index=True, comment='工艺代码')
    process_name = db.Column(db.String(100), comment='工艺名称')
    process_category = db.Column(db.String(50), comment='工艺类别')
    process_sequence = db.Column(db.Integer, default=0, comment='工序顺序')

    # 关联报价系统工艺
    quotation_process_id = db.Column(db.Integer, comment='报价系统工艺ID')

    # 工艺参数
    setup_time = db.Column(db.Numeric(10, 4), comment='准备时间(分钟)')
    cycle_time = db.Column(db.Numeric(10, 4), comment='加工周期(分钟)')
    daily_output = db.Column(db.Integer, comment='日产量')
    defect_rate = db.Column(db.Numeric(5, 4), comment='不良率')

    # 设备要求
    machine_type = db.Column(db.String(100), comment='设备类型')
    machine_model = db.Column(db.String(100), comment='设备型号')
    machine_specs = db.Column(db.Text, comment='设备规格要求')

    # 工艺参数详情 (JSON)
    parameters = db.Column(db.JSON, comment='工艺参数')
    """
    格式:
    {
        "cutting_speed": 120,        // 切削速度 m/min
        "feed_rate": 0.15,           // 进给量 mm/r
        "depth_of_cut": 2.0,         // 切削深度 mm
        "spindle_speed": 1500,       // 主轴转速 rpm
        "coolant": "水溶性切削液",    // 冷却液
        "tool_type": "硬质合金刀具", // 刀具类型
        "tool_life": 500,            // 刀具寿命(件)
        "tool_cost": 150             // 刀具成本(元)
    }
    """

    # 作业标准
    work_instruction = db.Column(db.Text, comment='作业指导')
    safety_notes = db.Column(db.Text, comment='安全注意事项')
    quality_points = db.Column(db.Text, comment='质量要点')

    # 文件关联 (通过 FileIndex)
    file_index_ids = db.Column(db.JSON, comment='关联的FileIndex ID列表')

    # 版本控制
    version = db.Column(db.String(20), default='1.0', nullable=False, comment='版本号')
    is_current = db.Column(db.Boolean, default=True, index=True, comment='是否当前版本')
    parent_version_id = db.Column(db.BigInteger, comment='上一版本ID')
    version_note = db.Column(db.Text, comment='版本说明')

    # 审计字段
    created_by = db.Column(db.Integer, comment='创建人ID')
    created_by_name = db.Column(db.String(100), comment='创建人姓名')
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'part_number': self.part_number,
            'process_code': self.process_code,
            'process_name': self.process_name,
            'process_category': self.process_category,
            'process_sequence': self.process_sequence,
            'quotation_process_id': self.quotation_process_id,
            'setup_time': float(self.setup_time) if self.setup_time else None,
            'cycle_time': float(self.cycle_time) if self.cycle_time else None,
            'daily_output': self.daily_output,
            'defect_rate': float(self.defect_rate) if self.defect_rate else None,
            'machine_type': self.machine_type,
            'machine_model': self.machine_model,
            'machine_specs': self.machine_specs,
            'parameters': self.parameters or {},
            'work_instruction': self.work_instruction,
            'safety_notes': self.safety_notes,
            'quality_points': self.quality_points,
            'file_index_ids': self.file_index_ids or [],
            'version': self.version,
            'is_current': self.is_current,
            'parent_version_id': self.parent_version_id,
            'version_note': self.version_note,
            'created_by': self.created_by,
            'created_by_name': self.created_by_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<ProcessDocument {self.process_code}: {self.process_name}>'
