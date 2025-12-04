#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把所有"走芯机"改成"走心机"
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.base_data import Department, Team
from app.models.employee import Employee

def fix_zouxinji():
    """修改走芯机为走心机"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("修改 走芯机 -> 走心机")
        print("=" * 80)

        # 1. 修改部门表
        print("\n【修改部门】")
        print("-" * 80)
        dept = Department.query.filter_by(name='走芯机').first()
        if dept:
            old_name = dept.name
            dept.name = '走心机'
            print(f"  ✓ 部门: {old_name} -> {dept.name}")
        else:
            print("  - 未找到'走芯机'部门")

        # 2. 修改团队表
        print("\n【修改团队】")
        print("-" * 80)
        team = Team.query.filter_by(name='走芯机组').first()
        if team:
            old_name = team.name
            team.name = '走心机组'
            print(f"  ✓ 团队: {old_name} -> {team.name}")
        else:
            print("  - 未找到'走芯机组'团队")

        # 3. 修改员工表中的部门字段
        print("\n【修改员工部门】")
        print("-" * 80)
        employees_dept = Employee.query.filter_by(department='走芯机').all()
        print(f"  找到 {len(employees_dept)} 名员工的部门为'走芯机'")
        for emp in employees_dept:
            emp.department = '走心机'
            print(f"    {emp.name}: 走芯机 -> 走心机")

        # 4. 修改员工表中的团队字段
        print("\n【修改员工团队】")
        print("-" * 80)
        employees_team = Employee.query.filter_by(team='走芯机组').all()
        print(f"  找到 {len(employees_team)} 名员工的团队为'走芯机组'")
        for emp in employees_team:
            emp.team = '走心机组'
            print(f"    {emp.name}: 走芯机组 -> 走心机组")

        # 提交更改
        try:
            db.session.commit()
            print("\n" + "=" * 80)
            print("✓ 修改完成！")
            print(f"  部门: 走芯机 -> 走心机")
            print(f"  团队: 走芯机组 -> 走心机组")
            print(f"  员工部门: {len(employees_dept)} 人")
            print(f"  员工团队: {len(employees_team)} 人")
            print("=" * 80)

        except Exception as e:
            print(f"\n✗ 提交失败: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

        return True


if __name__ == '__main__':
    fix_zouxinji()
