# models/material.py
"""
材料库模型
"""
from sqlalchemy import Column, Integer, String, DECIMAL, Text, DateTime, Boolean
from sqlalchemy.sql import func
from config.database import Base


class Material(Base):
    """材料库表"""
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    material_code = Column(String(50), unique=True, index=True, nullable=False, comment="材料代码")
    material_name = Column(String(100), nullable=False, comment="材料名称")
    category = Column(String(50), index=True, comment="材料类别（不锈钢、铝合金等）")

    # 物理属性
    density = Column(DECIMAL(10, 4), comment="密度 g/cm³")
    hardness = Column(String(50), comment="硬度")
    tensile_strength = Column(DECIMAL(10, 2), comment="抗拉强度 MPa")

    # 价格信息
    price_per_kg = Column(DECIMAL(10, 2), comment="价格/kg")
    price_currency = Column(String(10), default="CNY", comment="币种")

    # 供应商信息
    supplier = Column(String(200), comment="供应商")
    supplier_code = Column(String(100), comment="供应商料号")

    # 其他信息
    remark = Column(Text, comment="备注")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Material(code={self.material_code}, name={self.material_name})>"
