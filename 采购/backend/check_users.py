#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check users in caigou database"""
import sys
sys.path.insert(0, '.')

from app import app, db
from models.user import User

with app.app_context():
    users = User.query.all()
    print("Users in caigou DB:")
    for u in users:
        print(f"  id={u.id}, email={u.email}, username={u.username}, status={u.status}, role={u.role}")

    if not users:
        print("  (No users found)")
