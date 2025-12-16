"""
数据库修复脚本：将 users 表的 password_hash 字段重命名为 hashed_password
以匹配 shared/auth/models.py 中的 User 模型定义
"""
from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()

def fix_users_table():
    """修复 users 表字段名"""
    # 数据库配置
    DB_USER = os.getenv('MYSQL_USER', 'app')
    DB_PASSWORD = os.getenv('MYSQL_PASSWORD', 'app')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('MYSQL_DATABASE', 'cncplan')
    DATABASE_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'

    print(f"连接数据库: {DB_NAME}@{DB_HOST}")
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    # 检查 users 表是否存在
    if 'users' not in inspector.get_table_names():
        print("❌ users 表不存在")
        return

    # 获取现有列
    existing_columns = {col['name'] for col in inspector.get_columns('users')}
    print(f"现有字段: {sorted(existing_columns)}")

    with engine.connect() as conn:
        # 1. 如果存在 password_hash 但不存在 hashed_password，则重命名
        if 'password_hash' in existing_columns and 'hashed_password' not in existing_columns:
            print("\n步骤 1: 重命名 password_hash -> hashed_password")
            try:
                sql = "ALTER TABLE users CHANGE COLUMN password_hash hashed_password VARCHAR(255) NOT NULL"
                conn.execute(text(sql))
                conn.commit()
                print("✅ 成功重命名字段 password_hash -> hashed_password")
            except Exception as e:
                print(f"❌ 重命名失败: {e}")
                conn.rollback()
                return
        elif 'hashed_password' in existing_columns:
            print("✅ hashed_password 字段已存在，无需修改")
        else:
            print("⚠️  两个字段都不存在，需要创建 hashed_password 字段")
            try:
                sql = "ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255) NOT NULL DEFAULT ''"
                conn.execute(text(sql))
                conn.commit()
                print("✅ 成功创建 hashed_password 字段")
            except Exception as e:
                print(f"❌ 创建失败: {e}")
                conn.rollback()
                return

        # 2. 检查并添加其他可能缺失的字段
        required_fields = {
            'full_name': "VARCHAR(100)",
            'emp_no': "VARCHAR(50)",
            'user_type': "VARCHAR(20) DEFAULT 'employee' NOT NULL",
            'permissions': "VARCHAR(500)",
            'supplier_id': "INTEGER",
            'department_id': "INTEGER",
            'department_name': "VARCHAR(100)",
            'position_id': "INTEGER",
            'position_name': "VARCHAR(100)",
            'team_id': "INTEGER",
            'team_name': "VARCHAR(100)",
            'is_active': "BOOLEAN DEFAULT TRUE",
            'is_admin': "BOOLEAN DEFAULT FALSE",
            'updated_at': "DATETIME"
        }

        # 重新获取列信息
        existing_columns = {col['name'] for col in inspector.get_columns('users')}

        print("\n步骤 2: 检查其他必需字段")
        for field_name, field_def in required_fields.items():
            if field_name not in existing_columns:
                print(f"  添加字段: {field_name}")
                try:
                    sql = f"ALTER TABLE users ADD COLUMN {field_name} {field_def}"
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"  ✅ 成功添加 {field_name}")
                except Exception as e:
                    print(f"  ⚠️  添加 {field_name} 失败: {e}")
                    conn.rollback()

    # 3. 验证修复结果
    print("\n步骤 3: 验证修复结果")
    inspector = inspect(engine)
    final_columns = {col['name'] for col in inspector.get_columns('users')}
    print(f"修复后字段: {sorted(final_columns)}")

    if 'hashed_password' in final_columns:
        print("\n✅ users 表修复成功！hashed_password 字段已存在")
    else:
        print("\n❌ 修复失败，hashed_password 字段仍不存在")

if __name__ == '__main__':
    fix_users_table()
