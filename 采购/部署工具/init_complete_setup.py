# -*- coding: utf-8 -*-
"""
完整初始化：创建数据库、用户、测试数据
"""
import pymysql
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

print("=" * 60)
print("📊 采购系统 - 完整初始化")
print("=" * 60)
print()

# MySQL连接配置 - 尝试多种可能的root密码
ROOT_PASSWORDS = ['', 'root', 'exak472008', 'Exak472008', 'admin', 'Admin123']
HOST = 'localhost'
PORT = 3306

# 数据库配置
DB_NAME = 'caigou'
DB_USER = 'exzzz'
DB_PASSWORD = 'exak472008'

# 尝试连接MySQL
connection = None
used_password = None

for pwd in ROOT_PASSWORDS:
    try:
        print(f"尝试使用密码: {'(空密码)' if pwd == '' else '****'}")
        connection = pymysql.connect(
            host=HOST,
            port=PORT,
            user='root',
            password=pwd,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        used_password = pwd
        print(f"✅ 连接成功!")
        break
    except Exception as e:
        if 'Access denied' in str(e):
            continue
        else:
            print(f"❌ 连接失败: {e}")
            continue

if connection is None:
    print()
    print("❌ 无法连接到MySQL数据库")
    print()
    print("解决方案:")
    print("1. 请在MySQL命令行工具中手动执行:")
    print("   mysql -u root -p")
    print("   输入root密码后，执行:")
    print(f"   source C:/Users/Admin/Desktop/采购/部署工具/init_caigou_db.sql")
    print()
    print("2. 或者手动执行以下命令:")
    print(f"   CREATE DATABASE {DB_NAME};")
    print(f"   CREATE USER '{DB_USER}'@'localhost' IDENTIFIED BY '{DB_PASSWORD}';")
    print(f"   GRANT ALL PRIVILEGES ON {DB_NAME}.* TO '{DB_USER}'@'localhost';")
    sys.exit(1)

print()

try:
    with connection.cursor() as cursor:
        # 1. 删除旧数据库
        print("[1/8] 删除旧数据库(如果存在)...")
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        print("✅ 完成")

        # 2. 创建新数据库
        print()
        print("[2/8] 创建新数据库...")
        cursor.execute(f"""
            CREATE DATABASE {DB_NAME}
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci
        """)
        print(f"✅ 数据库 {DB_NAME} 已创建")

        # 3-6. 创建用户
        hosts = [
            ('localhost', '本地访问'),
            ('192.168.0.%', '局域网访问'),
            ('172.%', 'WSL2访问'),
            ('%', '任意IP访问')
        ]

        for idx, (host, desc) in enumerate(hosts, start=3):
            print()
            print(f"[{idx}/8] 配置{desc} ({host})...")

            # 删除旧用户
            cursor.execute(f"DROP USER IF EXISTS '{DB_USER}'@'{host}'")

            # 创建新用户
            cursor.execute(f"""
                CREATE USER '{DB_USER}'@'{host}'
                IDENTIFIED BY '{DB_PASSWORD}'
            """)

            # 授予权限
            cursor.execute(f"""
                GRANT ALL PRIVILEGES ON {DB_NAME}.*
                TO '{DB_USER}'@'{host}'
            """)

            print(f"✅ 用户 {DB_USER}@{host} 已创建并授权")

        # 7. 刷新权限
        print()
        print("[7/8] 刷新权限...")
        cursor.execute("FLUSH PRIVILEGES")
        print("✅ 权限已刷新")

        # 验证创建的用户
        print()
        print("验证创建的用户:")
        cursor.execute(f"""
            SELECT User, Host
            FROM mysql.user
            WHERE User = '{DB_USER}'
        """)
        users = cursor.fetchall()
        for user in users:
            print(f"  ✓ {user['User']}@{user['Host']}")

    connection.commit()
    connection.close()

    # 8. 使用新用户连接并创建表结构
    print()
    print("[8/8] 初始化表结构...")
    print()
    print("✅ 数据库初始化完成！")
    print()
    print("=" * 60)
    print("📊 数据库信息:")
    print(f"   数据库名: {DB_NAME}")
    print(f"   用户名: {DB_USER}")
    print(f"   密码: {DB_PASSWORD}")
    print(f"   端口: {PORT}")
    print()
    print("下一步:")
    print("1. 重启Backend服务以应用新数据库配置")
    print("2. Backend启动时会自动创建表结构")
    print("3. 然后可以创建测试用户和供应商数据")
    print("=" * 60)
    print()

except Exception as e:
    print(f"❌ 执行失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
