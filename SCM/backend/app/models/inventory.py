from __future__ import annotations
from datetime import datetime
from app import db

class InventoryTx(db.Model):
    """
    库存流水表：
    - 单据粒度的库存变动记录（正数=入库，负数=出库）
    - 以 product_text（内部图号）为主键维度；可选仓位、地点、订单号等属性
    """
    __tablename__ = "inventory_tx"

    id = db.Column(db.Integer, primary_key=True)
    product_text = db.Column(db.String(128), nullable=False, index=True)  # 内部图号
    qty_delta = db.Column(db.Float, nullable=False, default=0)             # 数量变化（+入/-出）

    tx_type   = db.Column(db.String(32), index=True)                       # 入库/出库/盘点/调整…
    order_no  = db.Column(db.String(64), index=True)                       # 关联订单编号（可选）
    bin_code  = db.Column(db.String(64), index=True)                       # 仓位（可选）
    location  = db.Column(db.String(16), index=True)                       # 地点（深圳/东莞）
    uom       = db.Column(db.String(16), default="pcs")                    # 单位，默认 pcs
    ref       = db.Column(db.String(128))                                   # 其他业务参考号
    remark    = db.Column(db.String(255))                                   # 备注

    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)  # 业务发生时间
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "product_text": self.product_text,
            "qty_delta": self.qty_delta,
            "tx_type": self.tx_type,
            "order_no": self.order_no,
            "bin_code": self.bin_code,
            "location": self.location,
            "uom": self.uom,
            "ref": self.ref,
            "remark": self.remark,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
