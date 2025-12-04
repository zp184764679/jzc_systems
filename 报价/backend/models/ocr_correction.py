# models/ocr_correction.py
"""
OCR修正记录模型
用于记录人工修正数据,实现AI学习优化
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class OCRCorrection(Base):
    """OCR修正记录表"""
    __tablename__ = 'ocr_corrections'

    id = Column(Integer, primary_key=True, index=True)
    drawing_id = Column(Integer, ForeignKey('drawings.id'), nullable=False)

    # 字段信息
    field_name = Column(String(50), nullable=False)  # 修正的字段名
    ocr_value = Column(Text)  # OCR原始值
    corrected_value = Column(Text)  # 人工修正值

    # 修正类型统计
    correction_type = Column(String(20))  # full_error(完全错误), partial_error(部分错误), format_error(格式错误)
    similarity_score = Column(Float)  # 相似度分数(0-1)

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # 关系
    drawing = relationship("Drawing", back_populates="corrections")
