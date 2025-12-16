# SCM 库存转移模型
# Transfer Order & Transfer Order Item
import enum
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy import Index
from app import db


class TransferStatus(enum.Enum):
    """转移单状态"""
    DRAFT = "draft"              # 草稿
    PENDING = "pending"          # 待执行
    IN_PROGRESS = "in_progress"  # 执行中（部分转移）
    COMPLETED = "completed"      # 已完成
    CANCELLED = "cancelled"      # 已取消


class TransferType(enum.Enum):
    """转移类型"""
    WAREHOUSE = "warehouse"      # 仓库间转移
    BIN = "bin"                  # 库位间转移
    CROSS = "cross"              # 跨仓库库位转移


# 状态名称映射
TRANSFER_STATUS_MAP = {
    TransferStatus.DRAFT.value: "草稿",
    TransferStatus.PENDING.value: "待执行",
    TransferStatus.IN_PROGRESS.value: "执行中",
    TransferStatus.COMPLETED.value: "已完成",
    TransferStatus.CANCELLED.value: "已取消",
}

TRANSFER_TYPE_MAP = {
    TransferType.WAREHOUSE.value: "仓库间转移",
    TransferType.BIN.value: "库位间转移",
    TransferType.CROSS.value: "跨仓库转移",
}


class TransferOrder(db.Model):
    """库存转移单"""
    __tablename__ = "scm_transfer_orders"

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # 转移类型和状态
    transfer_type = db.Column(
        db.Enum(TransferType),
        default=TransferType.WAREHOUSE,
        nullable=False
    )
    status = db.Column(
        db.Enum(TransferStatus),
        default=TransferStatus.DRAFT,
        nullable=False,
        index=True
    )

    # 源仓库/库位
    source_warehouse_id = db.Column(db.Integer, db.ForeignKey('scm_warehouses.id'), nullable=False)
    source_warehouse_name = db.Column(db.String(100))
    source_bin_id = db.Column(db.Integer, db.ForeignKey('scm_storage_bins.id'))
    source_bin_code = db.Column(db.String(50))

    # 目标仓库/库位
    target_warehouse_id = db.Column(db.Integer, db.ForeignKey('scm_warehouses.id'), nullable=False)
    target_warehouse_name = db.Column(db.String(100))
    target_bin_id = db.Column(db.Integer, db.ForeignKey('scm_storage_bins.id'))
    target_bin_code = db.Column(db.String(50))

    # 计划/实际日期
    planned_date = db.Column(db.Date)                   # 计划转移日期
    actual_date = db.Column(db.Date)                    # 实际转移日期

    # 数量统计
    total_planned_qty = db.Column(db.Numeric(14, 4), default=0)  # 计划总数量
    total_transferred_qty = db.Column(db.Numeric(14, 4), default=0)  # 已转移总数量

    # 原因/备注
    reason = db.Column(db.String(200))                  # 转移原因
    remark = db.Column(db.Text)                         # 备注

    # 操作人员
    created_by = db.Column(db.Integer)                  # 创建人ID
    created_by_name = db.Column(db.String(50))          # 创建人姓名
    submitted_by = db.Column(db.Integer)                # 提交人ID
    submitted_by_name = db.Column(db.String(50))        # 提交人姓名
    submitted_at = db.Column(db.DateTime)               # 提交时间
    executed_by = db.Column(db.Integer)                 # 执行人ID
    executed_by_name = db.Column(db.String(50))         # 执行人姓名
    completed_at = db.Column(db.DateTime)               # 完成时间

    # 审计字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    source_warehouse = db.relationship(
        'Warehouse',
        foreign_keys=[source_warehouse_id],
        backref='transfer_orders_from'
    )
    target_warehouse = db.relationship(
        'Warehouse',
        foreign_keys=[target_warehouse_id],
        backref='transfer_orders_to'
    )
    source_bin = db.relationship(
        'StorageBin',
        foreign_keys=[source_bin_id],
        backref='transfer_orders_from'
    )
    target_bin = db.relationship(
        'StorageBin',
        foreign_keys=[target_bin_id],
        backref='transfer_orders_to'
    )
    items = db.relationship(
        'TransferOrderItem',
        backref='order',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        Index("idx_transfer_status", "status"),
        Index("idx_transfer_source", "source_warehouse_id"),
        Index("idx_transfer_target", "target_warehouse_id"),
        Index("idx_transfer_date", "planned_date"),
    )

    def to_dict(self, include_items: bool = False) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "order_no": self.order_no,
            "transfer_type": self.transfer_type.value if self.transfer_type else None,
            "transfer_type_name": TRANSFER_TYPE_MAP.get(self.transfer_type.value) if self.transfer_type else None,
            "status": self.status.value if self.status else None,
            "status_name": TRANSFER_STATUS_MAP.get(self.status.value) if self.status else None,
            "source_warehouse_id": self.source_warehouse_id,
            "source_warehouse_name": self.source_warehouse_name,
            "source_bin_id": self.source_bin_id,
            "source_bin_code": self.source_bin_code,
            "target_warehouse_id": self.target_warehouse_id,
            "target_warehouse_name": self.target_warehouse_name,
            "target_bin_id": self.target_bin_id,
            "target_bin_code": self.target_bin_code,
            "planned_date": self.planned_date.isoformat() if self.planned_date else None,
            "actual_date": self.actual_date.isoformat() if self.actual_date else None,
            "total_planned_qty": float(self.total_planned_qty or 0),
            "total_transferred_qty": float(self.total_transferred_qty or 0),
            "reason": self.reason,
            "remark": self.remark,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
            "submitted_by": self.submitted_by,
            "submitted_by_name": self.submitted_by_name,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "executed_by": self.executed_by,
            "executed_by_name": self.executed_by_name,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_items:
            result["items"] = [item.to_dict() for item in self.items]

        return result

    def update_totals(self):
        """更新数量统计"""
        items = self.items.all()
        self.total_planned_qty = sum(i.planned_qty or Decimal('0') for i in items)
        self.total_transferred_qty = sum(i.transferred_qty or Decimal('0') for i in items)

    def check_completion(self):
        """检查是否全部完成"""
        items = self.items.all()
        all_completed = all(
            (i.transferred_qty or 0) >= (i.planned_qty or 0)
            for i in items
        )
        if all_completed and items:
            self.status = TransferStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            return True
        elif any((i.transferred_qty or 0) > 0 for i in items):
            self.status = TransferStatus.IN_PROGRESS
        return False


