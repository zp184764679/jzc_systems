"""
共享图纸模型 - 连接报价系统的 drawings 表
"""
from datetime import datetime
from . import db


class Drawing(db.Model):
    """图纸表 - 与报价系统共享"""
    __tablename__ = 'drawings'

    id = db.Column(db.Integer, primary_key=True)

    # 基本信息
    drawing_number = db.Column(db.String(100), unique=True, index=True, nullable=False, comment='图号')
    customer_name = db.Column(db.String(200), index=True, comment='客户名称')
    product_name = db.Column(db.String(200), comment='产品名称')
    customer_part_number = db.Column(db.String(100), comment='客户料号')

    # 材质信息
    material = db.Column(db.String(100), comment='材质')
    material_spec = db.Column(db.String(200), comment='材质规格')

    # 尺寸信息
    outer_diameter = db.Column(db.String(50), comment='外径')
    length = db.Column(db.String(50), comment='长度')
    weight = db.Column(db.String(50), comment='重量')

    # 精度要求
    tolerance = db.Column(db.String(100), comment='公差等级')
    surface_roughness = db.Column(db.String(50), comment='表面粗糙度')

    # 技术要求
    heat_treatment = db.Column(db.String(200), comment='热处理要求')
    surface_treatment = db.Column(db.String(200), comment='表面处理要求')
    special_requirements = db.Column(db.Text, comment='特殊要求')

    # 文件信息
    file_path = db.Column(db.String(500), comment='文件路径')
    file_name = db.Column(db.String(200), comment='文件名')
    file_size = db.Column(db.Integer, comment='文件大小（字节）')
    file_type = db.Column(db.String(20), comment='文件类型')

    # OCR识别数据
    ocr_data = db.Column(db.JSON, comment='OCR识别的原始数据')
    ocr_confidence = db.Column(db.String(10), comment='OCR置信度')
    ocr_status = db.Column(db.String(20), default='pending', comment='OCR状态')

    # 其他信息
    notes = db.Column(db.Text, comment='备注')
    version = db.Column(db.String(20), default='A.0', comment='版本号')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer, comment='创建人ID')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'drawing_number': self.drawing_number,
            'customer_name': self.customer_name,
            'product_name': self.product_name,
            'customer_part_number': self.customer_part_number,
            'material': self.material,
            'material_spec': self.material_spec,
            'outer_diameter': self.outer_diameter,
            'length': self.length,
            'weight': self.weight,
            'tolerance': self.tolerance,
            'surface_roughness': self.surface_roughness,
            'heat_treatment': self.heat_treatment,
            'surface_treatment': self.surface_treatment,
            'special_requirements': self.special_requirements,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'ocr_data': self.ocr_data,
            'ocr_confidence': self.ocr_confidence,
            'ocr_status': self.ocr_status,
            'notes': self.notes,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }

    def __repr__(self):
        return f'<Drawing {self.drawing_number}: {self.customer_name}>'
