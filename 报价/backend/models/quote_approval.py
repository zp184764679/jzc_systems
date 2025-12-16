# models/quote_approval.py
"""
报价审批模型
- 支持多级审批流程
- 记录审批历史
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
import enum


class ApprovalAction(enum.Enum):
    """审批动作"""
    SUBMIT = "submit"           # 提交审核
    APPROVE = "approve"         # 批准
    REJECT = "reject"           # 拒绝
    REVISE = "revise"           # 退回修改
    SEND = "send"               # 发送给客户
    WITHDRAW = "withdraw"       # 撤回


class QuoteApproval(Base):
    """报价审批记录"""
    __tablename__ = "quote_approvals"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True, comment="报价单ID")

    # 审批动作
    action = Column(String(20), nullable=False, comment="审批动作: submit/approve/reject/revise/send/withdraw")

    # 状态变更
    from_status = Column(String(20), comment="原状态")
    to_status = Column(String(20), comment="新状态")

    # 审批人信息
    approver_id = Column(Integer, comment="审批人ID")
    approver_name = Column(String(50), comment="审批人姓名")
    approver_role = Column(String(50), comment="审批人角色")

    # 审批意见
    comment = Column(Text, comment="审批意见")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="操作时间")

    def __repr__(self):
        return f"<QuoteApproval(quote_id={self.quote_id}, action={self.action})>"

    def to_dict(self):
        return {
            "id": self.id,
            "quote_id": self.quote_id,
            "action": self.action,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "approver_id": self.approver_id,
            "approver_name": self.approver_name,
            "approver_role": self.approver_role,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# 报价状态常量
class QuoteStatus:
    DRAFT = "draft"                     # 草稿
    PENDING_REVIEW = "pending_review"   # 待审核
    APPROVED = "approved"               # 已批准
    REJECTED = "rejected"               # 已拒绝
    SENT = "sent"                       # 已发送客户
    EXPIRED = "expired"                 # 已过期

    @classmethod
    def get_all(cls):
        return [cls.DRAFT, cls.PENDING_REVIEW, cls.APPROVED, cls.REJECTED, cls.SENT, cls.EXPIRED]

    @classmethod
    def get_display_name(cls, status):
        names = {
            cls.DRAFT: "草稿",
            cls.PENDING_REVIEW: "待审核",
            cls.APPROVED: "已批准",
            cls.REJECTED: "已拒绝",
            cls.SENT: "已发送",
            cls.EXPIRED: "已过期",
        }
        return names.get(status, status)


# 状态流转规则
QUOTE_STATUS_TRANSITIONS = {
    QuoteStatus.DRAFT: [QuoteStatus.PENDING_REVIEW],                                    # 草稿 → 待审核
    QuoteStatus.PENDING_REVIEW: [QuoteStatus.APPROVED, QuoteStatus.REJECTED, QuoteStatus.DRAFT],  # 待审核 → 批准/拒绝/退回
    QuoteStatus.APPROVED: [QuoteStatus.SENT, QuoteStatus.DRAFT],                        # 已批准 → 已发送/退回修改
    QuoteStatus.REJECTED: [QuoteStatus.DRAFT],                                          # 已拒绝 → 草稿（修改后重新提交）
    QuoteStatus.SENT: [],                                                               # 已发送 → 终态
    QuoteStatus.EXPIRED: [],                                                            # 已过期 → 终态
}


def can_transition(from_status: str, to_status: str) -> bool:
    """检查状态是否可以转换"""
    allowed = QUOTE_STATUS_TRANSITIONS.get(from_status, [])
    return to_status in allowed
