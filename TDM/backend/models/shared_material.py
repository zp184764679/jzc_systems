"""
共享材料库模型 - 连接报价系统的 materials 表
"""
from datetime import datetime
from . import db


class Material(db.Model):
    """材料库表 - 与报价系统共享"""
    __tablename__ = 'materials'

    id = db.Column(db.Integer, primary_key=True)
    material_code = db.Column(db.String(50), unique=True, index=True, nullable=False, comment='材料代码')
    material_name = db.Column(db.String(100), nullable=False, comment='材料名称')
    category = db.Column(db.String(50), index=True, comment='材料类别')

    # 物理属性
    density = db.Column(db.Numeric(10, 4), comment='密度 g/cm³')
    hardness = db.Column(db.String(50), comment='硬度')
    tensile_strength = db.Column(db.Numeric(10, 2), comment='抗拉强度 MPa')

    # 价格信息
    price_per_kg = db.Column(db.Numeric(10, 2), comment='价格/kg')
    price_currency = db.Column(db.String(10), default='CNY', comment='币种')

    # 供应商信息
    supplier = db.Column(db.String(200), comment='供应商')
    supplier_code = db.Column(db.String(100), comment='供应商料号')

    # 其他信息
    remark = db.Column(db.Text, comment='备注')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'material_code': self.material_code,
            'material_name': self.material_name,
            'category': self.category,
            'density': float(self.density) if self.density else None,
            'hardness': self.hardness,
            'tensile_strength': float(self.tensile_strength) if self.tensile_strength else None,
            'price_per_kg': float(self.price_per_kg) if self.price_per_kg else None,
            'price_currency': self.price_currency,
            'supplier': self.supplier,
            'supplier_code': self.supplier_code,
            'remark': self.remark,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Material {self.material_code}: {self.material_name}>'
