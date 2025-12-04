#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加东莞厂人事数据字段
Add Dongguan factory employee data fields to employees table
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from sqlalchemy import inspect, text

def migrate_add_dongguan_fields():
    """添加东莞厂人事数据相关字段到employees表"""
    app = create_app()

    with app.app_context():
        inspector = inspect(db.engine)

        # 检查employees表是否存在
        if 'employees' not in inspector.get_table_names():
            print("✗ employees表不存在！")
            return False

        # 获取现有列
        columns = [col['name'] for col in inspector.get_columns('employees')]

        # 要添加的新字段
        new_fields = {
            'nationality': 'VARCHAR(50)',
            'education': 'VARCHAR(50)',
            'native_place': 'VARCHAR(100)',
            'bank_card': 'VARCHAR(50)',
            'has_card': 'VARCHAR(10)',
            'salary_type': 'VARCHAR(20)',
            'accommodation': 'VARCHAR(20)'
        }

        added_count = 0
        skipped_count = 0

        try:
            with db.engine.connect() as conn:
                for field_name, field_type in new_fields.items():
                    # 检查字段是否已存在
                    if field_name in columns:
                        print(f"⊘ {field_name} 列已存在，跳过")
                        skipped_count += 1
                        continue

                    # 添加字段
                    print(f"正在添加 {field_name} 列...")
                    conn.execute(text(
                        f"ALTER TABLE employees ADD COLUMN {field_name} {field_type}"
                    ))
                    added_count += 1
                    print(f"✓ 成功添加 {field_name} 列")

                conn.commit()

            print(f"\n总结: 添加了 {added_count} 个新字段, 跳过了 {skipped_count} 个已存在字段")
            return True

        except Exception as e:
            print(f"✗ 迁移失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主函数"""
    print("=" * 60)
    print("HR系统 - 数据库迁移工具")
    print("添加东莞厂人事数据字段")
    print("=" * 60)

    success = migrate_add_dongguan_fields()

    if success:
        print("\n" + "=" * 60)
        print("迁移完成！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("迁移失败！")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
