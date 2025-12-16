# -*- coding: utf-8 -*-
"""
采购付款模型
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, VARCHAR, TEXT, DECIMAL, DATE
from extensions import db


class PaymentStatus(Enum):
    """付款状态"""
    DRAFT = 'draft'                        # 草稿
    PENDING_APPROVAL = 'pending_approval'  # 待审批
    APPROVED = 'approved'                  # 已批准
    PROCESSING = 'processing'              # 付款中
    PAID = 'paid'                          # 已付款
    FAILED = 'failed'                      # 付款失败
    CANCELLED = 'cancelled'                # 已取消


class PaymentType(Enum):
    """付款类型"""
    ADVANCE = 'advance'        # 预付款
    PROGRESS = 'progress'      # 进度款
    FINAL = 'final'            # 尾款
    DEPOSIT = 'deposit'        # 定金
    FULL = 'full'              # 全款


class PaymentMethod(Enum):
    """付款方式"""
    BANK_TRANSFER = 'bank_transfer'  # 银行转账
    CHECK = 'check'                  # 支票
    CASH = 'cash'                    # 现金
    LETTER_OF_CREDIT = 'lc'          # 信用证
    ACCEPTANCE = 'acceptance'        # 承兑汇票


PAYMENT_STATUS_LABELS = {
    'draft': '草稿',
    'pending_approval': '待审批',
    'approved': '已批准',
    'processing': '付款中',
    'paid': '已付款',
    'failed': '付款失败',
    'cancelled': '已取消',
}

PAYMENT_TYPE_LABELS = {
    'advance': '预付款',
    'progress': '进度款',
    'final': '尾款',
    'deposit': '定金',
    'full': '全款',
}

PAYMENT_METHOD_LABELS = {
    'bank_transfer': '银行转账',
    'check': '支票',
    'cash': '现金',
    'lc': '信用证',
    'acceptance': '承兑汇票',
}


class Payment(db.Model):
    """采购付款"""
    __tablename__ = "payments"
    __table_args__ = (
        db.Index('idx_payment_supplier', 'supplier_id'),
        db.Index('idx_payment_po', 'po_id'),
        db.Index('idx_payment_status', 'status'),
        db.Index('idx_payment_date', 'payment_date'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    payment_number = db.Column(VARCHAR(50), unique=True, nullable=False, index=True)

    # 关联信息
    supplier_id = db.Column(BIGINT(unsigned=True), ForeignKey('suppliers.id'), nullable=False)
    supplier_name = db.Column(VARCHAR(200), nullable=False)
    po_id = db.Column(BIGINT(unsigned=True), nullable=True)  # 关联PO
    po_number = db.Column(VARCHAR(50), nullable=True)
    invoice_id = db.Column(BIGINT(unsigned=True), nullable=True)  # 关联发票
    invoice_number = db.Column(VARCHAR(50), nullable=True)
    contract_id = db.Column(BIGINT(unsigned=True), nullable=True)  # 关联合同
    contract_number = db.Column(VARCHAR(50), nullable=True)

    # 付款基本信息
    payment_type = db.Column(VARCHAR(20), nullable=False, default='full')
    payment_method = db.Column(VARCHAR(20), nullable=False, default='bank_transfer')
    currency = db.Column(VARCHAR(10), nullable=False, default='CNY')

    # 金额信息
    amount = db.Column(DECIMAL(14, 2), nullable=False)  # 付款金额
    tax_amount = db.Column(DECIMAL(14, 2), nullable=False, default=0)  # 税额
    total_amount = db.Column(DECIMAL(14, 2), nullable=False)  # 总金额（含税）

    # 付款日期
    due_date = db.Column(DATE, nullable=True)  # 应付日期
    payment_date = db.Column(DATE, nullable=True)  # 实际付款日期

    # 银行信息
    bank_name = db.Column(VARCHAR(100), nullable=True)
    bank_account = db.Column(VARCHAR(50), nullable=True)
    bank_account_name = db.Column(VARCHAR(100), nullable=True)

    # 状态
    status = db.Column(VARCHAR(30), nullable=False, default='draft')

    # 审批信息
    submitted_by = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=True)
    submitted_at = db.Column(DATETIME, nullable=True)
    approved_by = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(DATETIME, nullable=True)
    approval_note = db.Column(TEXT, nullable=True)

    # 付款凭证
    voucher_number = db.Column(VARCHAR(50), nullable=True)  # 凭证号
    voucher_path = db.Column(VARCHAR(500), nullable=True)  # 凭证附件

    # 创建/更新信息
    created_by = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=True)
    created_at = db.Column(DATETIME, default=datetime.utcnow)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 备注
    remarks = db.Column(TEXT, nullable=True)

    # 关系
    supplier = relationship("Supplier", foreign_keys=[supplier_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    submitted_by_user = relationship("User", foreign_keys=[submitted_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f'<Payment {self.payment_number}>'

    @staticmethod
    def generate_payment_number():
        """生成付款编号"""
        today = datetime.utcnow()
        prefix = f'PAY-{today.strftime("%Y%m%d")}'

        # 获取今日序号
        count = Payment.query.filter(
            Payment.payment_number.like(f'{prefix}%')
        ).count()
        seq = str(count + 1).zfill(4)

        return f'{prefix}-{seq}'

    @property
    def is_overdue(self):
        """是否逾期"""
        if not self.due_date:
            return False
        if self.status == 'paid':
            return False
        return datetime.utcnow().date() > self.due_date

    @property
    def days_until_due(self):
        """距离到期天数"""
        if not self.due_date:
            return None
        delta = self.due_date - datetime.utcnow().date()
        return delta.days

    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'payment_number': self.payment_number,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'po_id': self.po_id,
            'po_number': self.po_number,
            'invoice_id': self.invoice_id,
            'invoice_number': self.invoice_number,
            'contract_id': self.contract_id,
            'contract_number': self.contract_number,
            'payment_type': self.payment_type,
            'payment_type_label': PAYMENT_TYPE_LABELS.get(self.payment_type, self.payment_type),
            'payment_method': self.payment_method,
            'payment_method_label': PAYMENT_METHOD_LABELS.get(self.payment_method, self.payment_method),
            'currency': self.currency,
            'amount': float(self.amount) if self.amount else 0,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'bank_name': self.bank_name,
            'bank_account': self.bank_account,
            'bank_account_name': self.bank_account_name,
            'status': self.status,
            'status_label': PAYMENT_STATUS_LABELS.get(self.status, self.status),
            'is_overdue': self.is_overdue,
            'days_until_due': self.days_until_due,
            'submitted_by': self.submitted_by,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approval_note': self.approval_note,
            'voucher_number': self.voucher_number,
            'voucher_path': self.voucher_path,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'remarks': self.remarks,
        }


class PaymentPlan(db.Model):
    """付款计划"""
    __tablename__ = "payment_plans"
    __table_args__ = (
        db.Index('idx_payment_plan_po', 'po_id'),
        db.Index('idx_payment_plan_contract', 'contract_id'),
        db.Index('idx_payment_plan_due', 'due_date'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)

    # 关联信息
    po_id = db.Column(BIGINT(unsigned=True), nullable=True)
    po_number = db.Column(VARCHAR(50), nullable=True)
    contract_id = db.Column(BIGINT(unsigned=True), nullable=True)
    contract_number = db.Column(VARCHAR(50), nullable=True)
    supplier_id = db.Column(BIGINT(unsigned=True), ForeignKey('suppliers.id'), nullable=False)
    supplier_name = db.Column(VARCHAR(200), nullable=False)

    # 计划信息
    plan_name = db.Column(VARCHAR(200), nullable=False)
    payment_type = db.Column(VARCHAR(20), nullable=False)  # 付款类型
    percentage = db.Column(DECIMAL(5, 2), nullable=True)  # 付款比例（%）
    amount = db.Column(DECIMAL(14, 2), nullable=False)  # 计划金额
    currency = db.Column(VARCHAR(10), nullable=False, default='CNY')

    # 日期
    due_date = db.Column(DATE, nullable=False)  # 计划付款日期
    condition = db.Column(VARCHAR(200), nullable=True)  # 付款条件

    # 关联实际付款
    payment_id = db.Column(BIGINT(unsigned=True), ForeignKey('payments.id'), nullable=True)
    actual_amount = db.Column(DECIMAL(14, 2), nullable=True)  # 实际付款金额
    actual_date = db.Column(DATE, nullable=True)  # 实际付款日期

    # 状态
    is_completed = db.Column(db.Boolean, nullable=False, default=False)

    # 时间戳
    created_at = db.Column(DATETIME, default=datetime.utcnow)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 备注
    remarks = db.Column(TEXT, nullable=True)

    # 关系
    payment = relationship("Payment", foreign_keys=[payment_id])

    def __repr__(self):
        return f'<PaymentPlan {self.plan_name}>'

    @property
    def is_overdue(self):
        """是否逾期"""
        if self.is_completed:
            return False
        return datetime.utcnow().date() > self.due_date

    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'po_id': self.po_id,
            'po_number': self.po_number,
            'contract_id': self.contract_id,
            'contract_number': self.contract_number,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'plan_name': self.plan_name,
            'payment_type': self.payment_type,
            'payment_type_label': PAYMENT_TYPE_LABELS.get(self.payment_type, self.payment_type),
            'percentage': float(self.percentage) if self.percentage else None,
            'amount': float(self.amount) if self.amount else 0,
            'currency': self.currency,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'condition': self.condition,
            'payment_id': self.payment_id,
            'actual_amount': float(self.actual_amount) if self.actual_amount else None,
            'actual_date': self.actual_date.isoformat() if self.actual_date else None,
            'is_completed': self.is_completed,
            'is_overdue': self.is_overdue,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'remarks': self.remarks,
        }
