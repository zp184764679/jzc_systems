#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析新的东莞厂人事资料Excel文件
"""
import pandas as pd
import os

# Excel文件路径
excel_file = r"C:\Users\Admin\Desktop\HR\东莞厂人事资料-新2025.10.24xls.xls"

try:
    # 读取Excel文件 - 跳过第一行标题，使用第二行作为列名
    df = pd.read_excel(excel_file, header=1)

    print("=" * 80)
    print("东莞厂人事资料 - 数据分析")
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
    print(df.head().to_string())

    # 各列的数据类型和非空统计
    print(f"\n【数据统计】")
    print(df.info())

    # 检查每列的唯一值数量
    print(f"\n【唯一值统计】")
    for col in df.columns:
        unique_count = df[col].nunique()
        null_count = df[col].isnull().sum()
        print(f"  {col}: {unique_count} 个唯一值, {null_count} 个空值")

    # 检查一些关键字段的样本值
    print(f"\n【关键字段样本值】")

    # 检查性别
    if '性别' in df.columns:
        print(f"\n性别分布:")
        print(df['性别'].value_counts())

    # 检查部门
    if '部门' in df.columns:
        print(f"\n部门分布 (前10):")
        print(df['部门'].value_counts().head(10))

    # 检查雇佣状态相关字段
    for col in df.columns:
        if '状态' in col or '类型' in col or '合同' in col:
            print(f"\n{col}分布:")
            print(df[col].value_counts())

    print("\n" + "=" * 80)
    print("分析完成！")
    print("=" * 80)

except Exception as e:
    print(f"✗ 读取文件失败: {e}")
    import traceback
    traceback.print_exc()
