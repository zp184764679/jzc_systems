#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加工厂字段
Add factory_id column to employees table
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from sqlalchemy import inspect, text

def migrate_add_factory_column():
    """添加factory_id列到employees表"""
    app = create_app()

    with app.app_context():
        inspector = inspect(db.engine)

        # 检查employees表是否存在
        if 'employees' not in inspector.get_table_names():
            print("✗ employees表不存在！")
            return False

        # 获取现有列
        columns = [col['name'] for col in inspector.get_columns('employees')]

        # 检查factory_id列是否已存在
        if 'factory_id' in columns:
            print("✓ factory_id列已存在，无需迁移")
            return True

        # 添加factory_id列
        try:
            print("正在添加factory_id列...")
            with db.engine.connect() as conn:
                # SQLite语法：ALTER TABLE ADD COLUMN
                conn.execute(text(
                    "ALTER TABLE employees ADD COLUMN factory_id INTEGER"
                ))
                conn.commit()

            print("✓ 成功添加factory_id列")
            return True

        except Exception as e:
            print(f"✗ 添加factory_id列失败: {e}")
            return False


def main():
    """主函数"""
    print("=" * 60)
    print("HR系统 - 数据库迁移工具")
    print("=" * 60)

    success = migrate_add_factory_column()

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
