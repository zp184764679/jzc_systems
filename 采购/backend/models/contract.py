# -*- coding: utf-8 -*-
"""
采购合同模型
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, VARCHAR, TEXT, DECIMAL, DATE
from extensions import db


class ContractStatus(Enum):
    """合同状态"""
    DRAFT = 'draft'                    # 草稿
    PENDING_APPROVAL = 'pending_approval'  # 待审批
    APPROVED = 'approved'              # 已批准
    ACTIVE = 'active'                  # 执行中
    COMPLETED = 'completed'            # 已完成
    CANCELLED = 'cancelled'            # 已取消
    EXPIRED = 'expired'                # 已过期


class ContractType(Enum):
    """合同类型"""
    FRAMEWORK = 'framework'            # 框架合同
    SINGLE = 'single'                  # 单次采购
    LONG_TERM = 'long_term'           # 长期合同
    ANNUAL = 'annual'                  # 年度合同


CONTRACT_STATUS_LABELS = {
    'draft': '草稿',
    'pending_approval': '待审批',
    'approved': '已批准',
    'active': '执行中',
    'completed': '已完成',
    'cancelled': '已取消',
    'expired': '已过期',
}

CONTRACT_TYPE_LABELS = {
    'framework': '框架合同',
    'single': '单次采购',
    'long_term': '长期合同',
    'annual': '年度合同',
}


class Contract(db.Model):
    """采购合同"""
    __tablename__ = "contracts"
    __table_args__ = (
        db.Index('idx_contract_supplier_id', 'supplier_id'),
        db.Index('idx_contract_status', 'status'),
        db.Index('idx_contract_type', 'contract_type'),
        db.Index('idx_contract_start_date', 'start_date'),
        db.Index('idx_contract_end_date', 'end_date'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    contract_number = db.Column(VARCHAR(50), unique=True, nullable=False, index=True)

    # 基本信息
    title = db.Column(VARCHAR(200), nullable=False)
    contract_type = db.Column(VARCHAR(20), nullable=False, default='single')

    # 供应商
    supplier_id = db.Column(BIGINT(unsigned=True), ForeignKey('suppliers.id'), nullable=False)
    supplier_name = db.Column(VARCHAR(200), nullable=False)

    # 金额
    total_amount = db.Column(DECIMAL(14, 2), nullable=False, default=0)
    executed_amount = db.Column(DECIMAL(14, 2), nullable=False, default=0)  # 已执行金额
    currency = db.Column(VARCHAR(10), nullable=False, default='CNY')

    # 有效期
    start_date = db.Column(DATE, nullable=False)
    end_date = db.Column(DATE, nullable=False)

    # 关联采购订单（可选）
    po_id = db.Column(BIGINT(unsigned=True), ForeignKey('purchase_orders.id'), nullable=True)

    # 合同条款
    payment_terms = db.Column(TEXT, nullable=True)       # 付款条款
    delivery_terms = db.Column(TEXT, nullable=True)      # 交付条款
    warranty_terms = db.Column(TEXT, nullable=True)      # 质保条款
    penalty_clause = db.Column(TEXT, nullable=True)      # 违约条款
    other_terms = db.Column(TEXT, nullable=True)         # 其他条款

    # 附件
    attachment_path = db.Column(VARCHAR(500), nullable=True)  # 合同附件路径

    # 状态
    status = db.Column(VARCHAR(30), nullable=False, default='draft')

    # 审批信息
    submitted_by = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=True)
    submitted_at = db.Column(DATETIME, nullable=True)
    approved_by = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(DATETIME, nullable=True)
    approval_note = db.Column(TEXT, nullable=True)

    # 创建/更新信息
    created_by = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=True)
    created_at = db.Column(DATETIME, default=datetime.utcnow)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 备注
    remarks = db.Column(TEXT, nullable=True)

    # 关系
    supplier = relationship("Supplier", backref="contracts")
    purchase_order = relationship("PurchaseOrder", backref="contracts", foreign_keys=[po_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    submitted_by_user = relationship("User", foreign_keys=[submitted_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    items = relationship("ContractItem", back_populates="contract", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Contract {self.contract_number}>'

    @staticmethod
    def generate_contract_number():
        """生成合同编号：CT-YYYYMMDD-XXXXX"""
        today = datetime.utcnow().strftime('%Y%m%d')
        count = Contract.query.filter(
            db.func.DATE(Contract.created_at) == datetime.utcnow().date()
        ).count()
        seq = str(count + 1).zfill(5)
        return f'CT-{today}-{seq}'

    def to_dict(self, include_items=False):
        """序列化为字典"""
        result = {
            'id': self.id,
            'contract_number': self.contract_number,
            'title': self.title,
            'contract_type': self.contract_type,
            'contract_type_label': CONTRACT_TYPE_LABELS.get(self.contract_type, self.contract_type),
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'executed_amount': float(self.executed_amount) if self.executed_amount else 0,
            'remaining_amount': float(self.total_amount - self.executed_amount) if self.total_amount else 0,
            'execution_rate': round(float(self.executed_amount) / float(self.total_amount) * 100, 2) if self.total_amount and self.total_amount > 0 else 0,
            'currency': self.currency,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'po_id': self.po_id,
            'payment_terms': self.payment_terms,
            'delivery_terms': self.delivery_terms,
            'warranty_terms': self.warranty_terms,
            'penalty_clause': self.penalty_clause,
            'other_terms': self.other_terms,
            'attachment_path': self.attachment_path,
            'status': self.status,
            'status_label': CONTRACT_STATUS_LABELS.get(self.status, self.status),
            'submitted_by': self.submitted_by,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approval_note': self.approval_note,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'remarks': self.remarks,
            'is_expired': self.end_date < datetime.utcnow().date() if self.end_date else False,
            'days_remaining': (self.end_date - datetime.utcnow().date()).days if self.end_date else None,
        }

        if include_items and self.items:
            result['items'] = [item.to_dict() for item in self.items]

        return result


class ContractItem(db.Model):
    """合同明细"""
    __tablename__ = "contract_items"
    __table_args__ = (
        db.Index('idx_contract_item_contract_id', 'contract_id'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    contract_id = db.Column(BIGINT(unsigned=True), ForeignKey('contracts.id'), nullable=False)

    # 物料信息
    material_code = db.Column(VARCHAR(50), nullable=True)
    material_name = db.Column(VARCHAR(200), nullable=False)
    specification = db.Column(VARCHAR(200), nullable=True)
    unit = db.Column(VARCHAR(20), nullable=True)

    # 数量和价格
    quantity = db.Column(DECIMAL(12, 2), nullable=False, default=0)
    unit_price = db.Column(DECIMAL(12, 4), nullable=False, default=0)
    amount = db.Column(DECIMAL(14, 2), nullable=False, default=0)

    # 已执行数量
    executed_quantity = db.Column(DECIMAL(12, 2), nullable=False, default=0)

    # 备注
    remarks = db.Column(TEXT, nullable=True)

    # 时间戳
    created_at = db.Column(DATETIME, default=datetime.utcnow)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    contract = relationship("Contract", back_populates="items")

    def __repr__(self):
        return f'<ContractItem {self.material_name}>'

    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'contract_id': self.contract_id,
            'material_code': self.material_code,
            'material_name': self.material_name,
            'specification': self.specification,
            'unit': self.unit,
            'quantity': float(self.quantity) if self.quantity else 0,
            'unit_price': float(self.unit_price) if self.unit_price else 0,
            'amount': float(self.amount) if self.amount else 0,
            'executed_quantity': float(self.executed_quantity) if self.executed_quantity else 0,
            'remaining_quantity': float(self.quantity - self.executed_quantity) if self.quantity else 0,
            'execution_rate': round(float(self.executed_quantity) / float(self.quantity) * 100, 2) if self.quantity and self.quantity > 0 else 0,
            'remarks': self.remarks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
