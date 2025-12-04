# -*- coding: utf-8 -*-
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, VARCHAR
from sqlalchemy.exc import IntegrityError
from extensions import db
from .pr_counter import PRCounter

"""
PR状态流转：
  submitted → supervisor_approved → price_filled → admin_approved → [super_admin_approved] → completed
  任意阶段可被 rejected
"""

class PR(db.Model):
    __tablename__ = "pr"

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    pr_number = db.Column(VARCHAR(50), unique=True, nullable=False, index=True)
    title = db.Column(VARCHAR(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    urgency = db.Column(VARCHAR(20), nullable=True)  # normal | urgent | critical
    created_by = db.Column(VARCHAR(100), nullable=True)
    created_at = db.Column(DATETIME, default=datetime.utcnow)

    owner_id = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=False)
    status = db.Column(VARCHAR(50), nullable=False, default="submitted")
    # 状态: submitted, supervisor_approved, price_filled, admin_approved,
    #       pending_super_admin, super_admin_approved, completed, rejected

    # 价格相关
    total_amount = db.Column(Numeric(12, 2), nullable=True)  # 总金额
    price_filled_at = db.Column(DATETIME, nullable=True)  # 价格填写时间
    price_filled_by = db.Column(BIGINT(unsigned=True), nullable=True)  # 填写人

    # 审批相关
    supervisor_approved_at = db.Column(DATETIME, nullable=True)
    supervisor_approved_by = db.Column(BIGINT(unsigned=True), nullable=True)
    admin_approved_at = db.Column(DATETIME, nullable=True)
    admin_approved_by = db.Column(BIGINT(unsigned=True), nullable=True)
    super_admin_approved_at = db.Column(DATETIME, nullable=True)
    super_admin_approved_by = db.Column(BIGINT(unsigned=True), nullable=True)
    rejected_at = db.Column(DATETIME, nullable=True)
    rejected_by = db.Column(BIGINT(unsigned=True), nullable=True)
    reject_reason = db.Column(db.Text, nullable=True)

    # 是否需要超管审批（系统自动判断）
    needs_super_admin = db.Column(db.Boolean, default=False)
    auto_approve_reason = db.Column(VARCHAR(200), nullable=True)  # 自动通过原因

    # 关系
    owner = relationship("User", back_populates="prs")
    items = relationship("PRItem", back_populates="pr", cascade="all, delete-orphan")

    def calculate_total_amount(self):
        """计算总金额"""
        total = 0
        for item in self.items:
            if item.total_price:
                total += float(item.total_price)
        self.total_amount = total
        return total

    @staticmethod
    def _today_keys():
        """
        生成两个 key：
        - yymmdd: 展示用（如 251027）
        - yyyymmdd: 计数器用（如 20251027）
        说明：用 UTC 可避免跨时区导致“跨天错号”
        """
        today = datetime.now(timezone.utc).date()
        return today.strftime("%y%m%d"), today.strftime("%Y%m%d")

    @classmethod
    def generate_pr_number(cls):
        """
        并发安全地产生 'YYMMDD + 3位流水'，例如 251027001。
        利用 pr_counters(date_key) 行级锁（MySQL InnoDB）串行递增 seq。
        """
        yymmdd, yyyymmdd = cls._today_keys()

        # 子事务：锁住当日计数器行（InnoDB 下 with_for_update 生效）
        with db.session.begin_nested():
            counter = (PRCounter.query
                       .filter_by(date_key=yyyymmdd)
                       .with_for_update()     # ⬅️ 行级锁
                       .first())
            if not counter:
                counter = PRCounter(date_key=yyyymmdd, seq=0)
                db.session.add(counter)
                db.session.flush()
            counter.seq += 1
            seq = counter.seq

        return f"{yymmdd}{seq:03d}"  # 251027 + 001

    def __repr__(self):
        return f'<PR {self.id}: {self.title}>'
