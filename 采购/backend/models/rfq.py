# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, VARCHAR, TEXT
from extensions import db


class RFQ(db.Model):
    __tablename__ = "rfqs"
    __table_args__ = (
        db.Index('idx_rfqs_pr_id', 'pr_id'),
        db.Index('idx_rfqs_status', 'status'),
        db.Index('idx_rfqs_created_at', 'created_at'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    pr_id = db.Column(BIGINT(unsigned=True), ForeignKey('pr.id'), nullable=False)
    
    # draft/pending/sent/collecting/closed
    status = db.Column(VARCHAR(20), nullable=False, default='draft')
    
    note = db.Column(TEXT, nullable=True)
    payment_terms = db.Column(db.Integer, default=90, nullable=False, comment='付款周期(天)')
    created_by = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=True)
    created_at = db.Column(DATETIME, default=datetime.utcnow)
    sent_at = db.Column(DATETIME, nullable=True)
    closed_at = db.Column(DATETIME, nullable=True)

    # 分类状态追踪
    classification_status = db.Column(VARCHAR(20), nullable=True, comment='分类状态: pending/processing/completed/failed')
    classification_task_id = db.Column(VARCHAR(100), nullable=True, comment='Celery任务ID')
    classification_started_at = db.Column(DATETIME, nullable=True, comment='分类开始时间')
    classification_completed_at = db.Column(DATETIME, nullable=True, comment='分类完成时间')

    # 关系
    pr = relationship("PR", backref="rfqs")
    created_user = relationship("User", foreign_keys=[created_by])
    items = relationship("RFQItem", back_populates="rfq", cascade="all, delete-orphan")
    notification_tasks = relationship("RFQNotificationTask", back_populates="rfq", cascade="all, delete-orphan")
    quotes = relationship("SupplierQuote", back_populates="rfq", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<RFQ {self.id}: PR#{self.pr_id}>'
