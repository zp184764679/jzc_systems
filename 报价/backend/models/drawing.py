# models/drawing.py
"""
图纸模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Drawing(Base):
    """图纸表"""
    __tablename__ = "drawings"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    drawing_number = Column(String(100), unique=True, index=True, nullable=False, comment="图号")
    customer_name = Column(String(200), index=True, comment="客户名称")
    product_name = Column(String(200), comment="产品名称")
    customer_part_number = Column(String(100), comment="客户料号")

    # 材质信息
    material = Column(String(100), comment="材质")
    material_spec = Column(String(200), comment="材质规格")

    # 尺寸信息（从OCR提取）
    outer_diameter = Column(String(50), comment="外径")
    length = Column(String(50), comment="长度")
    weight = Column(String(50), comment="重量")

    # 精度要求
    tolerance = Column(String(100), comment="公差等级")
    surface_roughness = Column(String(50), comment="表面粗糙度")

    # 技术要求
    heat_treatment = Column(String(200), comment="热处理要求")
    surface_treatment = Column(String(200), comment="表面处理要求")
    special_requirements = Column(Text, comment="特殊要求")

    # 文件信息
    file_path = Column(String(500), comment="文件路径")
    file_name = Column(String(200), comment="文件名")
    file_size = Column(Integer, comment="文件大小（字节）")
    file_type = Column(String(20), comment="文件类型")

    # OCR识别数据
    ocr_data = Column(JSON, comment="OCR识别的原始数据")
    ocr_confidence = Column(String(10), comment="OCR置信度")
    ocr_status = Column(String(20), default="pending", comment="OCR状态：pending, processing, completed, failed")

    # 其他信息
    notes = Column(Text, comment="备注")
    version = Column(String(20), default="A.0", comment="版本号")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, comment="创建人ID")

    # 关系
    corrections = relationship("OCRCorrection", back_populates="drawing", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Drawing(number={self.drawing_number}, customer={self.customer_name})>"
