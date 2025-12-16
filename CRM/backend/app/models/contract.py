# -*- coding: utf-8 -*-
"""
合同管理模型
包含: 合同、合同明细、合同审批
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional
import enum

from sqlalchemy import Index, func
from sqlalchemy.dialects.mysql import JSON

from .. import db


class ContractStatus(enum.Enum):
    """合同状态枚举"""
    DRAFT = "draft"           # 草稿
    PENDING = "pending"       # 待审批
    APPROVED = "approved"     # 已批准
    ACTIVE = "active"         # 生效中
    EXPIRED = "expired"       # 已过期
    TERMINATED = "terminated" # 已终止


class ContractType(enum.Enum):
    """合同类型枚举"""
    SALES = "sales"           # 销售合同
    FRAMEWORK = "framework"   # 框架协议
    SERVICE = "service"       # 服务合同
    NDA = "nda"               # 保密协议
    OTHER = "other"           # 其他


class ApprovalStatus(enum.Enum):
    """审批状态枚举"""
    PENDING = "pending"       # 待审批
    APPROVED = "approved"     # 已通过
    REJECTED = "rejected"     # 已拒绝


class Contract(db.Model):
    """合同主表"""
    __tablename__ = "crm_contracts"

    id = db.Column(db.Integer, primary_key=True)

    # 合同编号（自动生成）
    contract_no = db.Column(db.String(32), unique=True, nullable=False, index=True)

    # 基本信息
    name = db.Column(db.String(200), nullable=False)              # 合同名称
    contract_type = db.Column(db.String(32), default=ContractType.SALES.value)  # 合同类型
    status = db.Column(db.String(32), default=ContractStatus.DRAFT.value, index=True)

    # 客户信息
    customer_id = db.Column(db.Integer, index=True, nullable=False)  # 客户ID
    customer_name = db.Column(db.String(200))                        # 客户名称（冗余）

    # 关联销售机会
    opportunity_id = db.Column(db.Integer, index=True)               # 关联机会ID（可选）

    # 金额
    total_amount = db.Column(db.Numeric(14, 2), default=0)           # 合同总金额
    currency = db.Column(db.String(8), default='CNY')                # 币种
    tax_rate = db.Column(db.Numeric(5, 2), default=13)               # 税率 (%)

    # 日期
    start_date = db.Column(db.Date)                                  # 合同开始日期
    end_date = db.Column(db.Date)                                    # 合同结束日期
    sign_date = db.Column(db.Date)                                   # 签订日期

    # 签约方
    our_signatory = db.Column(db.String(64))                         # 我方签约人
    customer_signatory = db.Column(db.String(64))                    # 客户签约人

    # 条款
    payment_terms = db.Column(db.Text)                               # 付款条款
    delivery_terms = db.Column(db.Text)                              # 交货条款
    special_terms = db.Column(db.Text)                               # 特殊条款

    # 附件
    attachments = db.Column(JSON, default=list)                      # 附件列表

    # 负责人
    owner_id = db.Column(db.Integer, index=True)                     # 负责人ID
    owner_name = db.Column(db.String(64))                            # 负责人姓名（冗余）

    # 备注
    remark = db.Column(db.Text)

    # 审计字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer)

    # 索引
    __table_args__ = (
        Index("idx_contract_customer", "customer_id"),
        Index("idx_contract_status_date", "status", "end_date"),
        Index("idx_contract_owner", "owner_id"),
    )

    # 关系
    items = db.relationship('ContractItem', backref='contract', lazy='dynamic', cascade='all, delete-orphan')
    approvals = db.relationship('ContractApproval', backref='contract', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_items=False, include_approvals=False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "contract_no": self.contract_no,
            "name": self.name,
            "contract_type": self.contract_type,
            "status": self.status,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "opportunity_id": self.opportunity_id,
            "total_amount": float(self.total_amount or 0),
            "currency": self.currency,
            "tax_rate": float(self.tax_rate or 0),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "sign_date": self.sign_date.isoformat() if self.sign_date else None,
            "our_signatory": self.our_signatory,
            "customer_signatory": self.customer_signatory,
            "payment_terms": self.payment_terms,
            "delivery_terms": self.delivery_terms,
            "special_terms": self.special_terms,
            "attachments": self.attachments or [],
            "owner_id": self.owner_id,
            "owner_name": self.owner_name,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }

        if include_items:
            data["items"] = [item.to_dict() for item in self.items.all()]

        if include_approvals:
            data["approvals"] = [a.to_dict() for a in self.approvals.order_by(ContractApproval.created_at.desc()).all()]

        return data

    @staticmethod
    def generate_contract_no() -> str:
        """生成合同编号: CON-YYYYMMDD-XXXX"""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"CON-{today}-"

        # 获取今日最大编号
        last = Contract.query.filter(
            Contract.contract_no.like(f"{prefix}%")
        ).order_by(Contract.contract_no.desc()).first()

        if last:
            try:
                last_num = int(last.contract_no.split("-")[-1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"

    def calculate_total(self):
        """计算合同总金额（根据明细）"""
        total = db.session.query(
            func.coalesce(func.sum(ContractItem.amount), 0)
        ).filter(ContractItem.contract_id == self.id).scalar()
        self.total_amount = total or 0

    def is_expiring_soon(self, days=30) -> bool:
        """检查合同是否即将到期"""
        if not self.end_date or self.status != ContractStatus.ACTIVE.value:
            return False
        from datetime import timedelta
        return date.today() <= self.end_date <= date.today() + timedelta(days=days)

    def is_expired(self) -> bool:
        """检查合同是否已过期"""
        if not self.end_date:
            return False
        return self.end_date < date.today()


class ContractItem(db.Model):
    """合同明细"""
    __tablename__ = "crm_contract_items"

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('crm_contracts.id'), nullable=False, index=True)

    # 产品/服务信息
    product_name = db.Column(db.String(200), nullable=False)         # 产品/服务名称
    specification = db.Column(db.String(500))                        # 规格型号

    # 数量与金额
    quantity = db.Column(db.Numeric(12, 2), default=1)               # 数量
    unit = db.Column(db.String(32), default='个')                    # 单位
    unit_price = db.Column(db.Numeric(14, 4), default=0)             # 单价
    amount = db.Column(db.Numeric(14, 2), default=0)                 # 金额

    # 交货信息
    delivery_date = db.Column(db.Date)                               # 交货日期

    # 备注
    remark = db.Column(db.String(500))

    # 排序
    sort_order = db.Column(db.Integer, default=0)

    # 审计
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "product_name": self.product_name,
            "specification": self.specification,
            "quantity": float(self.quantity or 0),
            "unit": self.unit,
            "unit_price": float(self.unit_price or 0),
            "amount": float(self.amount or 0),
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "remark": self.remark,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def calculate_amount(self):
        """计算金额"""
        if self.quantity and self.unit_price:
            self.amount = Decimal(str(self.quantity)) * Decimal(str(self.unit_price))
        else:
            self.amount = 0


class ContractApproval(db.Model):
    """合同审批记录"""
    __tablename__ = "crm_contract_approvals"

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('crm_contracts.id'), nullable=False, index=True)

    # 审批人
    approver_id = db.Column(db.Integer, nullable=False)              # 审批人ID
    approver_name = db.Column(db.String(64))                         # 审批人姓名

    # 审批信息
    status = db.Column(db.String(32), default=ApprovalStatus.PENDING.value)  # 审批状态
    comment = db.Column(db.Text)                                     # 审批意见

    # 时间
    approved_at = db.Column(db.DateTime)                             # 审批时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "approver_id": self.approver_id,
            "approver_name": self.approver_name,
            "status": self.status,
            "comment": self.comment,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# 合同类型名称映射
CONTRACT_TYPE_MAP = {
    ContractType.SALES.value: "销售合同",
    ContractType.FRAMEWORK.value: "框架协议",
    ContractType.SERVICE.value: "服务合同",
    ContractType.NDA.value: "保密协议",
    ContractType.OTHER.value: "其他",
}

# 合同状态名称映射
CONTRACT_STATUS_MAP = {
    ContractStatus.DRAFT.value: "草稿",
    ContractStatus.PENDING.value: "待审批",
    ContractStatus.APPROVED.value: "已批准",
    ContractStatus.ACTIVE.value: "生效中",
    ContractStatus.EXPIRED.value: "已过期",
    ContractStatus.TERMINATED.value: "已终止",
}

# 审批状态名称映射
APPROVAL_STATUS_MAP = {
    ApprovalStatus.PENDING.value: "待审批",
    ApprovalStatus.APPROVED.value: "已通过",
    ApprovalStatus.REJECTED.value: "已拒绝",
}
