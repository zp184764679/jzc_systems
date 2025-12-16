"""
添加 seq_no 列到 customers 表 (SQLite版本)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from sqlalchemy import text

def add_column():
    app = create_app()
    with app.app_context():
        # SQLite: 检查列是否已存在
        result = db.session.execute(text("PRAGMA table_info(customers)"))
        columns = [row[1] for row in result.fetchall()]

        if 'seq_no' in columns:
            print("seq_no 列已存在")
        else:
            # 添加列
            db.session.execute(text("ALTER TABLE customers ADD COLUMN seq_no INTEGER"))
            db.session.commit()
            print("已添加 seq_no 列")

        # 创建索引 (SQLite 不支持 IF NOT EXISTS for index, 所以用try)
        try:
            db.session.execute(text("CREATE INDEX idx_customers_seq_no ON customers(seq_no)"))
            db.session.commit()
            print("已创建索引")
        except Exception:
            print("索引已存在或创建失败")

if __name__ == '__main__':
    add_column()
