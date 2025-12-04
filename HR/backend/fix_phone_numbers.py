#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复电话号码格式（去除.0后缀）
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.employee import Employee

def fix_phone_numbers():
    """修复电话号码格式"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("修复电话号码格式")
        print("=" * 80)

        fixed_count = 0

        print("\n开始处理员工电话号码...")

        for employee in Employee.query.all():
            if employee.phone and '.0' in str(employee.phone):
                old_phone = employee.phone
                # 去除 .0 后缀
                new_phone = str(employee.phone).replace('.0', '')
                employee.phone = new_phone
                fixed_count += 1
                print(f"  {employee.name}: {old_phone} -> {new_phone}")

        # 提交更改
        try:
            db.session.commit()
            print(f"\n✓ 电话号码修复完成！")
            print(f"  修复数量: {fixed_count} 条")

        except Exception as e:
            print(f"\n✗ 提交失败: {e}")
            db.session.rollback()
            return False

        return True


if __name__ == '__main__':
    fix_phone_numbers()
