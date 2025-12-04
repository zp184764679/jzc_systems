# -*- coding: utf-8 -*-
# backend/app/models/pending_shipment.py
"""
待出货订单模型
记录订单的交货要求，关联库存产品
"""
from __future__ import annotations
from datetime import datetime
from app import db


class PendingShipment(db.Model):
    """
    待出货订单表
    当订单创建时（从采购系统或CRM），记录需要在什么时间出什么货
    """
    __tablename__ = "pending_shipments"

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(64), nullable=False, index=True)  # 订单号
    customer_name = db.Column(db.String(128))  # 客户名称
    customer_id = db.Column(db.String(64), index=True)  # 客户ID

    product_text = db.Column(db.String(128), nullable=False, index=True)  # 内部图号
    product_name = db.Column(db.String(200))  # 产品名称
    qty_ordered = db.Column(db.Float, nullable=False, default=0)  # 订单数量
    qty_shipped = db.Column(db.Float, default=0)  # 已出货数量
    uom = db.Column(db.String(16), default="pcs")  # 单位

    delivery_date = db.Column(db.Date, nullable=False, index=True)  # 交货日期
    priority = db.Column(db.Integer, default=0)  # 优先级 (0=普通, 1=高, 2=紧急)

    location = db.Column(db.String(16), index=True)  # 发货地点（深圳/东莞）
    receiver_address = db.Column(db.String(500))  # 收货地址
    receiver_contact = db.Column(db.String(100))  # 收货联系人
    receiver_phone = db.Column(db.String(50))  # 收货电话

    status = db.Column(db.String(20), default='待出货', index=True)  # 状态：待出货/部分出货/已完成/已取消
    remark = db.Column(db.String(255))  # 备注

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def qty_remaining(self):
        """剩余待出货数量"""
        return (self.qty_ordered or 0) - (self.qty_shipped or 0)

    @property
    def is_overdue(self):
        """是否逾期"""
        if not self.delivery_date:
            return False
        return datetime.now().date() > self.delivery_date and self.status == '待出货'

    def to_dict(self):
        return {
            "id": self.id,
            "order_no": self.order_no,
            "customer_name": self.customer_name,
            "customer_id": self.customer_id,
            "product_text": self.product_text,
            "product_name": self.product_name,
            "qty_ordered": self.qty_ordered,
            "qty_shipped": self.qty_shipped,
            "qty_remaining": self.qty_remaining,
            "uom": self.uom,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "priority": self.priority,
            "location": self.location,
            "receiver_address": self.receiver_address,
            "receiver_contact": self.receiver_contact,
            "receiver_phone": self.receiver_phone,
            "status": self.status,
            "remark": self.remark,
            "is_overdue": self.is_overdue,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
