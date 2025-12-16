# backend/app/models/stocktake.py
"""
库存盘点模型
- 支持全盘/抽盘/循环盘点
- 盘点差异处理
- 自动调整库存
"""
from __future__ import annotations
import enum
from datetime import datetime
from decimal import Decimal
from app import db


class StocktakeStatus(enum.Enum):
    """盘点单状态"""
    DRAFT = "draft"           # 草稿
    IN_PROGRESS = "in_progress"  # 盘点中
    PENDING_REVIEW = "pending_review"  # 待审核
    APPROVED = "approved"     # 已审核
    ADJUSTED = "adjusted"     # 已调整
    CANCELLED = "cancelled"   # 已取消


class StocktakeType(enum.Enum):
    """盘点类型"""
    FULL = "full"             # 全盘
    PARTIAL = "partial"       # 抽盘
    CYCLE = "cycle"           # 循环盘点
    SPOT = "spot"             # 抽查


STOCKTAKE_STATUS_MAP = {
    "draft": "草稿",
    "in_progress": "盘点中",
    "pending_review": "待审核",
    "approved": "已审核",
    "adjusted": "已调整",
    "cancelled": "已取消",
}

STOCKTAKE_TYPE_MAP = {
    "full": "全盘",
    "partial": "抽盘",
    "cycle": "循环盘点",
    "spot": "抽查",
}


