#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查OCR识别的原始数据
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.settings import settings

# 创建数据库连接
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 80)
print("📊 检查OCR原始数据")
print("=" * 80)

# 查询图纸ID=2的OCR数据
query = text("""
    SELECT
        id,
        drawing_number,
        ocr_data,
        ocr_status,
        tolerance,
        surface_roughness
    FROM drawings
    WHERE id = 1
""")

result = session.execute(query).fetchone()

if result:
    print(f"\n图纸ID: {result.id}")
    print(f"图号: {result.drawing_number}")
    print(f"OCR状态: {result.ocr_status}")
    print(f"\n数据库字段值:")
    print(f"  tolerance (公差): {repr(result.tolerance)}")
    print(f"  surface_roughness (表面粗糙度): {repr(result.surface_roughness)}")

    if result.ocr_data:
        print(f"\n{'=' * 80}")
        print("OCR原始数据 (JSON):")
        print(f"{'=' * 80}")
        try:
            ocr_data = json.loads(result.ocr_data) if isinstance(result.ocr_data, str) else result.ocr_data
            print(json.dumps(ocr_data, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"解析OCR数据失败: {e}")
            print(result.ocr_data)
    else:
        print("\n⚠️  OCR原始数据为空")
else:
    print("\n⚠️  未找到图纸ID=2的记录")

session.close()

print("\n" + "=" * 80)
print("✅ 检查完成")
print("=" * 80)
