#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复工号格式和职位名称
1. 去除工号的 .0 后缀
2. 简化职位名称（去除部门前缀）
"""
import sys
import os
import re

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.employee import Employee

# 职位名称简化规则
# 如果职位包含部门名称，则去除部门前缀
def simplify_title(department, title):
    """简化职位名称，去除部门前缀"""
    if not department or not title:
        return title

    # 如果职位以部门名开头，去除部门名
    if title.startswith(department):
        simplified = title[len(department):]
        # 如果简化后不为空，返回简化后的名称
        if simplified:
            return simplified

    return title


def fix_data():
    """修复工号和职位数据"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("修复工号格式和职位名称")
        print("=" * 80)

        # 统计
        empno_fixed_count = 0
        title_fixed_count = 0

        print("\n开始处理员工数据...")

        for employee in Employee.query.all():
            modified = False

            # 1. 修复工号格式（去除.0后缀）
            if employee.empNo and '.0' in employee.empNo:
                old_empno = employee.empNo
                # 去除 .0 后缀
                new_empno = employee.empNo.replace('.0', '')
                employee.empNo = new_empno
                empno_fixed_count += 1
                modified = True
                print(f"  工号修复: {old_empno} -> {new_empno}")

            # 2. 简化职位名称
            if employee.department and employee.title:
                old_title = employee.title
                new_title = simplify_title(employee.department, employee.title)

                if old_title != new_title:
                    employee.title = new_title
                    title_fixed_count += 1
                    modified = True
                    print(f"  职位简化: {employee.empNo} - {employee.department} - {old_title} -> {new_title}")

        # 提交更改
        try:
            db.session.commit()
            print(f"\n✓ 数据修复完成！")
            print(f"  工号修复: {empno_fixed_count} 条")
            print(f"  职位简化: {title_fixed_count} 条")

        except Exception as e:
            print(f"\n✗ 提交失败: {e}")
            db.session.rollback()
            return False

        # 显示修复后的统计
        print("\n修复后的示例数据:")
        print("-" * 80)
        sample_employees = Employee.query.filter(
            Employee.department.in_(['铣床', '磨床', '数控', '走心机', '加工中心'])
        ).limit(10).all()

        for emp in sample_employees:
            print(f"{emp.empNo:<10s} {emp.name:<10s} {emp.department:<15s} {emp.title or '-':<20s}")

        return True


if __name__ == '__main__':
    fix_data()
