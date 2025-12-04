# models/supplier_quote.py
# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, VARCHAR, TEXT, DECIMAL
from extensions import db

# -------- 内部工具：生成展示编号 YYMMDD-SSSS-QQQ --------
def _pad_int(n, width):
    try:
        n = int(n)
        return f"{n:0{width}d}"
    except Exception:
        return "0" * width

def _supplier_code4(supplier):
    """
    供应商4位编码：
      - 优先用 supplier.code（若含数字取数字部分；不足左补零到4位）
      - 没有则用 supplier.id 左补零到4位
    """
    code = None
    try:
        raw = getattr(supplier, "code", None)
        if raw:
            s = str(raw).strip()
            digits = "".join([c for c in s if c.isdigit()]) or "0"
            code = _pad_int(digits, 4)[-4:]
    except Exception:
        code = None
    if not code:
        code = _pad_int(getattr(supplier, "id", 0), 4)
    return code

def generate_quote_display_no(quote_obj):
    """
    生成展示编号：YYMMDD-SSSS-QQQ
      - YYMMDD：created_at（无则当前UTC）
      - SSSS：supplier.code（数字部分）或 supplier.id，左补零4位
      - QQQ：quote.id % 1000 的三位序号（如需“每日001递增”，需改为每日流水机制）
    """
    dt = getattr(quote_obj, "created_at", None) or datetime.utcnow()
    day = dt.strftime("%y%m%d")
    supplier = getattr(quote_obj, "supplier", None)
    ssss = _supplier_code4(supplier)
    qqq = _pad_int(getattr(quote_obj, "id", 0) % 1000, 3)
    return f"{day}-{ssss}-{qqq}"


class SupplierQuote(db.Model):
    __tablename__ = "supplier_quotes"
    __table_args__ = (
        db.Index('idx_sq_rfq_id', 'rfq_id'),
        db.Index('idx_sq_supplier_id', 'supplier_id'),
        db.Index('idx_sq_rfq_item_id', 'rfq_item_id'),  # 🔧 新增：RFQ物料项索引
        db.Index('idx_sq_status', 'status'),
        db.Index('idx_sq_total_price', 'total_price'),
        # 复合索引（与你的迁移一致）
        db.Index('ix_supplier_quotes_supplier_rfq_item', 'supplier_id', 'rfq_id', 'item_name'),
        # 🔧 修改：按物料项的唯一索引（避免同一供应商对同一RFQ的同一物料项重复报价）
        db.Index('ix_supplier_quotes_supplier_rfq_item_id', 'supplier_id', 'rfq_id', 'rfq_item_id', unique=True),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    rfq_id = db.Column(BIGINT(unsigned=True), ForeignKey('rfqs.id'), nullable=False)
    rfq_item_id = db.Column(BIGINT(unsigned=True), ForeignKey('rfq_items.id'), nullable=True, comment='关联的RFQ物料项ID，每个物料单独报价')  # 🔧 新增字段
    supplier_id = db.Column(BIGINT(unsigned=True), ForeignKey('suppliers.id'), nullable=False)

    # 状态：pending/received/expired/withdrawn
    status = db.Column(VARCHAR(20), nullable=False, default='pending', index=True)

    # 品类分组字段（新增）- 用于按品类合并报价
    category = db.Column(VARCHAR(100), nullable=True, index=True, comment='品类名称，如"刀具/铣削刀具"')

    # 逐条物料邀请所需字段（保留向后兼容，但现在用于存储品类信息或废弃）
    item_name = db.Column(VARCHAR(200), nullable=True)
    item_description = db.Column(TEXT, nullable=True)
    quantity_requested = db.Column(db.Integer, nullable=True)
    unit = db.Column(VARCHAR(50), nullable=True)

    # 报价汇总字段
    total_price = db.Column(DECIMAL(12, 2), nullable=True)
    lead_time = db.Column(db.Integer, nullable=True)
    supplier_name = db.Column(VARCHAR(200), nullable=True)
    payment_terms = db.Column(db.Integer, default=90, nullable=False, comment='供应商报价付款周期(天)')

    # 报价号（持久化存储）
    quote_number = db.Column(VARCHAR(50), nullable=True, unique=True, index=True)

    # 报价内容（JSON，自由填写）
    quote_json = db.Column(TEXT, nullable=True)

    # 元数据
    created_at = db.Column(DATETIME, default=datetime.utcnow)
    responded_at = db.Column(DATETIME, nullable=True)
    expired_at = db.Column(DATETIME, nullable=True)

    # 关系
    rfq = relationship("RFQ", back_populates="quotes")
    supplier = relationship("Supplier")

    # -------- 可选：便捷属性 --------
    @property
    def display_no(self) -> str:
        """计算型展示编号：YYMMDD-SSSS-QQQ"""
        return generate_quote_display_no(self)

    def __repr__(self):
        return f'<SupplierQuote {self.id}: RFQ#{self.rfq_id} Supplier#{self.supplier_id}>'

    # -------- 对外序列化 --------
    def to_dict(self):
        def _dt(v):
            return v.isoformat(timespec='seconds') if isinstance(v, datetime) else (v.isoformat() if v else None)

        def _num(v):
            try:
                return float(v) if v is not None else None
            except Exception:
                return None

        # 解析 quote_json
        quote_data = None
        if self.quote_json:
            try:
                import json
                quote_data = json.loads(self.quote_json) if isinstance(self.quote_json, str) else self.quote_json
            except Exception:
                quote_data = None

        return {
            "id": self.id,
            "rfq_id": self.rfq_id,
            "rfq_item_id": self.rfq_item_id,  # 🔧 新增：关联的物料项ID
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name or (self.supplier.company_name if self.supplier else None),
            "status": self.status,
            "category": self.category,  # ✅ 品类标识（已废弃，保留向后兼容）

            # 物料字段（废弃，保留向后兼容）
            "item_name": self.item_name,
            "item_description": self.item_description,
            "quantity_requested": self.quantity_requested,
            "unit": self.unit,

            # 报价汇总
            "total_price": _num(self.total_price),
            "lead_time": self.lead_time,
            "payment_terms": self.payment_terms,

            # 报价详情（解析后的对象，包含items数组）
            "quote_data": quote_data,

            # 时间
            "created_at": _dt(self.created_at),
            "responded_at": _dt(self.responded_at),
            "expired_at": _dt(self.expired_at),

            # 报价号（优先使用持久化的quote_number，如果没有则使用计算型display_no）
            "quote_number": self.quote_number,
            "display_no": self.quote_number or self.display_no,
        }
