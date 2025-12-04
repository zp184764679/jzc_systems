# models/process_route.py
"""
工艺路线模型 - 整合PM系统的模板化功能
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class ProcessRoute(Base):
    """工艺路线表 - 支持模板化和多对象关联"""
    __tablename__ = "process_routes"

    # 基础信息
    id = Column(Integer, primary_key=True, index=True)
    route_code = Column(String(64), unique=True, index=True, nullable=False, comment="路线编码")
    name = Column(String(128), comment="路线名称")

    # 关联对象（支持三种关联方式）
    product_id = Column(Integer, ForeignKey("products.id"), comment="关联产品")
    drawing_id = Column(Integer, ForeignKey("drawings.id"), comment="关联图纸")
    quote_id = Column(Integer, ForeignKey("quotes.id"), comment="关联报价")

    # 模板功能（新增）
    is_template = Column(Boolean, default=False, index=True, comment="是否为模板")
    template_name = Column(String(128), comment="模板名称")
    template_category = Column(String(64), comment="模板分类")

    # 版本管理
    version = Column(String(32), default="1.0", comment="版本号")

    # 成本汇总（计算字段）
    total_cost = Column(DECIMAL(12, 4), default=0, comment="总成本")
    total_time = Column(Float, default=0, comment="总工时（分钟）")

    # 其他
    description = Column(Text, comment="说明")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, comment="创建人ID")

    # 关系
    product = relationship("Product", backref="process_routes")
    drawing = relationship("Drawing", backref="process_routes")
    quote = relationship("Quote", backref="process_routes")
    steps = relationship("ProcessRouteStep", back_populates="route", cascade="all, delete-orphan", order_by="ProcessRouteStep.sequence")

    def __repr__(self):
        return f"<ProcessRoute(code={self.route_code}, name={self.name}, is_template={self.is_template})>"


class ProcessRouteStep(Base):
    """工艺路线步骤表 - 工序明细"""
    __tablename__ = "process_route_steps"

    # 基础信息
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("process_routes.id"), nullable=False, index=True, comment="路线ID")
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False, comment="工艺ID")

    # 顺序
    sequence = Column(Integer, default=0, comment="工序顺序")

    # 部门和设备
    department = Column(String(64), comment="部门")
    machine = Column(String(128), comment="设备")
    machine_model = Column(String(128), comment="设备型号")

    # 工时预估
    estimate_minutes = Column(Integer, comment="预计工时（分钟）")
    setup_time = Column(Float, default=0, comment="段取时间（小时）")

    # 成本信息
    labor_cost = Column(DECIMAL(10, 4), default=0, comment="人工成本")
    machine_cost = Column(DECIMAL(10, 4), default=0, comment="机器成本")
    tool_cost = Column(DECIMAL(10, 4), default=0, comment="刀具成本")
    material_cost = Column(DECIMAL(10, 4), default=0, comment="辅料成本")
    other_cost = Column(DECIMAL(10, 4), default=0, comment="其他成本")
    total_cost = Column(DECIMAL(10, 4), default=0, comment="该工序总成本")

    # 生产参数
    daily_output = Column(Integer, comment="日产量（件/天）")
    defect_rate = Column(Float, default=0, comment="不良率")

    # 工艺参数（JSON格式存储详细参数）
    process_parameters = Column(Text, comment="工艺参数JSON")

    # 其他
    remarks = Column(Text, comment="备注")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    route = relationship("ProcessRoute", back_populates="steps")
    process = relationship("Process", backref="route_steps")

    def __repr__(self):
        return f"<ProcessRouteStep(route_id={self.route_id}, sequence={self.sequence}, process_id={self.process_id})>"
