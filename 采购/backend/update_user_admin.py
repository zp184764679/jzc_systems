#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新最新注册的用户为超级管理员
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db
from models.user import User
from datetime import datetime

def update_latest_user():
    """将最新注册的用户设置为已审核通过的超级管理员"""

    with app.app_context():
        # 查找最新注册的用户
        latest_user = User.query.order_by(User.created_at.desc()).first()

        if not latest_user:
            print("❌ 没有找到任何用户")
            return False

        print(f"\n找到最新注册用户:")
        print(f"  ID: {latest_user.id}")
        print(f"  用户名: {latest_user.username}")
        print(f"  邮箱: {latest_user.email}")
        print(f"  当前状态: {latest_user.status}")
        print(f"  当前角色: {latest_user.role}")
        print(f"  注册时间: {latest_user.created_at}")

        # 更新状态和角色
        old_status = latest_user.status
        old_role = latest_user.role

        latest_user.status = 'approved'
        latest_user.role = 'super_admin'

        try:
            db.session.commit()
            print(f"\n✅ 更新成功!")
            print(f"  状态: {old_status} → {latest_user.status}")
            print(f"  角色: {old_role} → {latest_user.role}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 更新失败: {e}")
            return False

if __name__ == '__main__':
    success = update_latest_user()
    sys.exit(0 if success else 1)
