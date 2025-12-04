# models/process_cost.py
"""
工序成本配置模型
用于存储标准工序的成本配置数据
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from config.database import Base


class ProcessCost(Base):
    """工序成本配置表"""
    __tablename__ = "process_costs"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    process_name = Column(String(100), unique=True, nullable=False, index=True, comment="工序名称")
    process_code = Column(String(50), comment="工序代码")
    category = Column(String(50), comment="工序类别：加工/检查/表面处理/包装等")

    # 成本参数
    daily_production = Column(Float, comment="日产量（件/天）")
    engineering_cost_per_day = Column(Float, comment="工事费/日（元/天）")
    setup_time = Column(Float, default=0, comment="段取时间（天）")
    defect_rate = Column(Float, default=0, comment="不良率（0-1之间的小数）")

    # 特殊计费方式
    unit_price = Column(Float, comment="单价（用于按件计费的工序，如电镀）")
    hourly_rate = Column(Float, comment="小时费率（用于按时间计费的工序）")

    # 说明和备注
    description = Column(Text, comment="工序说明")
    formula_notes = Column(Text, comment="计算公式说明")
    is_active = Column(Integer, default=1, comment="是否启用：1启用 0禁用")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ProcessCost(name={self.process_name}, category={self.category})>"
