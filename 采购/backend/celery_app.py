# celery_app.py
# -*- coding: utf-8 -*-
"""
Celery应用入口文件
用于 celery -A celery_app worker 命令启动
"""
import os
import sys
from dotenv import load_dotenv

# 确保当前目录正确
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

# ⭐ 关键修复：在导入app之前加载环境变量
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

# 强制设置数据库URI到环境变量（确保worker子进程也能获取）
if not os.environ.get('SQLALCHEMY_DATABASE_URI'):
    os.environ['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://zhoupeng:ZPexak472008%40@127.0.0.1:3307/caigou?charset=utf8mb4'

print(f'[celery_app] 工作目录: {os.getcwd()}')
print(f'[celery_app] DATABASE_URI: {os.environ.get("SQLALCHEMY_DATABASE_URI", "NOT_SET")}')

# 现在才导入app
from app import app
from extensions import celery, init_celery

# 初始化Celery配置并绑定Flask上下文
init_celery(app)

# 暴露给 celery -A 命令的实例
__all__ = ['celery', 'app']
