"""
TechnicalSpec 技术规格模型
"""
from datetime import datetime
from . import db


class TechnicalSpec(db.Model):
    """技术规格表"""
    __tablename__ = 'tdm_technical_specs'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    product_id = db.Column(db.BigInteger, db.ForeignKey('tdm_product_master.id'), nullable=False, index=True)
    part_number = db.Column(db.String(100), nullable=False, index=True, comment='品番号(冗余)')

    # 材料信息
    material_code = db.Column(db.String(50), comment='材料代码')
    material_name = db.Column(db.String(100), comment='材料名称')
    material_spec = db.Column(db.String(200), comment='材料规格')
    density = db.Column(db.Numeric(10, 4), comment='密度 g/cm3')
    hardness = db.Column(db.String(50), comment='硬度')
    tensile_strength = db.Column(db.Numeric(10, 2), comment='抗拉强度 MPa')

    # 尺寸信息
    outer_diameter = db.Column(db.Numeric(10, 4), comment='外径 mm')
    inner_diameter = db.Column(db.Numeric(10, 4), comment='内径 mm')
    length = db.Column(db.Numeric(10, 4), comment='长度 mm')
    width = db.Column(db.Numeric(10, 4), comment='宽度 mm')
    height = db.Column(db.Numeric(10, 4), comment='高度 mm')
    weight = db.Column(db.Numeric(10, 4), comment='重量 kg')
    volume = db.Column(db.Numeric(10, 4), comment='体积 cm3')

    # 精度要求
    tolerance_class = db.Column(db.String(50), comment='公差等级')
    surface_roughness = db.Column(db.String(50), comment='表面粗糙度 Ra')
    geometric_tolerance = db.Column(db.JSON, comment='几何公差 JSON')
    position_tolerance = db.Column(db.String(100), comment='位置公差')
    form_tolerance = db.Column(db.String(100), comment='形状公差')

    # 热处理
    heat_treatment = db.Column(db.String(200), comment='热处理要求')
    hardness_spec = db.Column(db.String(100), comment='硬度要求')
    heat_treatment_temp = db.Column(db.String(100), comment='热处理温度')

    # 表面处理
    surface_treatment = db.Column(db.String(200), comment='表面处理')
    coating_spec = db.Column(db.String(200), comment='涂层规格')
    coating_thickness = db.Column(db.String(100), comment='涂层厚度')
    color = db.Column(db.String(50), comment='颜色')

    # 特殊要求
    special_requirements = db.Column(db.Text, comment='特殊要求')
    quality_requirements = db.Column(db.Text, comment='质量要求')
    packaging_requirements = db.Column(db.Text, comment='包装要求')

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
            # 材料信息
            'material_code': self.material_code,
            'material_name': self.material_name,
            'material_spec': self.material_spec,
            'density': float(self.density) if self.density else None,
            'hardness': self.hardness,
            'tensile_strength': float(self.tensile_strength) if self.tensile_strength else None,
            # 尺寸信息
            'outer_diameter': float(self.outer_diameter) if self.outer_diameter else None,
            'inner_diameter': float(self.inner_diameter) if self.inner_diameter else None,
            'length': float(self.length) if self.length else None,
            'width': float(self.width) if self.width else None,
            'height': float(self.height) if self.height else None,
            'weight': float(self.weight) if self.weight else None,
            'volume': float(self.volume) if self.volume else None,
            # 精度要求
            'tolerance_class': self.tolerance_class,
            'surface_roughness': self.surface_roughness,
            'geometric_tolerance': self.geometric_tolerance,
            'position_tolerance': self.position_tolerance,
            'form_tolerance': self.form_tolerance,
            # 热处理
            'heat_treatment': self.heat_treatment,
            'hardness_spec': self.hardness_spec,
            'heat_treatment_temp': self.heat_treatment_temp,
            # 表面处理
            'surface_treatment': self.surface_treatment,
            'coating_spec': self.coating_spec,
            'coating_thickness': self.coating_thickness,
            'color': self.color,
            # 特殊要求
            'special_requirements': self.special_requirements,
            'quality_requirements': self.quality_requirements,
            'packaging_requirements': self.packaging_requirements,
            # 版本控制
            'version': self.version,
            'is_current': self.is_current,
            'parent_version_id': self.parent_version_id,
            'version_note': self.version_note,
            # 审计
            'created_by': self.created_by,
            'created_by_name': self.created_by_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<TechnicalSpec {self.part_number} v{self.version}>'
