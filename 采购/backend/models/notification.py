# -*- coding: utf-8 -*-
"""
通用通知模型
Generic Notification Model
"""
from datetime import datetime
from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, VARCHAR, TEXT
from extensions import db


class Notification(db.Model):
    """
    通用通知表 - 用于所有类型的系统通知

    支持的通知类型：
    - po_created: 采购订单创建通知（发送给供应商）
    - invoice_approved: 发票审批通过通知（发送给供应商）
    - invoice_rejected: 发票审批驳回通知（发送给供应商）
    - invoice_deadline_reminder: 发票截止日期提醒（发送给供应商）
    """
    __tablename__ = "notifications"
    __table_args__ = (
        Index('idx_notifications_recipient_id', 'recipient_id'),
        Index('idx_notifications_type', 'notification_type'),
        Index('idx_notifications_read', 'is_read'),
        Index('idx_notifications_created_at', 'created_at'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)

    # 接收者（供应商ID或用户ID）
    recipient_id = db.Column(BIGINT(unsigned=True), nullable=False)
    recipient_type = db.Column(VARCHAR(20), nullable=False, default='supplier')  # supplier/user

    # 通知类型
    notification_type = db.Column(VARCHAR(50), nullable=False)  # po_created, invoice_approved, etc.

    # 通知标题和内容
    title = db.Column(VARCHAR(200), nullable=False)
    message = db.Column(TEXT, nullable=False)

    # 关联的业务对象
    related_type = db.Column(VARCHAR(50), nullable=True)  # purchase_order, invoice, etc.
    related_id = db.Column(BIGINT(unsigned=True), nullable=True)

    # 通知数据（JSON格式，存储额外信息）
    data = db.Column(TEXT, nullable=True)

    # 阅读状态
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(DATETIME, nullable=True)

    # 发送状态
    is_sent = db.Column(db.Boolean, default=False, nullable=False)
    sent_at = db.Column(DATETIME, nullable=True)
    send_method = db.Column(VARCHAR(20), nullable=True)  # email, sms, in_app

    # 时间戳
    created_at = db.Column(DATETIME, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Notification {self.id}: {self.notification_type} to {self.recipient_type}#{self.recipient_id}>'

    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'recipient_id': self.recipient_id,
            'recipient_type': self.recipient_type,
            'notification_type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'related_type': self.related_type,
            'related_id': self.related_id,
            'data': self.data,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'is_sent': self.is_sent,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'send_method': self.send_method,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
