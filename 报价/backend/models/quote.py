# models/quote.py
"""
报价模型 - 基于创怡兴报价公式
"""
from sqlalchemy import Column, Integer, String, DECIMAL, Float, Text, DateTime, JSON, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Quote(Base):
    """报价单表 - 完整的制造成本计算"""
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)

    # 报价单信息
    quote_number = Column(String(100), unique=True, index=True, nullable=False, comment="报价单号")
    drawing_id = Column(Integer, ForeignKey("drawings.id"), comment="关联图纸ID")
    product_id = Column(Integer, ForeignKey("products.id"), comment="关联产品ID")
    customer_name = Column(String(200), index=True, comment="客户名称")
    product_name = Column(String(200), comment="产品名称")
    lot_size = Column(Integer, default=2000, comment="批量（LOT）")

    # ===== B. 材料费 =====
    material_name = Column(String(100), comment="材料名称")
    material_spec = Column(String(200), comment="材料规格")
    material_density = Column(Float, comment="材质比重（g/cm³）")
    outer_diameter = Column(Float, comment="外径（mm）")
    material_length = Column(Float, comment="材料长度（mm）")
    product_length = Column(Float, comment="产品长度（mm）")
    cut_width = Column(Float, default=2.5, comment="切口宽度（mm）")
    remaining_material = Column(Float, comment="残材长度（mm）")
    pieces_per_bar = Column(Integer, comment="取数（每根可切数量）")
    part_weight = Column(Float, comment="零件重量（g）")
    material_price_per_kg = Column(Float, comment="材料单价（元/kg）")
    total_defect_rate = Column(Float, default=0.0306, comment="总不良率")
    material_management_rate = Column(Float, default=1.03, comment="材管率")
    material_cost = Column(DECIMAL(12, 4), default=0, comment="B.材料费")

    # ===== C. 加工费 =====
    process_cost = Column(DECIMAL(12, 4), default=0, comment="C.加工费")

    # ===== D. 管理费 =====
    general_management_rate = Column(Float, default=0.10, comment="一般管理费率（默认10%）")
    transportation_cost = Column(DECIMAL(12, 4), default=0, comment="H.运送费")
    management_cost = Column(DECIMAL(12, 4), default=0, comment="D.管理费")

    # ===== F. 其他费用 =====
    packaging_material_cost = Column(DECIMAL(12, 4), default=0, comment="梱包材料费")
    consumables_cost = Column(DECIMAL(12, 4), default=0, comment="消耗品费用")
    other_cost = Column(DECIMAL(12, 4), default=0, comment="F.其他费用")

    # ===== 成本汇总 =====
    subtotal_cost = Column(DECIMAL(12, 4), default=0, comment="A.小计単価（B+C+D+F）")
    profit_rate = Column(Float, default=0.15, comment="利润率（默认15%）")
    profit_amount = Column(DECIMAL(12, 4), default=0, comment="M.利润（A×15%）")
    unit_price = Column(DECIMAL(12, 4), default=0, comment="N.零件単価总计（B+C+D+F+M）")
    total_amount = Column(DECIMAL(12, 2), default=0, comment="总价（单价×批量）")

    # 其他信息
    currency = Column(String(10), default="RMB", comment="币种：RMB/USD/HKD")
    exchange_rate = Column(DECIMAL(10, 4), default=1, comment="汇率")
    quantity = Column(Integer, default=1, comment="数量")
    lead_time = Column(Integer, comment="交货周期（天）")

    # 计算详情（JSON格式存储完整计算过程）
    calculation_details = Column(JSON, comment="详细计算过程")
    details = Column(JSON, comment="报价明细（兼容旧版）")

    # 状态管理
    status = Column(String(20), default="draft", comment="状态：draft, sent, approved, rejected")
    valid_until = Column(Date, comment="有效期至")

    # 备注
    notes = Column(Text, comment="备注")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, comment="创建人ID")

    # 关系
    product = relationship("Product", back_populates="quotes")
    processes = relationship("QuoteProcess", back_populates="quote", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Quote(number={self.quote_number}, unit_price={self.unit_price})>"


class QuoteItem(Base):
    """报价明细表"""
    __tablename__ = "quote_items"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False, comment="报价单ID")

    # 明细信息
    item_type = Column(String(50), comment="项目类型：material, process, other")
    item_name = Column(String(200), comment="项目名称")
    specification = Column(String(200), comment="规格")

    # 数量和单价
    quantity = Column(DECIMAL(12, 4), default=1, comment="数量")
    unit = Column(String(20), comment="单位")
    unit_price = Column(DECIMAL(12, 4), comment="单价")
    amount = Column(DECIMAL(12, 2), comment="金额")

    # 其他
    remark = Column(Text, comment="备注")
    sequence_number = Column(Integer, default=0, comment="序号")

    def __repr__(self):
        return f"<QuoteItem(name={self.item_name}, amount={self.amount})>"


class QuoteProcess(Base):
    """报价工序明细表 - 基于创怡兴工序计算"""
    __tablename__ = "quote_processes"

    id = Column(Integer, primary_key=True, index=True)

    # 关联信息
    quote_id = Column(Integer, ForeignKey('quotes.id'), nullable=False, index=True, comment="关联报价ID")

    # 工序基本信息
    process_name = Column(String(100), nullable=False, comment="工序名称：CNC车削/铣扁/电镀等")
    sequence = Column(Integer, comment="工序顺序")

    # 计算参数（基于创怡兴公式）
    defect_rate = Column(Float, default=0, comment="不良率（0-1之间的小数）")
    processing_quantity = Column(Float, comment="加工個数（LOT × (1 + 不良率)）")
    daily_production = Column(Float, comment="日産（件/天）")
    processing_days = Column(Float, comment="加工日数（加工個数 ÷ 日産）")
    setup_time = Column(Float, default=0, comment="段取時間（天）")
    engineering_cost_per_day = Column(Float, comment="工事費／日（元/天）")
    lot_size = Column(Integer, comment="LOT批量")

    # 特殊计费方式（电镀、包装等工序）
    unit_price = Column(Float, comment="单价（$/件）- 用于电镀等按件计费")
    box_processing_time = Column(Float, comment="箱处理时间（小时）- 用于包装工序")
    hourly_rate = Column(Float, comment="工事费/时（元/小时）- 用于按小时计费")
    box_quantity = Column(Integer, comment="箱入数 - 用于包装工序")

    # 计算结果
    process_cost = Column(DECIMAL(12, 4), default=0, comment="加工小費 = ((加工日数 + 段取时间) × 工事费/日) ÷ LOT")

    # 备注
    notes = Column(Text, comment="备注")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    quote = relationship("Quote", back_populates="processes")

    def __repr__(self):
        return f"<QuoteProcess(name={self.process_name}, cost={self.process_cost})>"


# 注意：ProcessRoute模型已迁移至 models/process_route.py
# 新模型支持模板化功能、多对象关联(Product/Drawing/Quote)和独立的工序步骤表(ProcessRouteStep)
