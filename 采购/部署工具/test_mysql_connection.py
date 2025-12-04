# -*- coding: utf-8 -*-
"""
MySQL连接测试脚本
测试本地和远程MySQL连接
"""
import sys
import os

# 添加backend路径
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
sys.path.insert(0, backend_path)

print("=" * 60)
print("🔍 MySQL连接测试")
print("=" * 60)
print()

# 测试1: 导入依赖
print("测试1: 检查依赖...")
try:
    import pymysql
    print("✅ pymysql 已安装")
except ImportError:
    print("❌ pymysql 未安装")
    print("请运行: pip install pymysql")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv 已安装")
except ImportError:
    print("❌ python-dotenv 未安装")
    print("请运行: pip install python-dotenv")
    sys.exit(1)

print()

# 测试2: 加载配置
print("测试2: 加载配置文件...")
env_path = os.path.join(backend_path, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ 已加载配置: {env_path}")
else:
    print(f"❌ 配置文件不存在: {env_path}")
    sys.exit(1)

db_host = os.getenv('DB_HOST', 'localhost')
db_port = int(os.getenv('DB_PORT', 3306))
db_user = os.getenv('DB_USER', 'root')
db_password = os.getenv('DB_PASSWORD', '')
db_name = os.getenv('DB_NAME', 'caigou_local')

print(f"   主机: {db_host}")
print(f"   端口: {db_port}")
print(f"   用户: {db_user}")
print(f"   数据库: {db_name}")
print()

# 测试3: 连接数据库
print("测试3: 连接MySQL数据库...")
try:
    connection = pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    print("✅ 数据库连接成功！")

    # 测试4: 执行查询
    print()
    print("测试4: 执行测试查询...")
    with connection.cursor() as cursor:
        # 查询数据库版本
        cursor.execute("SELECT VERSION() as version")
        result = cursor.fetchone()
        print(f"✅ MySQL版本: {result['version']}")

        # 查询当前数据库
        cursor.execute("SELECT DATABASE() as current_db")
        result = cursor.fetchone()
        print(f"✅ 当前数据库: {result['current_db']}")

        # 查询所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        if tables:
            print(f"✅ 数据库表数量: {len(tables)}")
            print("   表列表:")
            for table in tables[:10]:  # 只显示前10个
                table_name = list(table.values())[0]
                print(f"   - {table_name}")
        else:
            print("⚠️  数据库中还没有表")

    connection.close()
    print()

except pymysql.err.OperationalError as e:
    print(f"❌ 连接失败: {e}")
    print()
    print("可能的原因:")
    print("1. MySQL服务未启动")
    print("2. 用户名或密码错误")
    print("3. 数据库不存在")
    print("4. 防火墙阻止连接")
    sys.exit(1)
except Exception as e:
    print(f"❌ 未知错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 60)
print("✅ 所有测试通过！MySQL连接正常")
print("=" * 60)
