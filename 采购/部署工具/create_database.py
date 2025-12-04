# -*- coding: utf-8 -*-
"""
自动创建MySQL数据库和用户
不需要交互输入密码
"""
import pymysql
import sys

print("=" * 60)
print("📊 创建MySQL数据库和用户")
print("=" * 60)
print()

# MySQL连接配置 - 尝试多种可能的root密码
ROOT_PASSWORDS = ['', 'root', 'exak472008', 'Exak472008']
HOST = 'localhost'
PORT = 3306

# 数据库配置
DB_NAME = 'caigou_local'
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
    print("请手动执行以下命令:")
    print("1. 打开命令提示符")
    print("2. 运行: mysql -u root -p")
    print("3. 输入root密码")
    print("4. 执行: source C:/Users/Admin/Desktop/采购/部署工具/setup_mysql_local.sql")
    sys.exit(1)

print()

try:
    with connection.cursor() as cursor:
        # 1. 删除旧数据库(如果存在)
        print("[1/7] 删除旧数据库(如果存在)...")
        cursor.execute("DROP DATABASE IF EXISTS caigou_local")
        print("✅ 完成")

        # 2. 创建新数据库
        print()
        print("[2/7] 创建新数据库...")
        cursor.execute("""
            CREATE DATABASE caigou_local
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci
        """)
        print("✅ 数据库 caigou_local 已创建")

        # 3-6. 创建用户(删除旧用户,创建新用户)
        hosts = [
            ('localhost', '本地访问'),
            ('192.168.0.%', '局域网访问'),
            ('172.%', 'WSL2访问'),
            ('%', '任意IP访问')
        ]

        for idx, (host, desc) in enumerate(hosts, start=3):
            print()
            print(f"[{idx}/7] 配置{desc} ({host})...")

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
        print("[7/7] 刷新权限...")
        cursor.execute("FLUSH PRIVILEGES")
        print("✅ 权限已刷新")

        # 验证创建的用户
        print()
        print("验证创建的用户:")
        cursor.execute("""
            SELECT User, Host
            FROM mysql.user
            WHERE User = %s
        """, (DB_USER,))
        users = cursor.fetchall()
        for user in users:
            print(f"  ✓ {user['User']}@{user['Host']}")

    connection.commit()
    print()
    print("=" * 60)
    print("✅ 所有配置完成！")
    print("=" * 60)
    print()
    print("📊 数据库信息:")
    print(f"   数据库名: {DB_NAME}")
    print(f"   用户名: {DB_USER}")
    print(f"   密码: {DB_PASSWORD}")
    print(f"   端口: {PORT}")
    print()
    print("🌐 可访问方式:")
    print("   本地: localhost")
    print("   局域网: 192.168.0.x")
    print("   WSL2: 172.x.x.x")
    print("   外网: 任意IP (需配置防火墙)")
    print()

except Exception as e:
    print(f"❌ 执行失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if connection:
        connection.close()
