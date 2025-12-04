#!/usr/bin/env python
"""检查数据库中的图纸记录"""
import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 创建数据库连接
engine = create_engine('sqlite:///./quote_system.db')
Session = sessionmaker(bind=engine)
session = Session()

# 查询图纸记录
from models.drawing import Drawing
drawings = session.query(Drawing).all()

print(f"数据库中共有 {len(drawings)} 条图纸记录:\n")
for d in drawings:
    print(f"ID: {d.id}")
    print(f"  图号: {d.drawing_number}")
    print(f"  文件名: {d.file_name}")
    print(f"  OCR状态: {d.ocr_status}")
    print(f"  创建时间: {d.created_at}")
    print()

session.close()
