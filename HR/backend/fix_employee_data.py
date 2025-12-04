#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复员工数据问题
1. 修复工号的.0后缀
2. 清理部门中的"/"
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.employee import Employee

def fix_employee_numbers():
    """修复工号的.0后缀问题"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("修复员工工号格式")
        print("=" * 80)

        # 获取所有员工
        employees = Employee.query.all()
        fixed_count = 0

        for emp in employees:
            # 检查工号是否包含.0
            if '.' in emp.empNo:
                try:
                    # 将工号转为浮点数，再转为整数，最后转为字符串
                    emp_num = float(emp.empNo)
                    emp.empNo = str(int(emp_num))
                    fixed_count += 1

                    if fixed_count % 100 == 0:
                        print(f"  已修复 {fixed_count} 个工号...")
                except:
                    print(f"✗ 无法修复工号: {emp.empNo}")
                    continue

        # 提交更改
        try:
            db.session.commit()
            print(f"\n✓ 成功修复 {fixed_count} 个工号")
            return True
        except Exception as e:
            print(f"✗ 提交失败: {e}")
            db.session.rollback()
            return False


def clean_department_slashes():
    """清理部门中的斜杠"""
    app = create_app()

    with app.app_context():
        print("\n" + "=" * 80)
        print("清理部门数据")
        print("=" * 80)

        # 查找部门为"/"的员工
        employees = Employee.query.filter_by(department='/').all()

        print(f"\n找到 {len(employees)} 个员工的部门为 '/'")
        print("将其设置为 None（空）")

        for emp in employees:
            emp.department = None

        try:
            db.session.commit()
            print(f"✓ 成功清理 {len(employees)} 个部门数据")
            return True
        except Exception as e:
            print(f"✗ 提交失败: {e}")
            db.session.rollback()
            return False


def main():
    """主函数"""
    print("=" * 80)
    print("员工数据修复工具")
    print("=" * 80)

    # 修复工号
    if not fix_employee_numbers():
        print("\n✗ 工号修复失败！")
        sys.exit(1)

    # 清理部门
    if not clean_department_slashes():
        print("\n✗ 部门清理失败！")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("所有数据修复完成！")
    print("=" * 80)


if __name__ == '__main__':
    main()
