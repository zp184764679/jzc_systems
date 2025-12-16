# -*- coding: utf-8 -*-
"""
销售机会与客户跟进模型
包含: 销售机会(商机)、销售阶段历史、客户跟进记录
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import enum

from sqlalchemy import Index, func
from sqlalchemy.dialects.mysql import JSON

from .. import db


class OpportunityStage(enum.Enum):
    """销售阶段枚举"""
    LEAD = "lead"                    # 线索
    QUALIFIED = "qualified"          # 已确认
    PROPOSAL = "proposal"            # 方案阶段
    NEGOTIATION = "negotiation"      # 商务谈判
    CLOSED_WON = "closed_won"        # 成交
    CLOSED_LOST = "closed_lost"      # 丢单


class OpportunityPriority(enum.Enum):
    """机会优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class FollowUpType(enum.Enum):
    """跟进类型"""
    PHONE = "phone"                  # 电话
    VISIT = "visit"                  # 拜访
    EMAIL = "email"                  # 邮件
    WECHAT = "wechat"                # 微信
    MEETING = "meeting"              # 会议
    QUOTATION = "quotation"          # 报价
    SAMPLE = "sample"                # 样品
    OTHER = "other"                  # 其他


class SalesOpportunity(db.Model):
    """销售机会/商机"""
    __tablename__ = "crm_opportunities"

    id = db.Column(db.Integer, primary_key=True)

    # 机会编号（自动生成）
    opportunity_no = db.Column(db.String(32), unique=True, nullable=False, index=True)

    # 基本信息
    name = db.Column(db.String(200), nullable=False)              # 机会名称
    customer_id = db.Column(db.Integer, index=True, nullable=False)  # 客户ID
    customer_name = db.Column(db.String(200))                     # 客户名称（冗余）

    # 销售阶段
    stage = db.Column(db.String(32), default=OpportunityStage.LEAD.value, index=True)

    # 金额与概率
    expected_amount = db.Column(db.Numeric(14, 2), default=0)     # 预计金额
    currency = db.Column(db.String(8), default='CNY')             # 币种
    probability = db.Column(db.Integer, default=10)               # 成交概率 (0-100)
    weighted_amount = db.Column(db.Numeric(14, 2), default=0)     # 加权金额

    # 日期
    expected_close_date = db.Column(db.Date)                      # 预计成交日期
    actual_close_date = db.Column(db.Date)                        # 实际成交日期

    # 负责人
    owner_id = db.Column(db.Integer, index=True)                  # 负责人ID
    owner_name = db.Column(db.String(64))                         # 负责人姓名（冗余）

    # 优先级与来源
    priority = db.Column(db.String(16), default=OpportunityPriority.MEDIUM.value)
    source = db.Column(db.String(64))                             # 机会来源

    # 产品信息
    product_interest = db.Column(db.Text)                         # 意向产品

    # 竞争对手
    competitors = db.Column(db.Text)                              # 竞争对手

    # 备注
    description = db.Column(db.Text)                              # 详细描述
    win_reason = db.Column(db.Text)                               # 赢单原因
    loss_reason = db.Column(db.Text)                              # 丢单原因

    # 关联订单
    order_id = db.Column(db.Integer)                              # 转化的订单ID

    # 下次跟进
    next_follow_up_date = db.Column(db.Date)                      # 下次跟进日期
    next_follow_up_note = db.Column(db.String(500))               # 下次跟进内容

    # 审计字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer)

    # 索引
    __table_args__ = (
        Index("idx_opp_customer_stage", "customer_id", "stage"),
        Index("idx_opp_owner_stage", "owner_id", "stage"),
        Index("idx_opp_expected_close", "expected_close_date"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_no": self.opportunity_no,
            "name": self.name,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "stage": self.stage,
            "expected_amount": float(self.expected_amount or 0),
            "currency": self.currency,
            "probability": self.probability,
            "weighted_amount": float(self.weighted_amount or 0),
            "expected_close_date": self.expected_close_date.isoformat() if self.expected_close_date else None,
            "actual_close_date": self.actual_close_date.isoformat() if self.actual_close_date else None,
            "owner_id": self.owner_id,
            "owner_name": self.owner_name,
            "priority": self.priority,
            "source": self.source,
            "product_interest": self.product_interest,
            "competitors": self.competitors,
            "description": self.description,
            "win_reason": self.win_reason,
            "loss_reason": self.loss_reason,
            "order_id": self.order_id,
            "next_follow_up_date": self.next_follow_up_date.isoformat() if self.next_follow_up_date else None,
            "next_follow_up_note": self.next_follow_up_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }

    @staticmethod
    def generate_opportunity_no() -> str:
        """生成机会编号: OPP-YYYYMMDD-XXXX"""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"OPP-{today}-"

        # 获取今日最大编号
        last = SalesOpportunity.query.filter(
            SalesOpportunity.opportunity_no.like(f"{prefix}%")
        ).order_by(SalesOpportunity.opportunity_no.desc()).first()

        if last:
            try:
                last_num = int(last.opportunity_no.split("-")[-1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"

    def update_weighted_amount(self):
        """更新加权金额"""
        if self.expected_amount and self.probability:
            self.weighted_amount = Decimal(str(self.expected_amount)) * Decimal(str(self.probability)) / 100
        else:
            self.weighted_amount = 0


class OpportunityStageHistory(db.Model):
    """销售阶段变更历史"""
    __tablename__ = "crm_opportunity_stage_history"

    id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('crm_opportunities.id'), nullable=False, index=True)

    from_stage = db.Column(db.String(32))                         # 原阶段
    to_stage = db.Column(db.String(32), nullable=False)           # 新阶段

    changed_by = db.Column(db.Integer)                            # 变更人ID
    changed_by_name = db.Column(db.String(64))                    # 变更人姓名
    change_reason = db.Column(db.Text)                            # 变更原因

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 关系
    opportunity = db.relationship('SalesOpportunity', backref='stage_history')

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "changed_by": self.changed_by,
            "changed_by_name": self.changed_by_name,
            "change_reason": self.change_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FollowUpRecord(db.Model):
    """客户跟进记录"""
    __tablename__ = "crm_follow_up_records"

    id = db.Column(db.Integer, primary_key=True)

    # 关联
    customer_id = db.Column(db.Integer, index=True, nullable=False)    # 客户ID
    customer_name = db.Column(db.String(200))                          # 客户名称（冗余）
    opportunity_id = db.Column(db.Integer, index=True)                 # 关联机会（可选）

    # 跟进信息
    follow_up_type = db.Column(db.String(32), default=FollowUpType.PHONE.value)  # 跟进方式
    follow_up_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # 跟进时间

    # 内容
    subject = db.Column(db.String(200))                               # 主题
    content = db.Column(db.Text, nullable=False)                      # 跟进内容
    result = db.Column(db.Text)                                       # 跟进结果

    # 联系人
    contact_name = db.Column(db.String(64))                           # 联系人
    contact_phone = db.Column(db.String(32))                          # 联系电话
    contact_role = db.Column(db.String(64))                           # 联系人职位

    # 下次跟进
    next_follow_up_date = db.Column(db.Date)                          # 下次跟进日期
    next_follow_up_note = db.Column(db.String(500))                   # 下次跟进内容

    # 负责人
    owner_id = db.Column(db.Integer, index=True)                      # 跟进人ID
    owner_name = db.Column(db.String(64))                             # 跟进人姓名

    # 附件
    attachments = db.Column(JSON, default=list)                       # 附件列表

    # 审计
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 索引
    __table_args__ = (
        Index("idx_followup_customer_date", "customer_id", "follow_up_date"),
        Index("idx_followup_opportunity", "opportunity_id"),
        Index("idx_followup_owner_date", "owner_id", "follow_up_date"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "opportunity_id": self.opportunity_id,
            "follow_up_type": self.follow_up_type,
            "follow_up_date": self.follow_up_date.isoformat() if self.follow_up_date else None,
            "subject": self.subject,
            "content": self.content,
            "result": self.result,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "contact_role": self.contact_role,
            "next_follow_up_date": self.next_follow_up_date.isoformat() if self.next_follow_up_date else None,
            "next_follow_up_note": self.next_follow_up_note,
            "owner_id": self.owner_id,
            "owner_name": self.owner_name,
            "attachments": self.attachments or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# 阶段概率映射
STAGE_PROBABILITY_MAP = {
    OpportunityStage.LEAD.value: 10,
    OpportunityStage.QUALIFIED.value: 25,
    OpportunityStage.PROPOSAL.value: 50,
    OpportunityStage.NEGOTIATION.value: 75,
    OpportunityStage.CLOSED_WON.value: 100,
    OpportunityStage.CLOSED_LOST.value: 0,
}

# 阶段名称映射
STAGE_NAME_MAP = {
    OpportunityStage.LEAD.value: "线索",
    OpportunityStage.QUALIFIED.value: "已确认",
    OpportunityStage.PROPOSAL.value: "方案阶段",
    OpportunityStage.NEGOTIATION.value: "商务谈判",
    OpportunityStage.CLOSED_WON.value: "成交",
    OpportunityStage.CLOSED_LOST.value: "丢单",
}

# 跟进类型名称映射
FOLLOW_UP_TYPE_MAP = {
    FollowUpType.PHONE.value: "电话",
    FollowUpType.VISIT.value: "拜访",
    FollowUpType.EMAIL.value: "邮件",
    FollowUpType.WECHAT.value: "微信",
    FollowUpType.MEETING.value: "会议",
    FollowUpType.QUOTATION.value: "报价",
    FollowUpType.SAMPLE.value: "样品",
    FollowUpType.OTHER.value: "其他",
}

# 优先级名称映射
PRIORITY_NAME_MAP = {
    OpportunityPriority.LOW.value: "低",
    OpportunityPriority.MEDIUM.value: "中",
    OpportunityPriority.HIGH.value: "高",
    OpportunityPriority.URGENT.value: "紧急",
}
