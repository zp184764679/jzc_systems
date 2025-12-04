# models/product.py
"""
产品模型 - 工程数据系统的核心模块
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, DECIMAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Product(Base):
    """产品表 - 存储产品主数据"""
    __tablename__ = "products"

    # 基础信息
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, index=True, nullable=False, comment="产品编码")
    name = Column(String(128), nullable=False, comment="产品名称")
    customer_part_number = Column(String(100), comment="客户料号")

    # 材质信息
    material = Column(String(100), comment="材质")
    material_spec = Column(String(200), comment="材质规格")
    density = Column(DECIMAL(10, 4), comment="密度 g/cm³")

    # 尺寸信息
    outer_diameter = Column(Float, comment="外径 mm")
    length = Column(Float, comment="长度 mm")
    width_or_od = Column(String(50), comment="宽度/外径")
    weight_kg = Column(Float, comment="重量 kg")

    # 结构信息
    subpart_count = Column(Integer, comment="子部数量")

    # 技术要求
    tolerance = Column(String(100), comment="公差等级")
    surface_roughness = Column(String(50), comment="表面粗糙度")
    heat_treatment = Column(String(200), comment="热处理要求")
    surface_treatment = Column(String(200), comment="表面处理要求")

    # 图纸信息
    customer_drawing_no = Column(String(100), comment="客户图号")
    drawing_id = Column(Integer, ForeignKey("drawings.id"), comment="关联图纸")
    version = Column(String(20), default="A.0", comment="版本号")

    # 其他
    description = Column(Text, comment="描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    drawing = relationship("Drawing", backref="products")
    quotes = relationship("Quote", back_populates="product")
    boms = relationship("BOM", back_populates="product")

    def __repr__(self):
        return f"<Product(code={self.code}, name={self.name})>"
