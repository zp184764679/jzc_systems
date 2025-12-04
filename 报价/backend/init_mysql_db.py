"""
MySQL数据库初始化脚本
创建数据库和所有表结构
执行时间: 2025-11-14
"""
import pymysql
from sqlalchemy import create_engine
from config.settings import settings
from config.database import Base
from models.drawing import Drawing
from models.material import Material
from models.process import Process
from models.quote import Quote

def create_database():
    """创建数据库（如果不存在）"""
    # 尝试不同的密码连接MySQL服务器（不指定数据库）
    passwords = ['', 'root', '123456']  # 尝试空密码、root、123456
    connection = None

    for pwd in passwords:
        try:
            print(f"尝试使用密码: {'(empty)' if not pwd else '******'}")
            connection = pymysql.connect(
                host='localhost',
                user='root',
                password=pwd,
                charset='utf8mb4'
            )
            print(f"✅ 连接成功！")
            break
        except pymysql.err.OperationalError as e:
            if '1045' in str(e):  # Access denied
                continue
            else:
                raise

    if not connection:
        raise Exception("无法连接到MySQL服务器，请检查MySQL是否运行以及root密码")

    try:
        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute("CREATE DATABASE IF NOT EXISTS quote_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ 数据库 quote_system 已创建或已存在")
        connection.commit()
        return pwd  # 返回工作的密码
    finally:
        connection.close()

def create_tables(password):
    """创建所有表结构"""
    # 更新DATABASE_URL使用正确的密码
    db_url = f"mysql+pymysql://root:{password}@localhost:3306/quote_system?charset=utf8mb4"
    engine = create_engine(db_url, echo=True)

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("\n✅ 所有表结构已创建")
    return db_url

def verify_tables(password):
    """验证表是否创建成功"""
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password=password,
        database='quote_system',
        charset='utf8mb4'
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print("\n数据库中的表:")
            for table in tables:
                print(f"  - {table[0]}")

            # 检查processes表的字段
            cursor.execute("DESCRIBE processes")
            columns = cursor.fetchall()
            print("\nprocesses表字段:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
    finally:
        connection.close()

if __name__ == "__main__":
    print("=" * 50)
    print("开始初始化MySQL数据库")
    print("=" * 50)

    print("\n[1/3] 创建数据库...")
    working_password = create_database()

    print("\n[2/3] 创建表结构...")
    db_url = create_tables(working_password)

    print("\n[3/3] 验证表结构...")
    verify_tables(working_password)

    print("\n" + "=" * 50)
    print("✅ MySQL数据库初始化完成！")
    print(f"✅ 数据库URL: {db_url}")
    print("=" * 50)
    print("\n提示：请确保 config/settings.py 中的 DATABASE_URL 使用正确的密码")
