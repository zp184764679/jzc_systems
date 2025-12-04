# -*- coding: utf-8 -*-
"""
快速初始化远程数据库 - 创建测试用户和供应商
"""
import sys
import os

# 添加backend路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, db
from models.user import User
from models.supplier import Supplier
from werkzeug.security import generate_password_hash
from datetime import datetime

print("=" * 60)
print("🚀 快速初始化远程数据库")
print("=" * 60)
print()

try:
    with app.app_context():
        # 删除所有表并重新创建
        print("[1/4] 重建数据库表结构...")
        db.drop_all()
        db.create_all()
        print("✅ 表结构已重建")
        print()

        # 2. 创建测试用户 - 周鹏（管理员）
        print("[2/4] 创建管理员账户: 周鹏...")

        user1 = User(
            username='周鹏',
            email='jzchardware@gmail.com',
            phone='13590217332',
            password_hash=generate_password_hash('exak472008'),
            role='admin',
            status='approved',  # 已审批
            created_at=datetime.now()
        )
        db.session.add(user1)

        # 创建测试用户 - exzzz
        print("[2/4] 创建测试用户: exzzz...")

        user2 = User(
            username='exzzz',
            email='exzzz@test.com',
            phone='13800000000',
            password_hash=generate_password_hash('exak472008'),
            role='user',
            status='approved',  # 已审批
            created_at=datetime.now()
        )
        db.session.add(user2)
        db.session.commit()

        print(f"✅ 管理员创建成功 (ID: {user1.id})")
        print(f"   用户名: {user1.username}")
        print(f"   邮箱: {user1.email}")
        print(f"   电话: {user1.phone}")
        print(f"   密码: exak472008")
        print(f"   角色: admin")
        print()
        print(f"✅ 测试用户创建成功 (ID: {user2.id})")
        print(f"   用户名: {user2.username}")
        print(f"   邮箱: {user2.email}")
        print(f"   密码: exak472008")
        print(f"   角色: user")
        print()

        # 3. 创建测试供应商1
        print("[3/4] 创建测试供应商1...")

        supplier1 = Supplier(
            name='深圳市XX电子有限公司',
            contact_person='张经理',
            contact_phone='0755-12345678',
            contact_email='zhang@xxdz.com',
            address='深圳市南山区科技园',
            description='主营：电子元器件、集成电路、传感器等',
            category='电子元器件',
            status='active',
            created_at=datetime.now()
        )
        db.session.add(supplier1)
        db.session.commit()
        print(f"✅ 供应商1创建成功 (ID: {supplier1.id})")
        print(f"   名称: {supplier1.name}")
        print(f"   分类: {supplier1.category}")
        print()

        # 4. 创建测试供应商2
        print("[4/4] 创建测试供应商2...")

        supplier2 = Supplier(
            name='广州YY科技有限公司',
            contact_person='李总',
            contact_phone='020-87654321',
            contact_email='li@yykj.com',
            address='广州市天河区珠江新城',
            description='主营：工业自动化设备、机械零部件、五金工具等',
            category='机械设备',
            status='active',
            created_at=datetime.now()
        )
        db.session.add(supplier2)
        db.session.commit()
        print(f"✅ 供应商2创建成功 (ID: {supplier2.id})")
        print(f"   名称: {supplier2.name}")
        print(f"   分类: {supplier2.category}")
        print()

        print("=" * 60)
        print("✅ 所有数据初始化完成！")
        print("=" * 60)
        print()
        print("📊 测试账号信息:")
        print()
        print("   👤 管理员账户:")
        print("      用户名: 周鹏")
        print("      邮箱: jzchardware@gmail.com")
        print("      电话: 13590217332")
        print("      密码: exak472008")
        print("      角色: admin")
        print()
        print("   👤 测试用户:")
        print("      用户名: exzzz")
        print("      邮箱: exzzz@test.com")
        print("      密码: exak472008")
        print("      角色: user")
        print()
        print("🏭 测试供应商:")
        print("   1. 深圳市XX电子有限公司 (电子元器件)")
        print("   2. 广州YY科技有限公司 (机械设备)")
        print()
        print("现在可以重启Backend并测试登录了！")
        print("=" * 60)

except Exception as e:
    print(f"❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
