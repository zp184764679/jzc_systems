# -*- coding: utf-8 -*-
# app/models/capacity.py
"""
设备产能配置模型
- CapacityConfig: 设备产能配置
- CapacityAdjustment: 产能调整记录
- CapacityLog: 产能日志（实际产出记录）
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Optional, Dict, Any
from enum import Enum
from .. import db


class ShiftType(str, Enum):
    """班次类型"""
    DAY = 'day'           # 白班
    NIGHT = 'night'       # 夜班
    ALL = 'all'           # 全天


class AdjustmentType(str, Enum):
    """调整类型"""
    TEMPORARY = 'temporary'     # 临时调整
    SEASONAL = 'seasonal'       # 季节性调整
    MAINTENANCE = 'maintenance' # 维护调整
    UPGRADE = 'upgrade'         # 设备升级
    OTHER = 'other'             # 其他


class CapacityStatus(str, Enum):
    """配置状态"""
    DRAFT = 'draft'           # 草稿
    ACTIVE = 'active'         # 生效中
    INACTIVE = 'inactive'     # 已停用


SHIFT_TYPE_LABELS = {
    ShiftType.DAY.value: '白班',
    ShiftType.NIGHT.value: '夜班',
    ShiftType.ALL.value: '全天',
}

ADJUSTMENT_TYPE_LABELS = {
    AdjustmentType.TEMPORARY.value: '临时调整',
    AdjustmentType.SEASONAL.value: '季节性调整',
    AdjustmentType.MAINTENANCE.value: '维护调整',
    AdjustmentType.UPGRADE.value: '设备升级',
    AdjustmentType.OTHER.value: '其他',
}

CAPACITY_STATUS_LABELS = {
    CapacityStatus.DRAFT.value: '草稿',
    CapacityStatus.ACTIVE.value: '生效中',
    CapacityStatus.INACTIVE.value: '已停用',
}


def generate_config_code() -> str:
    """生成配置编码 CAP-YYYYMMDD-XXX"""
    from datetime import datetime
    today = datetime.now().strftime('%Y%m%d')
    prefix = f"CAP-{today}-"
    last = CapacityConfig.query.filter(
        CapacityConfig.config_code.like(f"{prefix}%")
    ).order_by(CapacityConfig.config_code.desc()).first()
    if last:
        try:
            seq = int(last.config_code.split('-')[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def generate_adjustment_code() -> str:
    """生成调整编码 ADJ-YYYYMMDD-XXX"""
    from datetime import datetime
    today = datetime.now().strftime('%Y%m%d')
    prefix = f"ADJ-{today}-"
    last = CapacityAdjustment.query.filter(
        CapacityAdjustment.adjustment_code.like(f"{prefix}%")
    ).order_by(CapacityAdjustment.adjustment_code.desc()).first()
    if last:
        try:
            seq = int(last.adjustment_code.split('-')[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


class CapacityConfig(db.Model):
    """设备产能配置"""
    __tablename__ = "capacity_configs"
    __table_args__ = (
        db.UniqueConstraint("config_code", name="uq_capacity_configs_code"),
        {"extend_existing": True},
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    config_code = db.Column(db.String(50), nullable=False, unique=True)  # 配置编码

    # 关联设备
    machine_id = db.Column(db.Integer, nullable=False)    # 设备ID
    machine_code = db.Column(db.String(64))               # 设备编码
    machine_name = db.Column(db.String(128))              # 设备名称

    # 产能配置
    shift_type = db.Column(db.String(20), default=ShiftType.ALL.value)  # 班次类型
    standard_capacity = db.Column(db.Integer, default=0)   # 标准产能（件/班次）
    max_capacity = db.Column(db.Integer, default=0)        # 最大产能
    min_capacity = db.Column(db.Integer, default=0)        # 最小产能

    # 工时配置
    working_hours = db.Column(db.Float, default=8.0)       # 班次工作小时数
    setup_time = db.Column(db.Float, default=0)            # 换线时间（分钟）
    cycle_time = db.Column(db.Float, default=0)            # 节拍时间（秒/件）

    # 产品类型（可选）
    product_type = db.Column(db.String(100))              # 产品类型
    product_code = db.Column(db.String(50))               # 产品编码

    # 有效期
    effective_from = db.Column(db.Date)                    # 生效日期
    effective_to = db.Column(db.Date)                      # 失效日期

    # 状态
    status = db.Column(db.String(20), default=CapacityStatus.DRAFT.value)
    is_default = db.Column(db.Boolean, default=False)     # 是否默认配置

    # 备注
    remarks = db.Column(db.Text)

    # 审计
    created_by = db.Column(db.BigInteger)
    created_by_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "config_code": self.config_code,
            "machine_id": self.machine_id,
            "machine_code": self.machine_code,
            "machine_name": self.machine_name,
            "shift_type": self.shift_type,
            "shift_type_label": SHIFT_TYPE_LABELS.get(self.shift_type, self.shift_type),
            "standard_capacity": self.standard_capacity,
            "max_capacity": self.max_capacity,
            "min_capacity": self.min_capacity,
            "working_hours": self.working_hours,
            "setup_time": self.setup_time,
            "cycle_time": self.cycle_time,
            "product_type": self.product_type,
            "product_code": self.product_code,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "status": self.status,
            "status_label": CAPACITY_STATUS_LABELS.get(self.status, self.status),
            "is_default": self.is_default,
            "remarks": self.remarks,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CapacityAdjustment(db.Model):
    """产能调整记录"""
    __tablename__ = "capacity_adjustments"
    __table_args__ = (
        db.UniqueConstraint("adjustment_code", name="uq_capacity_adjustments_code"),
        {"extend_existing": True},
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    adjustment_code = db.Column(db.String(50), nullable=False, unique=True)  # 调整编码

    # 关联设备
    machine_id = db.Column(db.Integer, nullable=False)
    machine_code = db.Column(db.String(64))
    machine_name = db.Column(db.String(128))

    # 关联配置
    config_id = db.Column(db.BigInteger)                  # 关联产能配置ID

    # 调整信息
    adjustment_type = db.Column(db.String(30), default=AdjustmentType.TEMPORARY.value)
    reason = db.Column(db.Text)                           # 调整原因

    # 调整前后
    original_capacity = db.Column(db.Integer)             # 原产能
    adjusted_capacity = db.Column(db.Integer)             # 调整后产能
    adjustment_rate = db.Column(db.Float)                 # 调整比例（%）

    # 有效期
    effective_from = db.Column(db.Date, nullable=False)   # 开始日期
    effective_to = db.Column(db.Date)                     # 结束日期（可为空，表示永久）

    # 状态
    is_active = db.Column(db.Boolean, default=True)

    # 审计
    created_by = db.Column(db.BigInteger)
    created_by_name = db.Column(db.String(100))
    approved_by = db.Column(db.BigInteger)
    approved_by_name = db.Column(db.String(100))
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "adjustment_code": self.adjustment_code,
            "machine_id": self.machine_id,
            "machine_code": self.machine_code,
            "machine_name": self.machine_name,
            "config_id": self.config_id,
            "adjustment_type": self.adjustment_type,
            "adjustment_type_label": ADJUSTMENT_TYPE_LABELS.get(self.adjustment_type, self.adjustment_type),
            "reason": self.reason,
            "original_capacity": self.original_capacity,
            "adjusted_capacity": self.adjusted_capacity,
            "adjustment_rate": self.adjustment_rate,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
            "approved_by": self.approved_by,
            "approved_by_name": self.approved_by_name,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CapacityLog(db.Model):
    """产能日志（每日实际产出记录）"""
    __tablename__ = "capacity_logs"
    __table_args__ = (
        db.UniqueConstraint("machine_id", "log_date", "shift_type", name="uq_capacity_logs_machine_date_shift"),
        {"extend_existing": True},
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    # 关联设备
    machine_id = db.Column(db.Integer, nullable=False)
    machine_code = db.Column(db.String(64))
    machine_name = db.Column(db.String(128))

    # 日期和班次
    log_date = db.Column(db.Date, nullable=False)
    shift_type = db.Column(db.String(20), default=ShiftType.ALL.value)

    # 产能数据
    planned_capacity = db.Column(db.Integer, default=0)   # 计划产能
    actual_output = db.Column(db.Integer, default=0)      # 实际产出
    defective_count = db.Column(db.Integer, default=0)    # 不良数量
    good_count = db.Column(db.Integer, default=0)         # 良品数量

    # 效率指标
    utilization_rate = db.Column(db.Float)                # 稼动率（实际/计划）
    yield_rate = db.Column(db.Float)                      # 良品率（良品/实际）
    oee = db.Column(db.Float)                             # OEE（综合设备效率）

    # 停机信息
    downtime_minutes = db.Column(db.Integer, default=0)   # 停机时间（分钟）
    downtime_reason = db.Column(db.String(200))           # 停机原因

    # 备注
    remarks = db.Column(db.Text)

    # 审计
    recorded_by = db.Column(db.BigInteger)
    recorded_by_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_rates(self):
        """计算效率指标"""
        if self.planned_capacity and self.planned_capacity > 0:
            self.utilization_rate = round(self.actual_output / self.planned_capacity * 100, 2)
        else:
            self.utilization_rate = 0

        if self.actual_output and self.actual_output > 0:
            self.good_count = self.actual_output - (self.defective_count or 0)
            self.yield_rate = round(self.good_count / self.actual_output * 100, 2)
        else:
            self.yield_rate = 0
            self.good_count = 0

        # OEE = 稼动率 × 良品率 / 100 （简化计算）
        if self.utilization_rate and self.yield_rate:
            self.oee = round(self.utilization_rate * self.yield_rate / 100, 2)
        else:
            self.oee = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "machine_id": self.machine_id,
            "machine_code": self.machine_code,
            "machine_name": self.machine_name,
            "log_date": self.log_date.isoformat() if self.log_date else None,
            "shift_type": self.shift_type,
            "shift_type_label": SHIFT_TYPE_LABELS.get(self.shift_type, self.shift_type),
            "planned_capacity": self.planned_capacity,
            "actual_output": self.actual_output,
            "defective_count": self.defective_count,
            "good_count": self.good_count,
            "utilization_rate": self.utilization_rate,
            "yield_rate": self.yield_rate,
            "oee": self.oee,
            "downtime_minutes": self.downtime_minutes,
            "downtime_reason": self.downtime_reason,
            "remarks": self.remarks,
            "recorded_by": self.recorded_by,
            "recorded_by_name": self.recorded_by_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