class TransferOrderItem(db.Model):
    """库存转移单明细"""
    __tablename__ = "scm_transfer_order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('scm_transfer_orders.id'), nullable=False, index=True)
    line_no = db.Column(db.Integer, default=1)          # 行号

    # 物料信息
    material_id = db.Column(db.Integer, db.ForeignKey('scm_materials.id'), nullable=False)
    material_code = db.Column(db.String(64))            # 物料编码
    material_name = db.Column(db.String(200))           # 物料名称
    specification = db.Column(db.String(200))           # 规格

    # 数量
    planned_qty = db.Column(db.Numeric(14, 4), default=0)      # 计划数量
    transferred_qty = db.Column(db.Numeric(14, 4), default=0)  # 已转移数量
    uom = db.Column(db.String(20), default='pcs')              # 单位

    # 批次信息（可选）
    batch_no = db.Column(db.String(64))                 # 批次号
    serial_no = db.Column(db.String(64))                # 序列号

    # 源/目标库位（可单独指定，覆盖主表）
    source_bin_id = db.Column(db.Integer, db.ForeignKey('scm_storage_bins.id'))
    source_bin_code = db.Column(db.String(50))
    target_bin_id = db.Column(db.Integer, db.ForeignKey('scm_storage_bins.id'))
    target_bin_code = db.Column(db.String(50))

    # 状态
    item_status = db.Column(db.String(20), default='pending')  # pending/partial/completed

    # 转移时间
    transferred_at = db.Column(db.DateTime)             # 转移时间
    transferred_by = db.Column(db.Integer)              # 转移人ID
    transferred_by_name = db.Column(db.String(50))      # 转移人姓名

    # 备注
    remark = db.Column(db.String(500))

    # 审计字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    material = db.relationship('Material', backref='transfer_items')
    source_bin_item = db.relationship(
        'StorageBin',
        foreign_keys=[source_bin_id],
        backref='transfer_items_from'
    )
    target_bin_item = db.relationship(
        'StorageBin',
        foreign_keys=[target_bin_id],
        backref='transfer_items_to'
    )

    __table_args__ = (
        Index("idx_transfer_item_order", "order_id"),
        Index("idx_transfer_item_material", "material_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "line_no": self.line_no,
            "material_id": self.material_id,
            "material_code": self.material_code,
            "material_name": self.material_name,
            "specification": self.specification,
            "planned_qty": float(self.planned_qty or 0),
            "transferred_qty": float(self.transferred_qty or 0),
            "uom": self.uom,
            "batch_no": self.batch_no,
            "serial_no": self.serial_no,
            "source_bin_id": self.source_bin_id,
            "source_bin_code": self.source_bin_code,
            "target_bin_id": self.target_bin_id,
            "target_bin_code": self.target_bin_code,
            "item_status": self.item_status,
            "transferred_at": self.transferred_at.isoformat() if self.transferred_at else None,
            "transferred_by": self.transferred_by,
            "transferred_by_name": self.transferred_by_name,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_status(self):
        """更新明细状态"""
        planned = float(self.planned_qty or 0)
        transferred = float(self.transferred_qty or 0)

        if transferred >= planned and planned > 0:
            self.item_status = 'completed'
        elif transferred > 0:
            self.item_status = 'partial'
        else:
            self.item_status = 'pending'


class TransferLog(db.Model):
    """转移执行日志"""
    __tablename__ = "scm_transfer_logs"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('scm_transfer_orders.id'), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey('scm_transfer_order_items.id'), nullable=False)

    # 物料信息
    material_code = db.Column(db.String(64))
    material_name = db.Column(db.String(200))

    # 转移数量
    transfer_qty = db.Column(db.Numeric(14, 4), nullable=False)
    uom = db.Column(db.String(20))

    # 批次
    batch_no = db.Column(db.String(64))

    # 源/目标
    source_warehouse_name = db.Column(db.String(100))
    source_bin_code = db.Column(db.String(50))
    target_warehouse_name = db.Column(db.String(100))
    target_bin_code = db.Column(db.String(50))

    # 执行信息
    executed_by = db.Column(db.Integer)
    executed_by_name = db.Column(db.String(50))
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联库存流水
    inventory_tx_out_id = db.Column(db.Integer)         # 出库流水ID
    inventory_tx_in_id = db.Column(db.Integer)          # 入库流水ID

    # 备注
    remark = db.Column(db.String(500))

    # 关系
    transfer_order = db.relationship('TransferOrder', backref='logs')
    transfer_item = db.relationship('TransferOrderItem', backref='logs')

    __table_args__ = (
        Index("idx_transfer_log_order", "order_id"),
        Index("idx_transfer_log_item", "item_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "item_id": self.item_id,
            "material_code": self.material_code,
            "material_name": self.material_name,
            "transfer_qty": float(self.transfer_qty or 0),
            "uom": self.uom,
            "batch_no": self.batch_no,
            "source_warehouse_name": self.source_warehouse_name,
            "source_bin_code": self.source_bin_code,
            "target_warehouse_name": self.target_warehouse_name,
            "target_bin_code": self.target_bin_code,
            "executed_by": self.executed_by,
            "executed_by_name": self.executed_by_name,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "inventory_tx_out_id": self.inventory_tx_out_id,
            "inventory_tx_in_id": self.inventory_tx_in_id,
            "remark": self.remark,
        }
