#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建缺失的数据库表
"""
from app import app, db

if __name__ == '__main__':
    with app.app_context():
        print("正在创建缺失的表...")
        db.create_all()
        print("✅ 所有缺失的表已创建完成!")

        # 验证表已创建
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\n当前数据库中的表: {len(tables)} 个")
        for table in sorted(tables):
            print(f"  - {table}")
