# -*- coding: utf-8 -*-
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, VARCHAR, TEXT, INTEGER, LONGTEXT
from extensions import db
import json


class RFQItem(db.Model):
    __tablename__ = "rfq_items"
    __table_args__ = (
        db.Index('idx_rfq_items_rfq_id', 'rfq_id'),
        db.Index('idx_rfq_items_pr_item_id', 'pr_item_id'),
        db.Index('idx_rfq_items_category', 'category'),
        db.Index('idx_rfq_items_major_category', 'major_category'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    rfq_id = db.Column(BIGINT(unsigned=True), ForeignKey('rfqs.id'), nullable=False)
    pr_item_id = db.Column(BIGINT(unsigned=True), ForeignKey('pr_item.id'), nullable=False)
    
    # 物料信息快照
    item_name = db.Column(VARCHAR(200), nullable=False)
    item_spec = db.Column(VARCHAR(200), nullable=True)
    quantity = db.Column(INTEGER, nullable=False, default=1)
    unit = db.Column(VARCHAR(50), nullable=True)
    
    # ✅ 分类信息（改进版）
    category = db.Column(VARCHAR(100), nullable=False)  # "刀具/铣削刀具"
    major_category = db.Column(VARCHAR(100), nullable=True)  # ✅ 新增："刀具"
    minor_category = db.Column(VARCHAR(100), nullable=True)  # ✅ 新增："铣削刀具"
    classification_source = db.Column(VARCHAR(20), nullable=False, default='vector')
    classification_score = db.Column(LONGTEXT, nullable=True)

    # 关系
    rfq = relationship("RFQ", back_populates="items")
    pr_item = relationship("PRItem")

    def __repr__(self):
        return f'<RFQItem {self.id}: {self.name}>'

    def set_classification_score(self, score_dict):
        """设置分类分数 - 自动转换为 JSON 字符串"""
        if isinstance(score_dict, dict):
            self.classification_score = json.dumps(score_dict, ensure_ascii=False)
        else:
            self.classification_score = score_dict

    def get_classification_score(self):
        """获取分类分数 - 自动解析 JSON 字符串"""
        if self.classification_score:
            try:
                return json.loads(self.classification_score)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

def to_dict(self):
    return {
        "id": self.id,
        "rfq_id": self.rfq_id,
        "pr_item_id": self.pr_item_id,
        "item_name": self.item_name,
        "item_spec": self.item_spec,
        "quantity": self.quantity,
        "unit": self.unit,
        "category": self.category,
        "major_category": self.major_category,
        "minor_category": self.minor_category,
        "classification_source": self.classification_source,
        "classification_score": self.get_classification_score(),
    }
