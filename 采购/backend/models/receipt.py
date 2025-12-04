# models/receipt.py
# -*- coding: utf-8 -*-
"""
收货回执模型
"""
from sqlalchemy import String, DateTime, ForeignKey, Index, Text, Integer
from sqlalchemy.dialects.mysql import BIGINT
from datetime import datetime
from extensions import db


class Receipt(db.Model):
    __tablename__ = 'receipts'
    __table_args__ = (
        Index('idx_receipts_po_id', 'po_id'),
        Index('idx_receipts_receiver_id', 'receiver_id'),
        Index('idx_receipts_status', 'status'),
        Index('idx_receipts_received_date', 'received_date'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)

    # 外键关系
    po_id = db.Column(BIGINT(unsigned=True), ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=False)
    receiver_id = db.Column(BIGINT(unsigned=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # 回执信息
    receipt_number = db.Column(String(100), unique=True, nullable=False)  # 回执编号
    received_date = db.Column(DateTime, nullable=False)  # 收货日期

    # 收货详情
    quality_status = db.Column(String(20), nullable=False, default='qualified')
    # 可选值: qualified(合格) / defective(有缺陷) / rejected(拒收)

    quantity_received = db.Column(Integer, nullable=True)  # 实际收货数量
    notes = db.Column(Text, nullable=True)  # 备注说明
    photos = db.Column(Text, nullable=True)  # 照片URL列表（JSON格式）

    # 状态
    status = db.Column(String(20), default='confirmed', nullable=False)
    # 可选值: confirmed(已确认) / disputed(有争议)

    # 时间戳
    created_at = db.Column(DateTime, default=datetime.utcnow)
    created_by = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=True)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    po = db.relationship('PurchaseOrder', backref='receipts', lazy=True)
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_items', lazy=True)
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_receipts', lazy=True)

    def __repr__(self):
        return f'<Receipt {self.receipt_number}>'

    @staticmethod
    def generate_receipt_number():
        """生成收货回执编号：RCP-YYYYMMDD-XXXXX"""
        today = datetime.utcnow().strftime('%Y%m%d')

        count = Receipt.query.filter(
            db.func.DATE(Receipt.created_at) == datetime.utcnow().date()
        ).count()

        seq = str(count + 1).zfill(5)
        return f'RCP-{today}-{seq}'

    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'receipt_number': self.receipt_number,
            'po_id': self.po_id,
            'receiver_id': self.receiver_id,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'quality_status': self.quality_status,
            'quantity_received': self.quantity_received,
            'notes': self.notes,
            'photos': self.photos,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'po': {
                'id': self.po.id,
                'po_number': self.po.po_number,
                'supplier_name': self.po.supplier_name,
                'total_price': float(self.po.total_price),
                'status': self.po.status,
            } if self.po else None,
            'receiver': {
                'id': self.receiver.id,
                'username': self.receiver.username,
                'realname': self.receiver.realname,
            } if self.receiver else None,
            'items': [item.to_dict() for item in self.items] if hasattr(self, 'items') else [],
        }


class ReceiptItem(db.Model):
    """收货回执明细 - 物料级别的收货质检信息"""
    __tablename__ = 'receipt_items'
    __table_args__ = (
        Index('idx_receipt_items_receipt_id', 'receipt_id'),
        Index('idx_receipt_items_material_code', 'material_code'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)

    # 外键关系
    receipt_id = db.Column(BIGINT(unsigned=True), ForeignKey('receipts.id', ondelete='CASCADE'), nullable=False)

    # 物料信息
    material_code = db.Column(String(100), nullable=False)  # 物料编码/SKU
    material_name = db.Column(String(255), nullable=True)  # 物料名称

    # 数量信息
    quantity_ordered = db.Column(Integer, nullable=False, default=0)  # 订单数量
    quantity_delivered = db.Column(Integer, nullable=False, default=0)  # 到货数量
    quantity_accepted = db.Column(Integer, nullable=False, default=0)  # 合格数量
    quantity_rejected = db.Column(Integer, nullable=False, default=0)  # 不良数量

    # 质量信息
    pass_rate = db.Column(db.Float, nullable=True)  # 合格率
    rejection_reason = db.Column(Text, nullable=True)  # 拒收原因

    # 仓库信息（用于集成）
    lot_number = db.Column(String(100), nullable=True)  # 批次号
    storage_location = db.Column(String(100), nullable=True)  # 存储位置

    # 时间戳
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    receipt = db.relationship('Receipt', backref=db.backref('items', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<ReceiptItem {self.material_code} - {self.quantity_accepted}/{self.quantity_delivered}>'

    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'receipt_id': self.receipt_id,
            'material_code': self.material_code,
            'material_name': self.material_name,
            'quantity_ordered': self.quantity_ordered,
            'quantity_delivered': self.quantity_delivered,
            'quantity_accepted': self.quantity_accepted,
            'quantity_rejected': self.quantity_rejected,
            'pass_rate': self.pass_rate,
            'rejection_reason': self.rejection_reason,
            'lot_number': self.lot_number,
            'storage_location': self.storage_location,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
