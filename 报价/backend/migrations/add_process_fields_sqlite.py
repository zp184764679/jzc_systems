"""
SQLite迁移脚本：为processes表添加新字段
执行时间: 2025-11-14
"""
import sqlite3
import os

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'quote_system.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(processes)")
        columns = [column[1] for column in cursor.fetchall()]

        # 添加 daily_fee 字段
        if 'daily_fee' not in columns:
            print("添加 daily_fee 字段...")
            cursor.execute("ALTER TABLE processes ADD COLUMN daily_fee DECIMAL(10, 2) DEFAULT 0")
            print("✅ daily_fee 字段添加成功")
        else:
            print("⚠️  daily_fee 字段已存在，跳过")

        # 添加 icon 字段
        if 'icon' not in columns:
            print("添加 icon 字段...")
            cursor.execute("ALTER TABLE processes ADD COLUMN icon VARCHAR(10)")
            print("✅ icon 字段添加成功")
        else:
            print("⚠️  icon 字段已存在，跳过")

        conn.commit()
        print("\n✅ 迁移成功完成！")

        # 显示当前表结构
        cursor.execute("PRAGMA table_info(processes)")
        print("\n当前 processes 表结构:")
        for column in cursor.fetchall():
            print(f"  - {column[1]}: {column[2]}")

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("开始执行迁移脚本...")
    migrate()
