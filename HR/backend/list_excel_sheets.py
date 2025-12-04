#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
列出Excel中的所有工作表
"""
import pandas as pd

EXCEL_FILE = r"C:\Users\Admin\Desktop\HR\东莞厂人事资料-新2025.10.24xls.xls"

def list_sheets():
    """列出所有工作表"""
    try:
        xl_file = pd.ExcelFile(EXCEL_FILE)
        print("=" * 80)
        print(f"Excel文件: {EXCEL_FILE}")
        print("=" * 80)
        print(f"\n工作表列表 (共{len(xl_file.sheet_names)}个):")
        for i, sheet_name in enumerate(xl_file.sheet_names, 1):
            print(f"  {i}. {sheet_name}")

        # 尝试读取每个工作表的前几行
        print("\n" + "=" * 80)
        for sheet_name in xl_file.sheet_names:
            print(f"\n工作表: {sheet_name}")
            print("-" * 80)
            try:
                df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, header=None, nrows=20)
                print(f"行数: {len(df)}, 列数: {len(df.columns)}")
                print("\n前10行数据:")
                for idx, row in df.head(10).iterrows():
                    row_data = []
                    for i in range(min(15, len(row))):
                        val = row.iloc[i]
                        if pd.notna(val):
                            row_data.append(f"[{i}]:{str(val)[:30]}")
                    if row_data:
                        print(f"  行{idx}: {' | '.join(row_data)}")
            except Exception as e:
                print(f"  ✗ 读取失败: {e}")

    except Exception as e:
        print(f"✗ 打开Excel文件失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    list_sheets()
