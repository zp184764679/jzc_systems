#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查Excel文件的所有工作表
"""
import pandas as pd

# Excel文件路径
excel_file = r"C:\Users\Admin\Desktop\HR\东莞厂人事资料-新2025.10.24xls.xls"

try:
    # 读取所有工作表
    excel_data = pd.ExcelFile(excel_file)

    print("=" * 80)
    print("Excel文件工作表分析")
    print("=" * 80)

    print(f"\n文件: {excel_file}")
    print(f"\n总共有 {len(excel_data.sheet_names)} 个工作表:")

    for i, sheet_name in enumerate(excel_data.sheet_names, 1):
        print(f"\n【工作表 {i}】: {sheet_name}")

        # 读取该工作表的数据
        df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=5)

        print(f"  - 总行数: {len(pd.read_excel(excel_file, sheet_name=sheet_name))}")
        print(f"  - 总列数: {len(df.columns)}")
        print(f"  - 前5行预览:")
        print(df.head())

        # 如果有标题行，尝试跳过标题读取
        if len(df) > 2:
            df_skip = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=2, nrows=3)
            print(f"\n  - 跳过标题后的列名:")
            print(f"    {list(df_skip.columns)}")

    print("\n" + "=" * 80)
    print("分析完成！")
    print("=" * 80)

except Exception as e:
    print(f"✗ 读取文件失败: {e}")
    import traceback
    traceback.print_exc()
