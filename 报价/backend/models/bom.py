# models/bom.py
"""
BOM（物料清单）模型 - Bill of Materials
支持层级式物料清单管理
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, DECIMAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class BOM(Base):
    """BOM主表 - 物料清单表头"""
    __tablename__ = "boms"

    # 基础信息
    id = Column(Integer, primary_key=True, index=True)
    bom_code = Column(String(64), unique=True, index=True, nullable=False, comment="BOM编码")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, comment="产品ID")
    version = Column(String(20), default="A.01", comment="版本/修订号")
    material_type = Column(String(20), default="成品", comment="物料类型：成品/半成品/原材料/标准件")
    unit = Column(String(20), default="套", comment="单位")

    # 生效管理
    effective_from = Column(Date, comment="生效日期")
    effective_to = Column(Date, comment="失效日期")

    # 责任人
    maker = Column(String(64), comment="制表人")
    approver = Column(String(64), comment="审核人")

    # 其他
    remark = Column(Text, comment="备注")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # 关系
    product = relationship("Product", back_populates="boms")
    items = relationship("BOMItem", back_populates="bom", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BOM(code={self.bom_code}, product_id={self.product_id}, version={self.version})>"


class BOMItem(Base):
    """BOM明细 - 物料清单行项目"""
    __tablename__ = "bom_items"

    # 基础信息
    id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(Integer, ForeignKey("boms.id"), nullable=False, comment="BOM ID")
    level = Column(String(20), comment="序号/层级：1, 1.1, 1.1.1")
    sequence = Column(Integer, comment="排序序号")

    # 零件信息
    part_no = Column(String(100), comment="零件编号（Part No.）")
    part_name = Column(String(200), comment="零件名称")
    spec = Column(String(200), comment="规格/型号")
    unit = Column(String(20), default="PCS", comment="单位")

    # 用量信息
    qty = Column(DECIMAL(12, 4), default=1, comment="用量/配比")
    loss_rate = Column(DECIMAL(5, 4), default=0, comment="损耗率 %")

    # 供应链信息
    alt_part = Column(String(100), comment="替代料/选用料")
    supplier = Column(String(200), comment="供应商")

    # 其他
    remark = Column(Text, comment="备注/工艺说明")
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    bom = relationship("BOM", back_populates="items")

    def __repr__(self):
        return f"<BOMItem(level={self.level}, part_no={self.part_no}, part_name={self.part_name})>"
