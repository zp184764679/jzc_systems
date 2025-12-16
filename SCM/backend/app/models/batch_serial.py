# -*- coding: utf-8 -*-
"""
批次和序列号管理模型
用于追踪物料的批次和序列号信息
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional
import enum

from sqlalchemy import Index, func
from sqlalchemy.dialects.mysql import JSON

from app import db


class BatchStatus(enum.Enum):
    """批次状态枚举"""
    ACTIVE = "active"           # 活跃/可用
    EXPIRED = "expired"         # 已过期
    QUARANTINE = "quarantine"   # 隔离/待检
    BLOCKED = "blocked"         # 冻结
    DEPLETED = "depleted"       # 已用尽


class QualityStatus(enum.Enum):
    """质量状态枚举"""
    PENDING = "pending"         # 待检
    PASSED = "passed"           # 合格
    FAILED = "failed"           # 不合格
    CONDITIONAL = "conditional" # 有条件放行


class SerialStatus(enum.Enum):
    """序列号状态枚举"""
    AVAILABLE = "available"     # 可用
    IN_STOCK = "in_stock"       # 在库
    SOLD = "sold"               # 已售出
    IN_USE = "in_use"           # 使用中
    RETURNED = "returned"       # 已退货
    SCRAPPED = "scrapped"       # 已报废
    LOST = "lost"               # 丢失


class BatchMaster(db.Model):
    """批次主数据"""
    __tablename__ = "scm_batch_master"

    id = db.Column(db.Integer, primary_key=True)

    # 批次编号
    batch_no = db.Column(db.String(64), nullable=False, index=True)

    # 关联物料
    material_id = db.Column(db.Integer, db.ForeignKey('scm_materials.id'), nullable=False, index=True)
    material_code = db.Column(db.String(64), index=True)
    material_name = db.Column(db.String(200))

    # 批次属性
    production_date = db.Column(db.Date)                              # 生产日期
    expiry_date = db.Column(db.Date)                                  # 有效期
    shelf_life_days = db.Column(db.Integer)                           # 保质期天数
    manufacturing_date = db.Column(db.Date)                           # 制造日期
    receipt_date = db.Column(db.Date, default=date.today)             # 入库日期

    # 来源信息
    supplier_id = db.Column(db.Integer)                               # 供应商ID
    supplier_name = db.Column(db.String(200))                         # 供应商名称
    supplier_batch_no = db.Column(db.String(64))                      # 供应商批次号
    manufacturer = db.Column(db.String(200))                          # 生产厂家
    origin_country = db.Column(db.String(64))                         # 原产国

    # 采购信息
    po_no = db.Column(db.String(64))                                  # 采购订单号
    po_line_no = db.Column(db.Integer)                                # 采购订单行号
    inbound_order_no = db.Column(db.String(64))                       # 入库单号

    # 数量
    initial_qty = db.Column(db.Numeric(14, 4), default=0)             # 初始数量
    current_qty = db.Column(db.Numeric(14, 4), default=0)             # 当前数量
    reserved_qty = db.Column(db.Numeric(14, 4), default=0)            # 预留数量
    uom = db.Column(db.String(32), default='pcs')                     # 计量单位

    # 质量信息
    quality_status = db.Column(db.String(32), default=QualityStatus.PENDING.value)
    inspection_date = db.Column(db.Date)                              # 检验日期
    inspection_no = db.Column(db.String(64))                          # 检验单号
    inspection_result = db.Column(db.Text)                            # 检验结果
    certificate_no = db.Column(db.String(100))                        # 合格证号
    certificate_url = db.Column(db.String(500))                       # 合格证文件

    # 状态
    status = db.Column(db.String(32), default=BatchStatus.ACTIVE.value, index=True)
    block_reason = db.Column(db.String(200))                          # 冻结原因

    # 附加信息
    lot_no = db.Column(db.String(64))                                 # 炉号/批号
    heat_no = db.Column(db.String(64))                                # 熔炼号
    customs_no = db.Column(db.String(64))                             # 报关单号
    attributes = db.Column(JSON, default=dict)                        # 扩展属性

    # 备注
    remark = db.Column(db.Text)

    # 审计字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer)
    created_by_name = db.Column(db.String(64))

    # 关系
    material = db.relationship('Material', backref='batches')
    serial_numbers = db.relationship('SerialNumber', backref='batch', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('material_id', 'batch_no', name='uq_material_batch'),
        Index("idx_batch_material", "material_id"),
        Index("idx_batch_supplier", "supplier_id"),
        Index("idx_batch_status", "status"),
        Index("idx_batch_expiry", "expiry_date"),
        Index("idx_batch_quality", "quality_status"),
    )

    def to_dict(self, include_material=False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "batch_no": self.batch_no,
            "material_id": self.material_id,
            "material_code": self.material_code,
            "material_name": self.material_name,
            "production_date": self.production_date.isoformat() if self.production_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "shelf_life_days": self.shelf_life_days,
            "manufacturing_date": self.manufacturing_date.isoformat() if self.manufacturing_date else None,
            "receipt_date": self.receipt_date.isoformat() if self.receipt_date else None,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "supplier_batch_no": self.supplier_batch_no,
            "manufacturer": self.manufacturer,
            "origin_country": self.origin_country,
            "po_no": self.po_no,
            "po_line_no": self.po_line_no,
            "inbound_order_no": self.inbound_order_no,
            "initial_qty": float(self.initial_qty or 0),
            "current_qty": float(self.current_qty or 0),
            "reserved_qty": float(self.reserved_qty or 0),
            "available_qty": float((self.current_qty or 0) - (self.reserved_qty or 0)),
            "uom": self.uom,
            "quality_status": self.quality_status,
            "quality_status_name": QUALITY_STATUS_MAP.get(self.quality_status, ""),
            "inspection_date": self.inspection_date.isoformat() if self.inspection_date else None,
            "inspection_no": self.inspection_no,
            "inspection_result": self.inspection_result,
            "certificate_no": self.certificate_no,
            "certificate_url": self.certificate_url,
            "status": self.status,
            "status_name": BATCH_STATUS_MAP.get(self.status, ""),
            "block_reason": self.block_reason,
            "lot_no": self.lot_no,
            "heat_no": self.heat_no,
            "customs_no": self.customs_no,
            "attributes": self.attributes or {},
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
            "is_expired": self.is_expired,
            "days_to_expiry": self.days_to_expiry,
        }

        if include_material and self.material:
            data["material"] = self.material.to_dict()

        return data

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date

    @property
    def days_to_expiry(self) -> Optional[int]:
        """距离过期天数（负数表示已过期）"""
        if not self.expiry_date:
            return None
        return (self.expiry_date - date.today()).days

    @classmethod
    def generate_batch_no(cls, material_code: str = None, prefix: str = None) -> str:
        """生成批次号: BAT-YYYYMMDD-XXXX 或 {前缀}-YYYYMMDD-XXXX"""
        today = datetime.now().strftime("%Y%m%d")

        if prefix:
            batch_prefix = f"{prefix}-{today}-"
        elif material_code:
            batch_prefix = f"{material_code[:8]}-{today}-"
        else:
            batch_prefix = f"BAT-{today}-"

        # 获取最大编号
        last = cls.query.filter(
            cls.batch_no.like(f"{batch_prefix}%")
        ).order_by(cls.batch_no.desc()).first()

        if last:
            try:
                last_num = int(last.batch_no.split("-")[-1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1

        return f"{batch_prefix}{new_num:04d}"

    def update_status(self):
        """根据条件自动更新状态"""
        if self.is_expired and self.status == BatchStatus.ACTIVE.value:
            self.status = BatchStatus.EXPIRED.value
        elif self.current_qty <= 0 and self.status == BatchStatus.ACTIVE.value:
            self.status = BatchStatus.DEPLETED.value


class SerialNumber(db.Model):
    """序列号主数据"""
    __tablename__ = "scm_serial_numbers"

    id = db.Column(db.Integer, primary_key=True)

    # 序列号
    serial_no = db.Column(db.String(100), nullable=False, index=True)

    # 关联物料
    material_id = db.Column(db.Integer, db.ForeignKey('scm_materials.id'), nullable=False, index=True)
    material_code = db.Column(db.String(64), index=True)
    material_name = db.Column(db.String(200))

    # 关联批次（可选）
    batch_id = db.Column(db.Integer, db.ForeignKey('scm_batch_master.id'), index=True)
    batch_no = db.Column(db.String(64))

    # 当前位置
    warehouse_id = db.Column(db.Integer, db.ForeignKey('scm_warehouses.id'), index=True)
    warehouse_name = db.Column(db.String(100))
    bin_id = db.Column(db.Integer, db.ForeignKey('scm_storage_bins.id'))
    bin_code = db.Column(db.String(64))

    # 来源信息
    supplier_id = db.Column(db.Integer)
    supplier_name = db.Column(db.String(200))
    supplier_serial_no = db.Column(db.String(100))                    # 供应商序列号
    manufacturer = db.Column(db.String(200))
    manufacturer_serial_no = db.Column(db.String(100))                # 厂商序列号

    # 采购信息
    po_no = db.Column(db.String(64))
    inbound_order_no = db.Column(db.String(64))
    receipt_date = db.Column(db.Date, default=date.today)

    # 销售/出库信息
    customer_id = db.Column(db.Integer)
    customer_name = db.Column(db.String(200))
    sales_order_no = db.Column(db.String(64))
    shipment_no = db.Column(db.String(64))
    shipment_date = db.Column(db.Date)

    # 质量信息
    quality_status = db.Column(db.String(32), default=QualityStatus.PENDING.value)
    inspection_date = db.Column(db.Date)
    inspection_no = db.Column(db.String(64))

    # 保修信息
    warranty_start_date = db.Column(db.Date)
    warranty_end_date = db.Column(db.Date)
    warranty_months = db.Column(db.Integer)

    # 状态
    status = db.Column(db.String(32), default=SerialStatus.AVAILABLE.value, index=True)
    status_changed_at = db.Column(db.DateTime)
    status_changed_by = db.Column(db.Integer)

    # 附加信息
    attributes = db.Column(JSON, default=dict)                        # 扩展属性
    remark = db.Column(db.Text)

    # 审计字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer)
    created_by_name = db.Column(db.String(64))

    # 关系
    material = db.relationship('Material', backref='serial_numbers')
    warehouse = db.relationship('Warehouse', backref='serial_numbers')
    bin = db.relationship('StorageBin', backref='serial_numbers')

    __table_args__ = (
        db.UniqueConstraint('material_id', 'serial_no', name='uq_material_serial'),
        Index("idx_serial_material", "material_id"),
        Index("idx_serial_batch", "batch_id"),
        Index("idx_serial_warehouse", "warehouse_id"),
        Index("idx_serial_status", "status"),
        Index("idx_serial_customer", "customer_id"),
    )

    def to_dict(self, include_material=False, include_batch=False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "serial_no": self.serial_no,
            "material_id": self.material_id,
            "material_code": self.material_code,
            "material_name": self.material_name,
            "batch_id": self.batch_id,
            "batch_no": self.batch_no,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse_name,
            "bin_id": self.bin_id,
            "bin_code": self.bin_code,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "supplier_serial_no": self.supplier_serial_no,
            "manufacturer": self.manufacturer,
            "manufacturer_serial_no": self.manufacturer_serial_no,
            "po_no": self.po_no,
            "inbound_order_no": self.inbound_order_no,
            "receipt_date": self.receipt_date.isoformat() if self.receipt_date else None,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "sales_order_no": self.sales_order_no,
            "shipment_no": self.shipment_no,
            "shipment_date": self.shipment_date.isoformat() if self.shipment_date else None,
            "quality_status": self.quality_status,
            "quality_status_name": QUALITY_STATUS_MAP.get(self.quality_status, ""),
            "inspection_date": self.inspection_date.isoformat() if self.inspection_date else None,
            "inspection_no": self.inspection_no,
            "warranty_start_date": self.warranty_start_date.isoformat() if self.warranty_start_date else None,
            "warranty_end_date": self.warranty_end_date.isoformat() if self.warranty_end_date else None,
            "warranty_months": self.warranty_months,
            "is_in_warranty": self.is_in_warranty,
            "status": self.status,
            "status_name": SERIAL_STATUS_MAP.get(self.status, ""),
            "status_changed_at": self.status_changed_at.isoformat() if self.status_changed_at else None,
            "status_changed_by": self.status_changed_by,
            "attributes": self.attributes or {},
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
        }

        if include_material and self.material:
            data["material"] = self.material.to_dict()

        if include_batch and self.batch:
            data["batch"] = self.batch.to_dict()

        return data

    @property
    def is_in_warranty(self) -> bool:
        """是否在保修期内"""
        if not self.warranty_end_date:
            return False
        return date.today() <= self.warranty_end_date

    def update_status(self, new_status: str, user_id: int = None):
        """更新状态"""
        self.status = new_status
        self.status_changed_at = datetime.utcnow()
        self.status_changed_by = user_id


class BatchTransaction(db.Model):
    """批次交易记录（追踪批次的进出）"""
    __tablename__ = "scm_batch_transactions"

    id = db.Column(db.Integer, primary_key=True)

    # 批次
    batch_id = db.Column(db.Integer, db.ForeignKey('scm_batch_master.id'), nullable=False, index=True)
    batch_no = db.Column(db.String(64), index=True)

    # 物料
    material_id = db.Column(db.Integer, db.ForeignKey('scm_materials.id'), nullable=False, index=True)
    material_code = db.Column(db.String(64))
    material_name = db.Column(db.String(200))

    # 交易类型
    transaction_type = db.Column(db.String(32), nullable=False, index=True)  # in/out/adjust/transfer
    transaction_subtype = db.Column(db.String(32))                           # 子类型: purchase/production/sales/...

    # 仓库和库位
    warehouse_id = db.Column(db.Integer, db.ForeignKey('scm_warehouses.id'), index=True)
    warehouse_name = db.Column(db.String(100))
    bin_id = db.Column(db.Integer)
    bin_code = db.Column(db.String(64))

    # 数量
    quantity = db.Column(db.Numeric(14, 4), nullable=False)           # 交易数量（正/负）
    before_qty = db.Column(db.Numeric(14, 4))                         # 交易前数量
    after_qty = db.Column(db.Numeric(14, 4))                          # 交易后数量
    uom = db.Column(db.String(32))

    # 关联单据
    reference_type = db.Column(db.String(32))                         # 单据类型
    reference_no = db.Column(db.String(64), index=True)               # 单据号
    reference_line = db.Column(db.Integer)                            # 单据行号

    # 客户/供应商
    partner_type = db.Column(db.String(16))                           # customer/supplier
    partner_id = db.Column(db.Integer)
    partner_name = db.Column(db.String(200))

    # 备注
    remark = db.Column(db.Text)

    # 审计字段
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_by = db.Column(db.Integer)
    created_by_name = db.Column(db.String(64))

    # 关系
    batch = db.relationship('BatchMaster', backref='transactions')
    material = db.relationship('Material')
    warehouse = db.relationship('Warehouse')

    __table_args__ = (
        Index("idx_batch_tx_batch", "batch_id"),
        Index("idx_batch_tx_material", "material_id"),
        Index("idx_batch_tx_date", "transaction_date"),
        Index("idx_batch_tx_ref", "reference_type", "reference_no"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "batch_no": self.batch_no,
            "material_id": self.material_id,
            "material_code": self.material_code,
            "material_name": self.material_name,
            "transaction_type": self.transaction_type,
            "transaction_type_name": BATCH_TX_TYPE_MAP.get(self.transaction_type, ""),
            "transaction_subtype": self.transaction_subtype,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse_name,
            "bin_id": self.bin_id,
            "bin_code": self.bin_code,
            "quantity": float(self.quantity or 0),
            "before_qty": float(self.before_qty or 0),
            "after_qty": float(self.after_qty or 0),
            "uom": self.uom,
            "reference_type": self.reference_type,
            "reference_no": self.reference_no,
            "reference_line": self.reference_line,
            "partner_type": self.partner_type,
            "partner_id": self.partner_id,
            "partner_name": self.partner_name,
            "remark": self.remark,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
        }


class SerialTransaction(db.Model):
    """序列号交易记录（追踪序列号的流转）"""
    __tablename__ = "scm_serial_transactions"

    id = db.Column(db.Integer, primary_key=True)

    # 序列号
    serial_id = db.Column(db.Integer, db.ForeignKey('scm_serial_numbers.id'), nullable=False, index=True)
    serial_no = db.Column(db.String(100), index=True)

    # 物料
    material_id = db.Column(db.Integer, db.ForeignKey('scm_materials.id'), nullable=False, index=True)
    material_code = db.Column(db.String(64))
    material_name = db.Column(db.String(200))

    # 交易类型
    transaction_type = db.Column(db.String(32), nullable=False, index=True)  # receipt/issue/transfer/status_change
    transaction_subtype = db.Column(db.String(32))

    # 位置变化
    from_warehouse_id = db.Column(db.Integer)
    from_warehouse_name = db.Column(db.String(100))
    from_bin_id = db.Column(db.Integer)
    from_bin_code = db.Column(db.String(64))
    to_warehouse_id = db.Column(db.Integer)
    to_warehouse_name = db.Column(db.String(100))
    to_bin_id = db.Column(db.Integer)
    to_bin_code = db.Column(db.String(64))

    # 状态变化
    from_status = db.Column(db.String(32))
    to_status = db.Column(db.String(32))

    # 关联单据
    reference_type = db.Column(db.String(32))
    reference_no = db.Column(db.String(64), index=True)
    reference_line = db.Column(db.Integer)

    # 客户/供应商
    partner_type = db.Column(db.String(16))
    partner_id = db.Column(db.Integer)
    partner_name = db.Column(db.String(200))

    # 备注
    remark = db.Column(db.Text)

    # 审计字段
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_by = db.Column(db.Integer)
    created_by_name = db.Column(db.String(64))

    # 关系
    serial = db.relationship('SerialNumber', backref='transactions')
    material = db.relationship('Material')

    __table_args__ = (
        Index("idx_serial_tx_serial", "serial_id"),
        Index("idx_serial_tx_material", "material_id"),
        Index("idx_serial_tx_date", "transaction_date"),
        Index("idx_serial_tx_ref", "reference_type", "reference_no"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "serial_id": self.serial_id,
            "serial_no": self.serial_no,
            "material_id": self.material_id,
            "material_code": self.material_code,
            "material_name": self.material_name,
            "transaction_type": self.transaction_type,
            "transaction_type_name": SERIAL_TX_TYPE_MAP.get(self.transaction_type, ""),
            "transaction_subtype": self.transaction_subtype,
            "from_warehouse_id": self.from_warehouse_id,
            "from_warehouse_name": self.from_warehouse_name,
            "from_bin_id": self.from_bin_id,
            "from_bin_code": self.from_bin_code,
            "to_warehouse_id": self.to_warehouse_id,
            "to_warehouse_name": self.to_warehouse_name,
            "to_bin_id": self.to_bin_id,
            "to_bin_code": self.to_bin_code,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "reference_type": self.reference_type,
            "reference_no": self.reference_no,
            "reference_line": self.reference_line,
            "partner_type": self.partner_type,
            "partner_id": self.partner_id,
            "partner_name": self.partner_name,
            "remark": self.remark,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
        }


# 状态名称映射
BATCH_STATUS_MAP = {
    BatchStatus.ACTIVE.value: "活跃",
    BatchStatus.EXPIRED.value: "已过期",
    BatchStatus.QUARANTINE.value: "隔离",
    BatchStatus.BLOCKED.value: "冻结",
    BatchStatus.DEPLETED.value: "已用尽",
}

QUALITY_STATUS_MAP = {
    QualityStatus.PENDING.value: "待检",
    QualityStatus.PASSED.value: "合格",
    QualityStatus.FAILED.value: "不合格",
    QualityStatus.CONDITIONAL.value: "有条件放行",
}

SERIAL_STATUS_MAP = {
    SerialStatus.AVAILABLE.value: "可用",
    SerialStatus.IN_STOCK.value: "在库",
    SerialStatus.SOLD.value: "已售出",
    SerialStatus.IN_USE.value: "使用中",
    SerialStatus.RETURNED.value: "已退货",
    SerialStatus.SCRAPPED.value: "已报废",
    SerialStatus.LOST.value: "丢失",
}

BATCH_TX_TYPE_MAP = {
    "in": "入库",
    "out": "出库",
    "adjust": "调整",
    "transfer": "转移",
}

SERIAL_TX_TYPE_MAP = {
    "receipt": "入库",
    "issue": "出库",
    "transfer": "转移",
    "status_change": "状态变更",
}
