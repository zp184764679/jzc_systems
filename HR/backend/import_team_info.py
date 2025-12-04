#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从Excel导入组别信息并更新到数据库
"""
import sys
import os
import pandas as pd

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.employee import Employee

EXCEL_FILE = r"C:\Users\Admin\Desktop\HR\东莞厂人事资料-新2025.10.24xls.xls"

# 组别配置：工作表名 -> 部门名
TEAM_SHEETS = {
    '铣床-生管组': '铣床',
    '磨床-品质组': '磨床',
    '加工中心-办公室': '加工中心',
    '数控-走心机': '数控',
}

def import_teams():
    """导入组别信息"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("导入组别信息")
        print("=" * 80)

        total_updated = 0

        for sheet_name, department in TEAM_SHEETS.items():
            print(f"\n处理工作表: {sheet_name} ({department})")
            print("-" * 80)

            try:
                # 读取工作表（不自动检测表头）
                df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, header=None)

                # 找到"白班"和"夜班"的列位置
                # 第1行应该包含"白班"和"夜班"
                header_row = df.iloc[1] if len(df) > 1 else None

                # 白班数据在前3列 (0,1,2)，夜班数据在后3列 (3,4,5)
                # 数据从第3行开始 (index=3)

                # 处理白班
                print(f"\n  白班:")
                white_shift_count = 0
                for idx in range(3, len(df)):
                    row = df.iloc[idx]
                    name = row.iloc[1] if pd.notna(row.iloc[1]) else None
                    position = row.iloc[2] if pd.notna(row.iloc[2]) else None

                    if name:
                        # 查找员工
                        employee = Employee.query.filter_by(
                            name=str(name).strip(),
                            department=department
                        ).first()

                        if employee:
                            old_team = employee.team
                            employee.team = "白班"
                            white_shift_count += 1
                            total_updated += 1
                            print(f"    {name}: {old_team or '无'} -> {employee.team}")
                        else:
                            print(f"    ✗ 未找到员工: {name} ({department})")

                print(f"  白班更新: {white_shift_count} 人")

                # 处理夜班
                print(f"\n  夜班:")
                night_shift_count = 0
                for idx in range(3, len(df)):
                    row = df.iloc[idx]
                    name = row.iloc[4] if len(row) > 4 and pd.notna(row.iloc[4]) else None
                    position = row.iloc[5] if len(row) > 5 and pd.notna(row.iloc[5]) else None

                    if name:
                        # 查找员工
                        employee = Employee.query.filter_by(
                            name=str(name).strip(),
                            department=department
                        ).first()

                        if employee:
                            old_team = employee.team
                            employee.team = "夜班"
                            night_shift_count += 1
                            total_updated += 1
                            print(f"    {name}: {old_team or '无'} -> {employee.team}")
                        else:
                            print(f"    ✗ 未找到员工: {name} ({department})")

                print(f"  夜班更新: {night_shift_count} 人")

            except Exception as e:
                print(f"  ✗ 处理失败: {e}")
                import traceback
                traceback.print_exc()
                continue

        # 处理走心机组（从"东莞精之成各组人员名单"工作表）
        print(f"\n处理工作表: 东莞精之成各组人员名单")
        print("-" * 80)

        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name='东莞精之成各组人员名单', header=None)

            # 走心机组在列0-2, 数控组在列4-6, 全检组在列8-10
            # 数据从第4行开始

            # 处理走心机组
            print(f"\n  走心机组:")
            walking_count = 0
            for idx in range(4, len(df)):
                row = df.iloc[idx]
                name = row.iloc[1] if pd.notna(row.iloc[1]) else None

                if name:
                    employee = Employee.query.filter_by(
                        name=str(name).strip(),
                        department='走心机'
                    ).first()

                    if employee:
                        old_team = employee.team
                        employee.team = "走心机组"
                        walking_count += 1
                        total_updated += 1
                        print(f"    {name}: {old_team or '无'} -> {employee.team}")

            print(f"  走心机组更新: {walking_count} 人")

            # 处理全检组（品质部）
            print(f"\n  全检组:")
            qc_count = 0
            for idx in range(4, len(df)):
                row = df.iloc[idx]
                name = row.iloc[9] if len(row) > 9 and pd.notna(row.iloc[9]) else None

                if name:
                    employee = Employee.query.filter_by(
                        name=str(name).strip(),
                        department='品质部'
                    ).first()

                    if employee:
                        old_team = employee.team
                        employee.team = "全检组"
                        qc_count += 1
                        total_updated += 1
                        print(f"    {name}: {old_team or '无'} -> {employee.team}")

            print(f"  全检组更新: {qc_count} 人")

        except Exception as e:
            print(f"  ✗ 处理失败: {e}")
            import traceback
            traceback.print_exc()

        # 提交更改
        try:
            db.session.commit()
            print(f"\n" + "=" * 80)
            print(f"✓ 组别信息导入完成！")
            print(f"  总共更新: {total_updated} 名员工")
            print("=" * 80)

        except Exception as e:
            print(f"\n✗ 提交失败: {e}")
            db.session.rollback()
            return False

        return True


if __name__ == '__main__':
    import_teams()
