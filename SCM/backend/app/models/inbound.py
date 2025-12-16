# backend/app/models/inbound.py
"""
入库单模型
- 支持多种来源：采购入库、生产入库、调拨入库、退货入库等
- 支持批次/序列号管理
- 自动更新库存汇总表
"""
from __future__ import annotations
import enum
from datetime import datetime
from decimal import Decimal
from app import db


class InboundStatus(enum.Enum):
    """入库单状态"""
    DRAFT = "draft"           # 草稿
    PENDING = "pending"       # 待入库
    PARTIAL = "partial"       # 部分入库
    COMPLETED = "completed"   # 已完成
    CANCELLED = "cancelled"   # 已取消


class InboundType(enum.Enum):
    """入库类型"""
    PURCHASE = "purchase"     # 采购入库
    PRODUCTION = "production" # 生产入库
    TRANSFER = "transfer"     # 调拨入库
    RETURN = "return"         # 退货入库
    OTHER = "other"           # 其他入库


INBOUND_STATUS_MAP = {
    "draft": "草稿",
    "pending": "待入库",
    "partial": "部分入库",
    "completed": "已完成",
    "cancelled": "已取消",
}

INBOUND_TYPE_MAP = {
    "purchase": "采购入库",
    "production": "生产入库",
    "transfer": "调拨入库",
    "return": "退货入库",
    "other": "其他入库",
}


