#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
os.environ["FLASK_APP"] = "app.py"

from flask import Flask
from werkzeug.security import generate_password_hash
from extensions import db
from models.user import User

# 直接import app
import app as app_module

# 获取app实例
app = app_module.app

with app.app_context():
    user = User.query.filter_by(email="jzchardware@gmail.com").first()
    if user:
        user.password_hash = generate_password_hash("exak472008")
        db.session.commit()
        print(f"✅ 已更新用户 {user.username} 的密码为: exak472008")
    else:
        print("❌ 用户不存在")
