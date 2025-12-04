# models/process.py
"""
工艺库模型
"""
from sqlalchemy import Column, Integer, String, DECIMAL, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Process(Base):
    """工艺库表"""
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True, index=True)
    process_code = Column(String(50), unique=True, index=True, nullable=False, comment="工艺代码")
    process_name = Column(String(100), nullable=False, comment="工艺名称")
    category = Column(String(50), index=True, comment="工艺类别（车、铣、磨等）")

    # 设备信息
    machine_type = Column(String(100), comment="设备类型")
    machine_model = Column(String(100), comment="设备型号")

    # 成本信息
    hourly_rate = Column(DECIMAL(10, 2), comment="工时费率 元/小时")
    setup_time = Column(DECIMAL(10, 4), default=0, comment="段取时间 天")
    daily_fee = Column(DECIMAL(10, 2), default=0, comment="工事费/日 元/天")

    # 生产效率
    daily_output = Column(Integer, default=1000, comment="日产量（件/天）")
    defect_rate = Column(DECIMAL(5, 4), default=0, comment="不良率 %")

    # UI展示
    icon = Column(String(10), comment="图标emoji")

    # 其他信息
    description = Column(Text, comment="工艺说明")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Process(code={self.process_code}, name={self.process_name})>"


class CuttingParameter(Base):
    """切削参数库"""
    __tablename__ = "cutting_parameters"

    id = Column(Integer, primary_key=True, index=True)

    # 材料和工艺组合
    material_category = Column(String(50), index=True, comment="材料类别")
    process_type = Column(String(50), index=True, comment="工艺类型")

    # 切削参数
    cutting_speed = Column(DECIMAL(10, 2), comment="切削速度 m/min")
    feed_rate = Column(DECIMAL(10, 4), comment="进给量 mm/r")
    depth_of_cut = Column(DECIMAL(10, 2), comment="切削深度 mm")
    spindle_speed = Column(Integer, comment="主轴转速 rpm")

    # 刀具信息
    tool_type = Column(String(100), comment="刀具类型")
    tool_life = Column(Integer, comment="刀具寿命 分钟")
    tool_cost = Column(DECIMAL(10, 2), comment="刀具成本")

    # 其他
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<CuttingParameter(material={self.material_category}, process={self.process_type})>"
