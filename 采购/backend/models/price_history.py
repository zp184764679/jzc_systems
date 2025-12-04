# models/price_history.py
# -*- coding: utf-8 -*-
"""
历史价格记录表 - 用于价格偏差比对
每次PR完成时，将物料价格记录到此表
"""
from datetime import datetime
from sqlalchemy import String, Numeric, Index
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, VARCHAR
from extensions import db


class PriceHistory(db.Model):
    __tablename__ = "price_history"

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)

    # 物料标识（用于匹配）
    item_name = db.Column(String(200), nullable=False, index=True)
    item_spec = db.Column(String(200), nullable=True)  # 规格

    # 价格信息
    unit_price = db.Column(Numeric(10, 2), nullable=False)  # 单价
    qty = db.Column(db.Integer, nullable=True)  # 采购数量
    unit = db.Column(VARCHAR(50), nullable=True)  # 单位

    # 来源信息
    pr_id = db.Column(BIGINT(unsigned=True), nullable=True)  # 关联的PR
    pr_number = db.Column(VARCHAR(50), nullable=True)  # PR单号
    pr_item_id = db.Column(BIGINT(unsigned=True), nullable=True)  # 关联的PR物料项

    # 时间
    created_at = db.Column(DATETIME, default=datetime.utcnow)

    # 复合索引：加速按名称+规格查询
    __table_args__ = (
        Index('idx_item_name_spec', 'item_name', 'item_spec'),
    )

    @classmethod
    def get_history_prices(cls, item_name: str, item_spec: str = None, limit: int = 10):
        """
        获取指定物料的历史价格记录

        Args:
            item_name: 物料名称
            item_spec: 规格（可选）
            limit: 返回记录数量

        Returns:
            历史价格记录列表
        """
        query = cls.query.filter_by(item_name=item_name)
        if item_spec:
            query = query.filter_by(item_spec=item_spec)
        return query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_average_price(cls, item_name: str, item_spec: str = None) -> float:
        """
        获取指定物料的历史平均价格

        Returns:
            平均价格，如果没有历史记录返回 None
        """
        records = cls.get_history_prices(item_name, item_spec, limit=20)
        if not records:
            return None
        total = sum(float(r.unit_price) for r in records)
        return total / len(records)

    @classmethod
    def check_price_deviation(cls, item_name: str, item_spec: str, new_price: float, threshold: float = 0.05) -> dict:
        """
        检查价格偏差是否在允许范围内

        Args:
            item_name: 物料名称
            item_spec: 规格
            new_price: 新价格
            threshold: 偏差阈值（默认5%）

        Returns:
            {
                'has_history': bool,  # 是否有历史记录
                'avg_price': float,   # 历史平均价格
                'deviation': float,   # 偏差百分比
                'within_threshold': bool,  # 是否在阈值内
                'history_count': int  # 历史记录数
            }
        """
        records = cls.get_history_prices(item_name, item_spec, limit=20)

        if not records:
            return {
                'has_history': False,
                'avg_price': None,
                'deviation': None,
                'within_threshold': True,  # 无历史记录，视为通过
                'history_count': 0
            }

        avg_price = sum(float(r.unit_price) for r in records) / len(records)

        if avg_price == 0:
            deviation = 0 if new_price == 0 else 1.0
        else:
            deviation = abs(new_price - avg_price) / avg_price

        return {
            'has_history': True,
            'avg_price': round(avg_price, 2),
            'deviation': round(deviation, 4),
            'within_threshold': deviation <= threshold,
            'history_count': len(records)
        }

    @classmethod
    def record_price(cls, item_name: str, item_spec: str, unit_price: float,
                     qty: int = None, unit: str = None,
                     pr_id: int = None, pr_number: str = None, pr_item_id: int = None):
        """
        记录新的价格历史
        """
        record = cls(
            item_name=item_name,
            item_spec=item_spec or "",
            unit_price=unit_price,
            qty=qty,
            unit=unit,
            pr_id=pr_id,
            pr_number=pr_number,
            pr_item_id=pr_item_id,
            created_at=datetime.utcnow()
        )
        db.session.add(record)
        return record

    def __repr__(self):
        return f'<PriceHistory {self.item_name} @ {self.unit_price}>'
