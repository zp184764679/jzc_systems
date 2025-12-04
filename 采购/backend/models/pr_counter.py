# -*- coding: utf-8 -*-
from extensions import db
from sqlalchemy.dialects.mysql import BIGINT, VARCHAR

class PRCounter(db.Model):
    __tablename__ = "pr_counters"

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    # 形如 “20251027”，作为当天的计数 key；唯一保证同一天只一条计数器
    date_key = db.Column(VARCHAR(8), unique=True, nullable=False, index=True)
    # 当天已用序号
    seq = db.Column(BIGINT(unsigned=True), nullable=False, default=0)