class InboundOrder(db.Model):
    """入库单"""
    __tablename__ = "scm_inbound_orders"
    __table_args__ = (
        db.Index('idx_inbound_order_no', 'order_no'),
        db.Index('idx_inbound_status', 'status'),
        db.Index('idx_inbound_type', 'inbound_type'),
        db.Index('idx_inbound_warehouse', 'warehouse_id'),
        db.Index('idx_inbound_source_no', 'source_no'),
        db.Index('idx_inbound_created_at', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False, comment="入库单号")

    # 入库类型和状态
    inbound_type = db.Column(db.Enum(InboundType), nullable=False, default=InboundType.PURCHASE, comment="入库类型")
    status = db.Column(db.Enum(InboundStatus), nullable=False, default=InboundStatus.DRAFT, comment="状态")

    # 来源信息
    source_no = db.Column(db.String(100), comment="来源单号（PO号/生产单号等）")
    source_system = db.Column(db.String(50), comment="来源系统（采购/MES等）")
    supplier_id = db.Column(db.Integer, comment="供应商ID")
    supplier_name = db.Column(db.String(200), comment="供应商名称")

    # 目标仓库
    warehouse_id = db.Column(db.Integer, db.ForeignKey('scm_warehouses.id'), nullable=False, comment="目标仓库")
    warehouse_name = db.Column(db.String(100), comment="仓库名称")

    # 计划信息
    planned_date = db.Column(db.Date, comment="计划入库日期")
    actual_date = db.Column(db.Date, comment="实际入库日期")

    # 数量汇总
    total_planned_qty = db.Column(db.Numeric(18, 4), default=0, comment="计划总数量")
    total_received_qty = db.Column(db.Numeric(18, 4), default=0, comment="实收总数量")

    # 质检信息
    is_inspected = db.Column(db.Boolean, default=False, comment="是否已质检")
    inspection_result = db.Column(db.String(20), comment="质检结果")  # passed/failed/partial
    inspection_date = db.Column(db.DateTime, comment="质检日期")
    inspector_id = db.Column(db.Integer, comment="质检员ID")
    inspector_name = db.Column(db.String(50), comment="质检员姓名")

    # 备注和附件
    remark = db.Column(db.Text, comment="备注")
    attachments = db.Column(db.JSON, comment="附件列表")

    # 操作人信息
    created_by = db.Column(db.Integer, comment="创建人ID")
    created_by_name = db.Column(db.String(50), comment="创建人姓名")
    received_by = db.Column(db.Integer, comment="收货人ID")
    received_by_name = db.Column(db.String(50), comment="收货人姓名")

    # 时间戳
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    warehouse = db.relationship('Warehouse', backref='inbound_orders')
    items = db.relationship('InboundOrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_items=False):
        data = {
            "id": self.id,
            "order_no": self.order_no,
            "inbound_type": self.inbound_type.value if self.inbound_type else None,
            "inbound_type_text": INBOUND_TYPE_MAP.get(self.inbound_type.value) if self.inbound_type else None,
            "status": self.status.value if self.status else None,
            "status_text": INBOUND_STATUS_MAP.get(self.status.value) if self.status else None,
            "source_no": self.source_no,
            "source_system": self.source_system,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse_name,
            "planned_date": self.planned_date.isoformat() if self.planned_date else None,
            "actual_date": self.actual_date.isoformat() if self.actual_date else None,
            "total_planned_qty": float(self.total_planned_qty) if self.total_planned_qty else 0,
            "total_received_qty": float(self.total_received_qty) if self.total_received_qty else 0,
            "is_inspected": self.is_inspected,
            "inspection_result": self.inspection_result,
            "inspection_date": self.inspection_date.isoformat() if self.inspection_date else None,
            "inspector_id": self.inspector_id,
            "inspector_name": self.inspector_name,
            "remark": self.remark,
            "attachments": self.attachments,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
            "received_by": self.received_by,
            "received_by_name": self.received_by_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items.all()]
        return data

    @staticmethod
    def generate_order_no(inbound_type="purchase"):
        """生成入库单号：IN-{类型前缀}-YYYYMMDD-XXXXX"""
        prefix_map = {
            "purchase": "PU",    # 采购入库
            "production": "PR",  # 生产入库
            "transfer": "TR",    # 调拨入库
            "return": "RT",      # 退货入库
            "other": "OT",       # 其他入库
        }
        prefix = prefix_map.get(inbound_type, "OT")
        today = datetime.utcnow().strftime('%Y%m%d')

        count = InboundOrder.query.filter(
            db.func.DATE(InboundOrder.created_at) == datetime.utcnow().date()
        ).count()

        seq = str(count + 1).zfill(5)
        return f'IN-{prefix}-{today}-{seq}'


class InboundOrderItem(db.Model):
    """入库单明细"""
    __tablename__ = "scm_inbound_order_items"
    __table_args__ = (
        db.Index('idx_inbound_item_order', 'order_id'),
        db.Index('idx_inbound_item_material', 'material_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('scm_inbound_orders.id', ondelete='CASCADE'), nullable=False, comment="入库单ID")
    line_no = db.Column(db.Integer, nullable=False, default=1, comment="行号")

    # 物料信息
    material_id = db.Column(db.Integer, db.ForeignKey('scm_materials.id'), comment="物料ID")
    material_code = db.Column(db.String(50), nullable=False, comment="物料编码")
    material_name = db.Column(db.String(200), comment="物料名称")
    specification = db.Column(db.String(200), comment="规格")

    # 数量信息
    planned_qty = db.Column(db.Numeric(18, 4), nullable=False, default=0, comment="计划数量")
    received_qty = db.Column(db.Numeric(18, 4), default=0, comment="实收数量")
    rejected_qty = db.Column(db.Numeric(18, 4), default=0, comment="拒收数量")
    uom = db.Column(db.String(20), default="pcs", comment="单位")

    # 存储位置
    bin_id = db.Column(db.Integer, db.ForeignKey('scm_storage_bins.id'), comment="库位ID")
    bin_code = db.Column(db.String(50), comment="库位编码")

    # 批次/序列号
    batch_no = db.Column(db.String(50), comment="批次号")
    serial_no = db.Column(db.String(100), comment="序列号")
    production_date = db.Column(db.Date, comment="生产日期")
    expiry_date = db.Column(db.Date, comment="过期日期")

    # 价格信息
    unit_price = db.Column(db.Numeric(18, 4), comment="单价")
    amount = db.Column(db.Numeric(18, 2), comment="金额")
    currency = db.Column(db.String(10), default="CNY", comment="币种")

    # 质检信息
    is_inspected = db.Column(db.Boolean, default=False, comment="是否已质检")
    inspection_result = db.Column(db.String(20), comment="质检结果")  # passed/failed
    inspection_note = db.Column(db.Text, comment="质检备注")

    # 来源行信息
    source_line_no = db.Column(db.Integer, comment="来源单行号")
    source_item_id = db.Column(db.Integer, comment="来源单明细ID")

    # 备注
    remark = db.Column(db.Text, comment="备注")

    # 时间戳
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    material = db.relationship('Material', backref='inbound_items')
    bin = db.relationship('StorageBin', backref='inbound_items')

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "line_no": self.line_no,
            "material_id": self.material_id,
            "material_code": self.material_code,
            "material_name": self.material_name,
            "specification": self.specification,
            "planned_qty": float(self.planned_qty) if self.planned_qty else 0,
            "received_qty": float(self.received_qty) if self.received_qty else 0,
            "rejected_qty": float(self.rejected_qty) if self.rejected_qty else 0,
            "uom": self.uom,
            "bin_id": self.bin_id,
            "bin_code": self.bin_code,
            "batch_no": self.batch_no,
            "serial_no": self.serial_no,
            "production_date": self.production_date.isoformat() if self.production_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "unit_price": float(self.unit_price) if self.unit_price else None,
            "amount": float(self.amount) if self.amount else None,
            "currency": self.currency,
            "is_inspected": self.is_inspected,
            "inspection_result": self.inspection_result,
            "inspection_note": self.inspection_note,
            "source_line_no": self.source_line_no,
            "source_item_id": self.source_item_id,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InboundReceiveLog(db.Model):
    """入库收货记录 - 记录每次收货操作"""
    __tablename__ = "scm_inbound_receive_logs"
    __table_args__ = (
        db.Index('idx_receive_log_order', 'order_id'),
        db.Index('idx_receive_log_item', 'item_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('scm_inbound_orders.id', ondelete='CASCADE'), nullable=False, comment="入库单ID")
    item_id = db.Column(db.Integer, db.ForeignKey('scm_inbound_order_items.id', ondelete='CASCADE'), comment="入库单明细ID")

    # 收货信息
    received_qty = db.Column(db.Numeric(18, 4), nullable=False, comment="本次收货数量")
    rejected_qty = db.Column(db.Numeric(18, 4), default=0, comment="本次拒收数量")

    # 存储位置
    bin_id = db.Column(db.Integer, comment="库位ID")
    bin_code = db.Column(db.String(50), comment="库位编码")

    # 批次信息
    batch_no = db.Column(db.String(50), comment="批次号")
    serial_no = db.Column(db.String(100), comment="序列号")

    # 操作人
    received_by = db.Column(db.Integer, comment="收货人ID")
    received_by_name = db.Column(db.String(50), comment="收货人姓名")
    received_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment="收货时间")

    # 备注
    remark = db.Column(db.Text, comment="备注")

    # 库存流水ID
    inventory_tx_id = db.Column(db.Integer, comment="关联的库存流水ID")

    # 时间戳
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "item_id": self.item_id,
            "received_qty": float(self.received_qty) if self.received_qty else 0,
            "rejected_qty": float(self.rejected_qty) if self.rejected_qty else 0,
            "bin_id": self.bin_id,
            "bin_code": self.bin_code,
            "batch_no": self.batch_no,
            "serial_no": self.serial_no,
            "received_by": self.received_by,
            "received_by_name": self.received_by_name,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "remark": self.remark,
            "inventory_tx_id": self.inventory_tx_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
