# models/supplier_category.py
# ✅ 重构：支持完整品类名称存储 + 大类查询优化
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.mysql import BIGINT
from extensions import db
from datetime import datetime


class SupplierCategory(db.Model):
    """
    供应商分类模型
    
    ✅ 核心字段：
    - category: 完整品类名称（如 "刀具/铣削刀具"）
    - major_category: 大类（如 "刀具"）- 用于快速匹配
    - minor_category: 小类（如 "铣削刀具"）- 可选
    
    业务流程：
    1. AI分类器 → category = "刀具/铣削刀具"
    2. RFQ 物料分类 → 存储 category 字段
    3. RFQ 匹配供应商 → 按 major_category 查询
    4. 前端显示 → 使用 category 直接显示
    """
    __tablename__ = 'supplier_categories'
    __table_args__ = (
        # 同一供应商不应重复绑定同一完整分类
        db.UniqueConstraint('supplier_id', 'category', name='uq_supplier_category'),
        
        # 索引：加快查询速度
        db.Index('idx_sc_supplier', 'supplier_id'),
        db.Index('idx_sc_major', 'major_category'),  # ✅ RFQ 匹配供应商使用
        db.Index('idx_sc_category', 'category'),      # ✅ 快速查询完整品类
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    supplier_id = db.Column(BIGINT(unsigned=True), ForeignKey('suppliers.id'), nullable=False)
    
    # ✅ 核心字段：完整品类名称
    # 格式："刀具/铣削刀具"（来自 AI 分类器或手工输入）
    category = db.Column(String(200), nullable=False)
    
    # ✅ 优化：拆分出大类（用于 RFQ 快速匹配）
    # 格式："刀具"（从 category 中提取，或手工指定）
    major_category = db.Column(String(50), nullable=True, index=True)
    
    # ✅ 可选：小类名称
    # 格式："铣削刀具"
    minor_category = db.Column(String(100), nullable=True)
    
    # 元数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = db.relationship('Supplier', back_populates='categories')

    def __repr__(self):
        return f"<SupplierCategory supplier_id={self.supplier_id} category='{self.category}' major='{self.major_category}'>"
    
    def to_dict(self):
        """
        序列化为字典 - 用于前端展示
        
        返回格式：
        {
            "id": 1,
            "category": "刀具/铣削刀具",
            "major_category": "刀具",
            "minor_category": "铣削刀具"
        }
        """
        return {
            'id': self.id,
            'category': self.category,
            'major_category': self.major_category,
            'minor_category': self.minor_category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }