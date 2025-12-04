# -*- coding: utf-8 -*-
"""
创建测试数据：用户和供应商
"""
import sys
import os

# 添加backend路径以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, db
from models.user import User
from models.supplier import Supplier
from werkzeug.security import generate_password_hash
from datetime import datetime

print("=" * 60)
print("📊 创建测试数据")
print("=" * 60)
print()

try:
    with app.app_context():
        # 1. 创建测试用户 - 周鹏
        print("[1/3] 创建测试用户: 周鹏...")

        # 检查用户是否已存在
        existing_user = User.query.filter_by(email='jzchardware@gmail.com').first()
        if existing_user:
            print("⚠️  用户已存在，跳过")
            user = existing_user
        else:
            user = User(
                username='周鹏',
                email='jzchardware@gmail.com',
                phone='13590217332',
                password_hash=generate_password_hash('123456'),  # 默认密码: 123456
                role='admin',  # 管理员权限
                is_active=True,
                created_at=datetime.now()
            )
            db.session.add(user)
            db.session.commit()
            print(f"✅ 用户创建成功 (ID: {user.id})")
            print(f"   用户名: {user.username}")
            print(f"   邮箱: {user.email}")
            print(f"   电话: {user.phone}")
            print(f"   密码: 123456")

        print()

        # 2. 创建测试供应商1
        print("[2/3] 创建测试供应商1...")

        supplier1 = Supplier.query.filter_by(name='深圳市XX电子有限公司').first()
        if supplier1:
            print("⚠️  供应商1已存在，跳过")
        else:
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
            print(f"   联系人: {supplier1.contact_person}")

        print()

        # 3. 创建测试供应商2
        print("[3/3] 创建测试供应商2...")

        supplier2 = Supplier.query.filter_by(name='广州YY科技有限公司').first()
        if supplier2:
            print("⚠️  供应商2已存在，跳过")
        else:
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
            print(f"   联系人: {supplier2.contact_person}")

        print()
        print("=" * 60)
        print("✅ 所有测试数据创建完成！")
        print("=" * 60)
        print()
        print("📊 测试账号信息:")
        print(f"   用户名: 周鹏")
        print(f"   邮箱: jzchardware@gmail.com")
        print(f"   电话: 13590217332")
        print(f"   密码: 123456")
        print(f"   角色: admin")
        print()
        print("🏭 测试供应商:")
        print("   1. 深圳市XX电子有限公司 (电子元器件)")
        print("   2. 广州YY科技有限公司 (机械设备)")
        print()
        print("现在可以使用上述账号登录系统了！")
        print("=" * 60)

except Exception as e:
    print(f"❌ 创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
