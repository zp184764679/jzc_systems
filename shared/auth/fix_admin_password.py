"""
重置管理员密码工具
安全修复：生成随机密码而非使用固定密码
"""
import sys
import os
import secrets
sys.path.insert(0, os.path.dirname(__file__))

from password_utils import hash_password
from sqlalchemy import create_engine, text

# 从环境变量读取数据库配置
DB_USER = os.getenv('AUTH_DB_USER', os.getenv('MYSQL_USER', 'app'))
DB_PASSWORD = os.getenv('AUTH_DB_PASSWORD', os.getenv('MYSQL_PASSWORD', 'app'))
DB_HOST = os.getenv('AUTH_DB_HOST', os.getenv('DB_HOST', 'localhost'))
DB_NAME = os.getenv('AUTH_DB_NAME', 'account')

db_url = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'
engine = create_engine(db_url)

# 安全修复：生成随机密码
password = secrets.token_urlsafe(16)
hashed = hash_password(password)

print("=" * 50)
print("⚠️  管理员密码重置工具")
print("=" * 50)

# Update the admin user
with engine.connect() as conn:
    result = conn.execute(text(
        "UPDATE users SET hashed_password = :hash WHERE username = 'admin'"
    ), {"hash": hashed})
    conn.commit()

    if result.rowcount > 0:
        print(f"✅ 已更新 {result.rowcount} 条记录")
        print()
        print("新的管理员凭证:")
        print(f"  用户名: admin")
        print(f"  密码: {password}")
        print()
        print("⚠️  请立即登录并修改密码！")
        print("⚠️  此密码只显示一次，请妥善保存！")
    else:
        print("❌ 未找到 admin 用户")

print("=" * 50)
