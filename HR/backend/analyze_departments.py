#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析和清洗部门数据
"""
import sys
import os
from collections import Counter

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.employee import Employee
from sqlalchemy import func

def analyze_departments():
    """分析部门数据"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("部门数据分析")
        print("=" * 80)

        # 统计各部门人数
        dept_counts = db.session.query(
            Employee.department,
            func.count(Employee.id)
        ).filter(
            Employee.department.isnot(None)
        ).group_by(
            Employee.department
        ).order_by(
            func.count(Employee.id).desc()
        ).all()

        print(f"\n共有 {len(dept_counts)} 个不同的部门名称")
        print(f"\n部门统计（按人数排序）：")
        print("-" * 80)
        print(f"{'部门名称':<40s} {'人数':>8s}")
        print("-" * 80)

        for dept, count in dept_counts:
            print(f"{dept:<40s} {count:>8d}")

if __name__ == '__main__':
    analyze_departments()
