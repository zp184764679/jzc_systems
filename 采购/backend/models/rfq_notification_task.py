# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, VARCHAR, TEXT
from extensions import db


class RFQNotificationTask(db.Model):
    __tablename__ = "rfq_notification_tasks"
    __table_args__ = (
        db.Index('idx_rnt_rfq_id', 'rfq_id'),
        db.Index('idx_rnt_supplier_id', 'supplier_id'),
        db.Index('idx_rnt_status', 'status'),
        db.Index('idx_rnt_next_retry_at', 'next_retry_at'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    rfq_id = db.Column(BIGINT(unsigned=True), ForeignKey('rfqs.id'), nullable=False)
    supplier_id = db.Column(BIGINT(unsigned=True), ForeignKey('suppliers.id'), nullable=False)
    
    # 该供应商对应的品类（用于企微消息中展示）
    category = db.Column(VARCHAR(100), nullable=False)
    
    # pending/sent/failed/success
    status = db.Column(VARCHAR(20), nullable=False, default='pending')
    
    # 重试相关
    retry_count = db.Column(BIGINT(unsigned=True), nullable=False, default=0)
    max_retries = db.Column(BIGINT(unsigned=True), nullable=False, default=5)
    error_reason = db.Column(TEXT, nullable=True)
    
    # 企微消息ID（追踪用）
    wecom_msg_id = db.Column(VARCHAR(200), nullable=True)
    
    # 时间戳
    created_at = db.Column(DATETIME, default=datetime.utcnow)
    sent_at = db.Column(DATETIME, nullable=True)
    next_retry_at = db.Column(DATETIME, nullable=True)

    # 关系
    rfq = relationship("RFQ", back_populates="notification_tasks")
    supplier = relationship("Supplier")

    def __repr__(self):
        return f'<RFQNotificationTask {self.id}: RFQ#{self.rfq_id} Supplier#{self.supplier_id}>'
