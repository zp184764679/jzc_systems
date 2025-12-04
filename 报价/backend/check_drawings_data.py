#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查图纸数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import settings

# 创建数据库连接
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
session = Session()

# 查询图纸数据
from sqlalchemy import text

print("=" * 80)
print("📊 检查图纸数据")
print("=" * 80)

# 查询最近的几条图纸记录
query = text("""
    SELECT
        id,
        drawing_number,
        customer_name,
        product_name,
        material,
        outer_diameter,
        length,
        weight,
        tolerance,
        surface_roughness,
        ocr_status,
        ocr_confidence
    FROM drawings
    ORDER BY id DESC
    LIMIT 5
""")

results = session.execute(query).fetchall()

if not results:
    print("\n⚠️  数据库中没有图纸记录！")
else:
    print(f"\n✅ 共找到 {len(results)} 条最近的图纸记录：\n")

    for row in results:
        print(f"{'=' * 80}")
        print(f"ID: {row.id}")
        print(f"图号: {row.drawing_number}")
        print(f"客户: {row.customer_name}")
        print(f"产品: {row.product_name}")
        print(f"材质: {row.material}")
        print(f"外径: {repr(row.outer_diameter)} (类型: {type(row.outer_diameter).__name__})")
        print(f"长度: {repr(row.length)} (类型: {type(row.length).__name__})")
        print(f"重量: {repr(row.weight)} (类型: {type(row.weight).__name__})")
        print(f"公差: {row.tolerance}")
        print(f"表面粗糙度: {row.surface_roughness}")
        print(f"OCR状态: {row.ocr_status}")
        print(f"OCR置信度: {row.ocr_confidence}")
        print()

# 检查空值情况
print("\n" + "=" * 80)
print("📈 数据完整性统计")
print("=" * 80)

stats_query = text("""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN outer_diameter IS NULL OR outer_diameter = '' THEN 1 ELSE 0 END) as null_diameter,
        SUM(CASE WHEN length IS NULL OR length = '' THEN 1 ELSE 0 END) as null_length,
        SUM(CASE WHEN weight IS NULL OR weight = '' THEN 1 ELSE 0 END) as null_weight,
        SUM(CASE WHEN material IS NULL OR material = '' THEN 1 ELSE 0 END) as null_material
    FROM drawings
""")

stats = session.execute(stats_query).fetchone()

print(f"\n总记录数: {stats.total}")
print(f"外径为空: {stats.null_diameter} ({stats.null_diameter/stats.total*100:.1f}%)" if stats.total > 0 else "外径为空: 0")
print(f"长度为空: {stats.null_length} ({stats.null_length/stats.total*100:.1f}%)" if stats.total > 0 else "长度为空: 0")
print(f"重量为空: {stats.null_weight} ({stats.null_weight/stats.total*100:.1f}%)" if stats.total > 0 else "重量为空: 0")
print(f"材质为空: {stats.null_material} ({stats.null_material/stats.total*100:.1f}%)" if stats.total > 0 else "材质为空: 0")

session.close()

print("\n" + "=" * 80)
print("✅ 检查完成")
print("=" * 80)
