# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, VARCHAR, TEXT, DECIMAL
from extensions import db


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        db.Index('idx_po_rfq_id', 'rfq_id'),
        db.Index('idx_po_quote_id', 'quote_id'),
        db.Index('idx_po_supplier_id', 'supplier_id'),
        db.Index('idx_po_status', 'status'),
        db.Index('idx_po_created_at', 'created_at'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    po_number = db.Column(VARCHAR(50), unique=True, nullable=False, index=True)
    
    # 关联关系
    rfq_id = db.Column(BIGINT(unsigned=True), ForeignKey('rfqs.id'), nullable=False)
    quote_id = db.Column(BIGINT(unsigned=True), ForeignKey('supplier_quotes.id'), nullable=False)
    supplier_id = db.Column(BIGINT(unsigned=True), ForeignKey('suppliers.id'), nullable=False)
    
    # 订单信息
    supplier_name = db.Column(VARCHAR(200), nullable=False)
    total_price = db.Column(DECIMAL(12, 2), nullable=False)
    lead_time = db.Column(db.Integer, nullable=True)
    
    # 报价快照（完整的报价数据JSON）
    quote_data = db.Column(TEXT, nullable=True)
    
    # 状态：created/pending_admin_confirmation/pending_super_admin_confirmation/confirmed/received/completed/cancelled
    status = db.Column(VARCHAR(50), nullable=False, default='created')

    # 发票相关
    invoice_due_date = db.Column(DATETIME, nullable=True)  # 发票截止日期（确认后+7天）
    invoice_uploaded = db.Column(db.Boolean, default=False, nullable=False)  # 是否已上传发票

    # 审批相关字段
    admin_confirmed_by = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=True)  # 管理员确认人
    admin_confirmed_at = db.Column(DATETIME, nullable=True)  # 管理员确认时间
    super_admin_confirmed_by = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=True)  # 超管确认人
    super_admin_confirmed_at = db.Column(DATETIME, nullable=True)  # 超管确认时间
    confirmation_note = db.Column(TEXT, nullable=True)  # 确认备注

    # 时间戳
    created_at = db.Column(DATETIME, default=datetime.utcnow)
    confirmed_at = db.Column(DATETIME, nullable=True)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    rfq = relationship("RFQ", backref="purchase_orders")
    quote = relationship("SupplierQuote")
    supplier = relationship("Supplier")
    admin_confirmed_by_user = relationship("User", foreign_keys=[admin_confirmed_by])
    super_admin_confirmed_by_user = relationship("User", foreign_keys=[super_admin_confirmed_by])

    def __repr__(self):
        return f'<PurchaseOrder {self.po_number}>'

    @staticmethod
    def generate_po_number():
        """生成 PO 编号：PO-YYYYMMDD-XXXXX"""
        today = datetime.utcnow().strftime('%Y%m%d')
        
        count = PurchaseOrder.query.filter(
            db.func.DATE(PurchaseOrder.created_at) == today
        ).count()
        
        seq = str(count + 1).zfill(5)
        return f'PO-{today}-{seq}'

    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'po_number': self.po_number,
            'rfq_id': self.rfq_id,
            'quote_id': self.quote_id,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'total_price': float(self.total_price),
            'lead_time': self.lead_time,
            'status': self.status,
            'invoice_due_date': self.invoice_due_date.isoformat() if self.invoice_due_date else None,
            'invoice_uploaded': self.invoice_uploaded,
            'admin_confirmed_by': self.admin_confirmed_by,
            'admin_confirmed_at': self.admin_confirmed_at.isoformat() if self.admin_confirmed_at else None,
            'super_admin_confirmed_by': self.super_admin_confirmed_by,
            'super_admin_confirmed_at': self.super_admin_confirmed_at.isoformat() if self.super_admin_confirmed_at else None,
            'confirmation_note': self.confirmation_note,
            'created_at': self.created_at.isoformat(),
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'updated_at': self.updated_at.isoformat(),
        }