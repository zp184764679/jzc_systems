#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
添加黑名单字段到员工表
Add blacklist fields to employees table
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from sqlalchemy import text

def add_blacklist_fields():
    """添加黑名单相关字段"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("HR系统 - 添加黑名单字段")
        print("=" * 80)

        try:
            # 检查字段是否已存在
            result = db.session.execute(text("""
                SELECT COUNT(*) as count
                FROM pragma_table_info('employees')
                WHERE name = 'is_blacklisted'
            """))

            field_exists = result.fetchone()[0] > 0

            if field_exists:
                print("\n✓ 黑名单字段已存在，无需迁移")
                return True

            print("\n正在添加黑名单字段...")

            # 添加 is_blacklisted 字段
            db.session.execute(text("""
                ALTER TABLE employees
                ADD COLUMN is_blacklisted INTEGER NOT NULL DEFAULT 0
            """))
            print("✓ 添加字段: is_blacklisted")

            # 添加 blacklist_reason 字段
            db.session.execute(text("""
                ALTER TABLE employees
                ADD COLUMN blacklist_reason TEXT
            """))
            print("✓ 添加字段: blacklist_reason")

            # 添加 blacklist_date 字段
            db.session.execute(text("""
                ALTER TABLE employees
                ADD COLUMN blacklist_date DATE
            """))
            print("✓ 添加字段: blacklist_date")

            # 提交更改
            db.session.commit()

            print("\n✓ 黑名单字段添加成功！")

            # 验证字段
            print("\n验证新字段...")
            result = db.session.execute(text("""
                SELECT name, type, [notnull], dflt_value
                FROM pragma_table_info('employees')
                WHERE name IN ('is_blacklisted', 'blacklist_reason', 'blacklist_date')
                ORDER BY name
            """))

            print("\n新添加的字段:")
            for row in result:
                print(f"  - {row[0]:20s} | 类型: {row[1]:10s} | NOT NULL: {row[2]} | 默认值: {row[3]}")

            return True

        except Exception as e:
            print(f"\n✗ 迁移失败: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False


def main():
    """主函数"""
    print("=" * 80)
    print("数据库迁移工具 - 添加黑名单字段")
    print("=" * 80)

    if not add_blacklist_fields():
        print("\n✗ 迁移失败！")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("迁移完成！")
    print("=" * 80)


if __name__ == '__main__':
    main()
