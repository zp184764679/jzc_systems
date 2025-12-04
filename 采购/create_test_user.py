#!/usr/bin/env python
# -*- coding: utf-8 -*-
from werkzeug.security import generate_password_hash
import pymysql

# 生成密码哈希
password = "admin123"
password_hash = generate_password_hash(password)

print(f"Password hash for '{password}': {password_hash}")

# 连接数据库
conn = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='exak472008',
    database='caigou',
    charset='utf8mb4'
)

try:
    with conn.cursor() as cursor:
        # 删除已有的测试用户
        cursor.execute("DELETE FROM users WHERE email='admin@test.com'")

        # 插入测试用户
        sql = """
        INSERT INTO users (username, email, password_hash, status, role, department, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        cursor.execute(sql, ('管理员', 'admin@test.com', password_hash, 'approved', 'super_admin', '行政'))

        conn.commit()
        print("✅ 测试用户创建成功！")
        print("   邮箱: admin@test.com")
        print("   密码: admin123")
        print("   角色: super_admin")
        print("   状态: approved")

        # 验证
        cursor.execute("SELECT id, username, email, role, status FROM users WHERE email='admin@test.com'")
        user = cursor.fetchone()
        print(f"\n验证: {user}")

finally:
    conn.close()
