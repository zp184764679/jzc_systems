# models/invoice.py
# -*- coding: utf-8 -*-
"""
发票模型 - 支持两种结算方式:
1. 单次结算 (per_order): 每个PO对应一张发票，po_id必填
2. 月结 (monthly): 一张发票对应多个PO，通过 invoice_po_links 关联

月结发票的 po_id 为空，改用 invoice_po_links 表关联多个PO
"""
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Index, Text
from sqlalchemy.dialects.mysql import BIGINT
from datetime import datetime
from extensions import db


# 发票-PO关联表（用于月结发票关联多个PO）
class InvoicePOLink(db.Model):
    """发票与PO的多对多关联表"""
    __tablename__ = 'invoice_po_links'
    __table_args__ = (
        db.UniqueConstraint('invoice_id', 'po_id', name='uq_invoice_po'),
        Index('idx_invoice_po_links_invoice', 'invoice_id'),
        Index('idx_invoice_po_links_po', 'po_id'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    invoice_id = db.Column(BIGINT(unsigned=True), ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False)
    po_id = db.Column(BIGINT(unsigned=True), ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=False)

    # 该PO在此发票中的金额（可选，用于分摊）
    po_amount = db.Column(Numeric(12, 2), nullable=True, comment='该PO对应的发票金额')

    created_at = db.Column(DateTime, default=datetime.utcnow)

    # 关系
    invoice = db.relationship('Invoice', back_populates='po_links')
    po = db.relationship('PurchaseOrder', backref='invoice_links', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'po_id': self.po_id,
            'po_amount': float(self.po_amount) if self.po_amount else None,
            'po': {
                'id': self.po.id,
                'po_number': self.po.po_number,
                'total_price': float(self.po.total_price) if self.po.total_price else 0,
                'status': self.po.status,
            } if self.po else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Invoice(db.Model):
    __tablename__ = 'invoices'
    __table_args__ = (
        Index('idx_invoices_supplier_id', 'supplier_id'),
        Index('idx_invoices_po_id', 'po_id'),
        Index('idx_invoices_quote_id', 'quote_id'),
        Index('idx_invoices_status', 'status'),
        Index('idx_invoices_created_at', 'created_at'),
        Index('idx_invoices_settlement_type', 'settlement_type'),
        Index('idx_invoices_settlement_period', 'settlement_period'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)

    # 结算方式
    # per_order: 单次结算，po_id必填
    # monthly: 月结，po_id为空，通过po_links关联多个PO
    settlement_type = db.Column(String(20), default='per_order', nullable=False, comment='结算方式')
    settlement_period = db.Column(String(10), nullable=True, comment='结算周期（月结时使用，格式：YYYY-MM）')

    # 外键关系
    supplier_id = db.Column(BIGINT(unsigned=True), ForeignKey('suppliers.id', ondelete='CASCADE'), nullable=False)
    # po_id改为nullable，月结发票不需要直接关联单个PO
    po_id = db.Column(BIGINT(unsigned=True), ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=True, comment='单次结算时的PO ID')
    quote_id = db.Column(BIGINT(unsigned=True), ForeignKey('supplier_quotes.id', ondelete='SET NULL'), nullable=True)
    
    # 发票信息
    invoice_code = db.Column(String(50), nullable=True)  # 发票代码（10-12位）
    invoice_number = db.Column(String(100), unique=True, nullable=False)  # 发票号码
    invoice_date = db.Column(DateTime, nullable=True)  # 开票日期

    # 购买方信息
    buyer_name = db.Column(String(255), nullable=True)  # 购买方名称
    buyer_tax_id = db.Column(String(50), nullable=True)  # 购买方纳税人识别号/统一社会信用代码

    # 销售方信息（供应商）
    seller_name = db.Column(String(255), nullable=True)  # 销售方名称
    seller_tax_id = db.Column(String(50), nullable=True)  # 销售方纳税人识别号

    # 金额信息
    amount_before_tax = db.Column(Numeric(12, 2), nullable=True)  # 金额合计（不含税）
    tax_amount = db.Column(Numeric(12, 2), nullable=True)  # 税额合计
    total_amount = db.Column(Numeric(12, 2), nullable=True)  # 价税合计
    amount = db.Column(Numeric(12, 2), nullable=False)  # 发票金额（兼容旧版，通常等于total_amount）
    currency = db.Column(String(10), default='CNY', nullable=False)  # 货币
    
    # 文件信息
    file_url = db.Column(Text, nullable=False)  # 文件地址/URL
    file_name = db.Column(String(255), nullable=True)  # 文件名
    file_type = db.Column(String(50), nullable=True)  # 文件类型（PDF、图片等）
    file_size = db.Column(String(20), nullable=True)  # 文件大小（MB/字节）
    
    # 备注信息
    description = db.Column(Text, nullable=True)  # 发票描述（向后兼容）
    remark = db.Column(Text, nullable=True)  # 备注说明（中国发票格式）
    
    # 审批状态
    status = db.Column(String(20), default='pending', nullable=False)
    # 可选值: pending(待审批) / approved(已批准) / rejected(已拒绝) / expired(已过期)
    
    approval_notes = db.Column(Text, nullable=True)  # 审批意见
    approved_by = db.Column(BIGINT(unsigned=True), nullable=True)  # 审批人ID
    approved_at = db.Column(DateTime, nullable=True)  # 审批时间
    
    # 时间戳
    created_at = db.Column(DateTime, default=datetime.utcnow)  # 创建时间
    uploaded_at = db.Column(DateTime, nullable=True)  # 上传时间
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expiry_date = db.Column(DateTime, nullable=True)  # 发票过期日期
    
    # 关系
    supplier = db.relationship('Supplier', backref='invoices', lazy=True)
    po = db.relationship('PurchaseOrder', backref='invoices', lazy=True)
    quote = db.relationship('SupplierQuote', backref='invoices', lazy=True)
    # 月结发票关联的多个PO
    po_links = db.relationship('InvoicePOLink', back_populates='invoice', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

    def get_all_pos(self):
        """获取该发票关联的所有PO（兼容单次结算和月结）"""
        if self.settlement_type == 'monthly':
            return [link.po for link in self.po_links if link.po]
        elif self.po:
            return [self.po]
        return []

    def get_total_po_amount(self):
        """计算关联PO的总金额"""
        pos = self.get_all_pos()
        return sum(float(po.total_price) if po.total_price else 0 for po in pos)

    def to_dict(self, include_po_links=True):
        result = {
            'id': self.id,
            'settlement_type': self.settlement_type,
            'settlement_period': self.settlement_period,
            'invoice_code': self.invoice_code,
            'invoice_number': self.invoice_number,
            'supplier_id': self.supplier_id,
            'po_id': self.po_id,
            'quote_id': self.quote_id,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'buyer_name': self.buyer_name,
            'buyer_tax_id': self.buyer_tax_id,
            'seller_name': self.seller_name,
            'seller_tax_id': self.seller_tax_id,
            'amount_before_tax': float(self.amount_before_tax) if self.amount_before_tax else None,
            'tax_amount': float(self.tax_amount) if self.tax_amount else None,
            'total_amount': float(self.total_amount) if self.total_amount else None,
            'amount': float(self.amount) if self.amount else 0,
            'currency': self.currency,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'description': self.description,
            'remark': self.remark,
            'status': self.status,
            'approval_notes': self.approval_notes,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'supplier': {
                'id': self.supplier.id,
                'company_name': self.supplier.company_name,
                'code': self.supplier.code,
                'settlement_type': self.supplier.settlement_type,
            } if self.supplier else None,
            'po': {
                'id': self.po.id,
                'po_number': self.po.po_number,
                'total_price': float(self.po.total_price) if self.po.total_price else 0,
                'status': self.po.status,
            } if self.po else None,
            'quote': {
                'id': self.quote.id,
                'quote_number': self.quote.quote_number,
                'item_name': self.quote.item_name,
            } if self.quote else None,
        }

        # 月结发票时，包含所有关联的PO
        if include_po_links and self.settlement_type == 'monthly' and self.po_links:
            result['po_links'] = [link.to_dict() for link in self.po_links]
            result['po_count'] = len(self.po_links)
            result['total_po_amount'] = self.get_total_po_amount()

        return result