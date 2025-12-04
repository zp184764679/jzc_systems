# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, VARCHAR, TEXT
from extensions import db


class SupplierNudge(db.Model):
    __tablename__ = "supplier_nudges"
    __table_args__ = (
        db.Index('idx_sn_task_id', 'task_id'),
        db.Index('idx_sn_status', 'status'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    task_id = db.Column(BIGINT(unsigned=True), ForeignKey('rfq_notification_tasks.id'), nullable=False)
    
    # pending/sent/closed
    status = db.Column(VARCHAR(20), nullable=False, default='pending')
    
    # 催促统计
    nudge_count = db.Column(BIGINT(unsigned=True), nullable=False, default=0)
    max_nudges = db.Column(BIGINT(unsigned=True), nullable=False, default=3)
    
    # 通知内容（采购员/采购经理的企微消息）
    nudge_message = db.Column(TEXT, nullable=True)
    
    # 时间戳
    created_at = db.Column(DATETIME, default=datetime.utcnow)
    last_nudge_at = db.Column(DATETIME, nullable=True)
    closed_at = db.Column(DATETIME, nullable=True)

    # 关系
    task = relationship("RFQNotificationTask")

    def __repr__(self):
        return f'<SupplierNudge {self.id}: Task#{self.task_id}>'