class StocktakeOrder(db.Model):
    """盘点单"""
    __tablename__ = "scm_stocktake_orders"
    __table_args__ = (
        db.Index('idx_stocktake_order_no', 'order_no'),
        db.Index('idx_stocktake_status', 'status'),
        db.Index('idx_stocktake_warehouse', 'warehouse_id'),
        db.Index('idx_stocktake_date', 'stocktake_date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False, comment="盘点单号")

    # 盘点类型和状态
    stocktake_type = db.Column(db.Enum(StocktakeType), nullable=False, default=StocktakeType.FULL, comment="盘点类型")
    status = db.Column(db.Enum(StocktakeStatus), nullable=False, default=StocktakeStatus.DRAFT, comment="状态")

    # 盘点范围
    warehouse_id = db.Column(db.Integer, db.ForeignKey('scm_warehouses.id'), nullable=False, comment="盘点仓库")
    warehouse_name = db.Column(db.String(100), comment="仓库名称")
    category_id = db.Column(db.Integer, comment="物料分类ID（可选，用于抽盘）")
    category_name = db.Column(db.String(100), comment="物料分类名称")

    # 盘点信息
    stocktake_date = db.Column(db.Date, nullable=False, comment="盘点日期")
    start_time = db.Column(db.DateTime, comment="开始时间")
    end_time = db.Column(db.DateTime, comment="结束时间")

    # 汇总数据
    total_items = db.Column(db.Integer, default=0, comment="盘点项数")
    counted_items = db.Column(db.Integer, default=0, comment="已盘点项数")
    diff_items = db.Column(db.Integer, default=0, comment="差异项数")
    total_book_qty = db.Column(db.Numeric(18, 4), default=0, comment="账面总数量")
    total_actual_qty = db.Column(db.Numeric(18, 4), default=0, comment="实际总数量")
    total_diff_qty = db.Column(db.Numeric(18, 4), default=0, comment="差异总数量")
    total_diff_amount = db.Column(db.Numeric(18, 2), default=0, comment="差异总金额")

    # 备注和附件
    remark = db.Column(db.Text, comment="备注")
    attachments = db.Column(db.JSON, comment="附件列表")

    # 操作人信息
    created_by = db.Column(db.Integer, comment="创建人ID")
    created_by_name = db.Column(db.String(50), comment="创建人姓名")
    stocktaker_id = db.Column(db.Integer, comment="盘点员ID")
    stocktaker_name = db.Column(db.String(50), comment="盘点员姓名")
    reviewer_id = db.Column(db.Integer, comment="审核人ID")
    reviewer_name = db.Column(db.String(50), comment="审核人姓名")
    reviewed_at = db.Column(db.DateTime, comment="审核时间")
    review_remark = db.Column(db.Text, comment="审核备注")

    # 时间戳
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    warehouse = db.relationship('Warehouse', backref='stocktake_orders')
    items = db.relationship('StocktakeOrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_items=False):
        data = {
            "id": self.id,
            "order_no": self.order_no,
            "stocktake_type": self.stocktake_type.value if self.stocktake_type else None,
            "stocktake_type_text": STOCKTAKE_TYPE_MAP.get(self.stocktake_type.value) if self.stocktake_type else None,
            "status": self.status.value if self.status else None,
            "status_text": STOCKTAKE_STATUS_MAP.get(self.status.value) if self.status else None,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse_name,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "stocktake_date": self.stocktake_date.isoformat() if self.stocktake_date else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_items": self.total_items,
            "counted_items": self.counted_items,
            "diff_items": self.diff_items,
            "total_book_qty": float(self.total_book_qty) if self.total_book_qty else 0,
            "total_actual_qty": float(self.total_actual_qty) if self.total_actual_qty else 0,
            "total_diff_qty": float(self.total_diff_qty) if self.total_diff_qty else 0,
            "total_diff_amount": float(self.total_diff_amount) if self.total_diff_amount else 0,
            "remark": self.remark,
            "attachments": self.attachments,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
            "stocktaker_id": self.stocktaker_id,
            "stocktaker_name": self.stocktaker_name,
            "reviewer_id": self.reviewer_id,
            "reviewer_name": self.reviewer_name,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_remark": self.review_remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "progress": round(self.counted_items / self.total_items * 100, 1) if self.total_items > 0 else 0,
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items.all()]
        return data

    @staticmethod
    def generate_order_no(stocktake_type="full"):
        """生成盘点单号：ST-{类型前缀}-YYYYMMDD-XXXXX"""
        prefix_map = {
            "full": "FL",      # 全盘
            "partial": "PT",   # 抽盘
            "cycle": "CY",     # 循环盘点
            "spot": "SP",      # 抽查
        }
        prefix = prefix_map.get(stocktake_type, "FL")
        today = datetime.utcnow().strftime('%Y%m%d')

        count = StocktakeOrder.query.filter(
            db.func.DATE(StocktakeOrder.created_at) == datetime.utcnow().date()
        ).count()

        seq = str(count + 1).zfill(5)
        return f'ST-{prefix}-{today}-{seq}'


class StocktakeOrderItem(db.Model):
    """盘点单明细"""
    __tablename__ = "scm_stocktake_order_items"
    __table_args__ = (
        db.Index('idx_stocktake_item_order', 'order_id'),
        db.Index('idx_stocktake_item_material', 'material_id'),
        db.Index('idx_stocktake_item_status', 'count_status'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('scm_stocktake_orders.id', ondelete='CASCADE'), nullable=False, comment="盘点单ID")
    line_no = db.Column(db.Integer, nullable=False, default=1, comment="行号")

    # 物料信息
    material_id = db.Column(db.Integer, db.ForeignKey('scm_materials.id'), comment="物料ID")
    material_code = db.Column(db.String(50), nullable=False, comment="物料编码")
    material_name = db.Column(db.String(200), comment="物料名称")
    specification = db.Column(db.String(200), comment="规格")
    uom = db.Column(db.String(20), default="pcs", comment="单位")

    # 存储位置
    bin_id = db.Column(db.Integer, db.ForeignKey('scm_storage_bins.id'), comment="库位ID")
    bin_code = db.Column(db.String(50), comment="库位编码")

    # 批次信息
    batch_no = db.Column(db.String(50), comment="批次号")

    # 数量信息
    book_qty = db.Column(db.Numeric(18, 4), nullable=False, default=0, comment="账面数量")
    actual_qty = db.Column(db.Numeric(18, 4), comment="实际数量")
    diff_qty = db.Column(db.Numeric(18, 4), default=0, comment="差异数量（实际-账面）")

    # 金额信息
    unit_cost = db.Column(db.Numeric(18, 4), default=0, comment="单位成本")
    book_amount = db.Column(db.Numeric(18, 2), default=0, comment="账面金额")
    actual_amount = db.Column(db.Numeric(18, 2), default=0, comment="实际金额")
    diff_amount = db.Column(db.Numeric(18, 2), default=0, comment="差异金额")

    # 盘点状态
    count_status = db.Column(db.String(20), default="pending", comment="盘点状态")  # pending/counted/adjusted
    counted_at = db.Column(db.DateTime, comment="盘点时间")
    counted_by = db.Column(db.Integer, comment="盘点人ID")
    counted_by_name = db.Column(db.String(50), comment="盘点人姓名")

    # 差异处理
    diff_reason = db.Column(db.String(200), comment="差异原因")
    adjust_status = db.Column(db.String(20), comment="调整状态")  # pending/approved/rejected
    adjust_remark = db.Column(db.Text, comment="调整备注")

    # 库存记录ID
    inventory_id = db.Column(db.Integer, comment="关联的库存记录ID")

    # 备注
    remark = db.Column(db.Text, comment="备注")

    # 时间戳
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    material = db.relationship('Material', backref='stocktake_items')
    bin = db.relationship('StorageBin', backref='stocktake_items')

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "line_no": self.line_no,
            "material_id": self.material_id,
            "material_code": self.material_code,
            "material_name": self.material_name,
            "specification": self.specification,
            "uom": self.uom,
            "bin_id": self.bin_id,
            "bin_code": self.bin_code,
            "batch_no": self.batch_no,
            "book_qty": float(self.book_qty) if self.book_qty else 0,
            "actual_qty": float(self.actual_qty) if self.actual_qty is not None else None,
            "diff_qty": float(self.diff_qty) if self.diff_qty else 0,
            "unit_cost": float(self.unit_cost) if self.unit_cost else 0,
            "book_amount": float(self.book_amount) if self.book_amount else 0,
            "actual_amount": float(self.actual_amount) if self.actual_amount else 0,
            "diff_amount": float(self.diff_amount) if self.diff_amount else 0,
            "count_status": self.count_status,
            "counted_at": self.counted_at.isoformat() if self.counted_at else None,
            "counted_by": self.counted_by,
            "counted_by_name": self.counted_by_name,
            "diff_reason": self.diff_reason,
            "adjust_status": self.adjust_status,
            "adjust_remark": self.adjust_remark,
            "inventory_id": self.inventory_id,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class StocktakeAdjustLog(db.Model):
    """盘点调整记录"""
    __tablename__ = "scm_stocktake_adjust_logs"
    __table_args__ = (
        db.Index('idx_adjust_log_order', 'order_id'),
        db.Index('idx_adjust_log_item', 'item_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('scm_stocktake_orders.id', ondelete='CASCADE'), nullable=False, comment="盘点单ID")
    item_id = db.Column(db.Integer, db.ForeignKey('scm_stocktake_order_items.id', ondelete='CASCADE'), comment="盘点明细ID")

    # 调整信息
    material_code = db.Column(db.String(50), comment="物料编码")
    material_name = db.Column(db.String(200), comment="物料名称")
    book_qty = db.Column(db.Numeric(18, 4), comment="账面数量")
    actual_qty = db.Column(db.Numeric(18, 4), comment="实际数量")
    adjust_qty = db.Column(db.Numeric(18, 4), comment="调整数量")
    adjust_type = db.Column(db.String(20), comment="调整类型")  # increase/decrease

    # 操作人
    adjusted_by = db.Column(db.Integer, comment="调整人ID")
    adjusted_by_name = db.Column(db.String(50), comment="调整人姓名")
    adjusted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment="调整时间")

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
            "material_code": self.material_code,
            "material_name": self.material_name,
            "book_qty": float(self.book_qty) if self.book_qty else 0,
            "actual_qty": float(self.actual_qty) if self.actual_qty else 0,
            "adjust_qty": float(self.adjust_qty) if self.adjust_qty else 0,
            "adjust_type": self.adjust_type,
            "adjusted_by": self.adjusted_by,
            "adjusted_by_name": self.adjusted_by_name,
            "adjusted_at": self.adjusted_at.isoformat() if self.adjusted_at else None,
            "remark": self.remark,
            "inventory_tx_id": self.inventory_tx_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
