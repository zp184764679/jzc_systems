# models/pr_item.py
from sqlalchemy import ForeignKey, Integer, String, Text, Numeric
from sqlalchemy.dialects.mysql import BIGINT, VARCHAR
from extensions import db
from sqlalchemy.orm import relationship

class PRItem(db.Model):
    __tablename__ = "pr_item"

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    pr_id = db.Column(BIGINT(unsigned=True), ForeignKey('pr.id'), nullable=False)
    name = db.Column(String(200), nullable=False)
    spec = db.Column(String(200), nullable=True)
    qty = db.Column(Integer, nullable=False, default=1)
    unit = db.Column(VARCHAR(50), nullable=True)
    remark = db.Column(Text, nullable=True)
    status = db.Column(VARCHAR(50), nullable=False, default="pending")
    classification = db.Column(VARCHAR(100), nullable=True)

    # 价格字段
    unit_price = db.Column(Numeric(10, 2), nullable=True)  # 单价
    total_price = db.Column(Numeric(10, 2), nullable=True)  # 小计 = 单价 × 数量

    # 关联 PR 类
    pr = relationship("PR", back_populates="items")

    def calculate_total(self):
        """计算小计"""
        if self.unit_price and self.qty:
            self.total_price = float(self.unit_price) * self.qty
        return self.total_price

    def __repr__(self):
        return f'<PRItem {self.id}: {self.name}>'