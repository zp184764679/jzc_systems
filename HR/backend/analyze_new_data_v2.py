#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析新的东莞厂人事资料Excel文件 - v2
"""
import pandas as pd
import os

# Excel文件路径
excel_file = r"C:\Users\Admin\Desktop\HR\东莞厂人事资料-新2025.10.24xls.xls"

try:
    # 先读取前几行看看结构
    df_raw = pd.read_excel(excel_file, nrows=5)
    print("原始前5行数据:")
    print(df_raw)
    print("\n原始列名:")
    print(df_raw.columns.tolist())

    # 读取Excel文件 - 跳过前2行（标题行和列名行在Excel里可能是合并的）
    df = pd.read_excel(excel_file, skiprows=2)

    print("\n" + "=" * 80)
    print("东莞厂人事资料 - 数据分析 (skiprows=2)")
    print("=" * 80)

    # 基本信息
    print(f"\n【基本信息】")
    print(f"总行数: {len(df)}")
    print(f"总列数: {len(df.columns)}")

    # 列名
    print(f"\n【列名列表】({len(df.columns)}个字段)")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")

    # 前5行数据样本
    print(f"\n【数据样本】(前5行)")
    for i, row in df.head().iterrows():
        print(f"\n第{i}行:")
        for col in df.columns[:10]:  # 只显示前10列
            print(f"  {col}: {row[col]}")

except Exception as e:
    print(f"✗ 读取文件失败: {e}")
    import traceback
    traceback.print_exc()
