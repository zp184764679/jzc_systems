#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析Excel中的组别结构
"""
import pandas as pd
import numpy as np

EXCEL_FILE = r"C:\Users\Admin\Desktop\HR\东莞厂人事资料-新2025.10.24xls.xls"

def analyze_teams():
    """分析Excel中的组别结构"""
    print("=" * 80)
    print("分析Excel中的组别结构")
    print("=" * 80)

    # 读取"总人数"工作表
    try:
        print(f"\n正在读取Excel文件: {EXCEL_FILE}")
        df = pd.read_excel(EXCEL_FILE, sheet_name='总人数', header=None)

        print(f"✓ 成功读取 {len(df)} 行数据")
        print(f"✓ 列数: {len(df.columns)}")

        # 显示前100行数据来分析结构
        print("\n前100行数据预览:")
        print("-" * 80)
        for idx, row in df.head(100).iterrows():
            # 显示每行的前10列
            row_data = []
            for i in range(min(10, len(row))):
                val = row.iloc[i]
                if pd.notna(val):
                    row_data.append(f"[{i}]:{val}")
            print(f"行{idx:3d}: {' | '.join(row_data)}")

    except Exception as e:
        print(f"✗ 读取Excel文件失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    analyze_teams()
