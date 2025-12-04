#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证员工数据导入结果
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.employee import Employee
from app.models.base_data import Factory

def verify_import():
    """验证导入的数据"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("HR系统 - 数据导入验证")
        print("=" * 60)

        # 1. 工厂统计
        print("\n【工厂数据】")
        factories = Factory.query.all()
        for factory in factories:
            print(f"  {factory.code}: {factory.name} ({factory.city})")

        # 2. 员工总数
        total_employees = Employee.query.count()
        print(f"\n【员工总数】: {total_employees} 人")

        # 3. 按工厂统计
        print("\n【按工厂统计】")
        for factory in factories:
            count = Employee.query.filter_by(factory_id=factory.id).count()
            print(f"  {factory.name}: {count} 人")

        # 4. 按部门统计
        print("\n【按部门统计】(前10个)")
        departments = db.session.query(
            Employee.department,
            db.func.count(Employee.id).label('count')
        ).filter(
            Employee.department.isnot(None)
        ).group_by(
            Employee.department
        ).order_by(
            db.func.count(Employee.id).desc()
        ).limit(10).all()

        for dept, count in departments:
            print(f"  {dept}: {count} 人")

        # 5. 抽样显示前5名员工
        print("\n【员工样本】(前5名)")
        samples = Employee.query.limit(5).all()
        for emp in samples:
            factory_name = emp.factory_ref.name if emp.factory_ref else "未分配"
            print(f"  {emp.empNo} - {emp.name} - {emp.department} - {factory_name}")

        print("\n" + "=" * 60)
        print("验证完成！")
        print("=" * 60)


if __name__ == '__main__':
    verify_import()
