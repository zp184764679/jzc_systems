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

# 检查数据库URI是否已从.env加载
if not os.environ.get('SQLALCHEMY_DATABASE_URI'):
    print('[celery_app] 警告: SQLALCHEMY_DATABASE_URI 未在 .env 中配置')
    raise RuntimeError('SQLALCHEMY_DATABASE_URI 环境变量未设置，请检查 .env 文件')

print(f'[celery_app] 工作目录: {os.getcwd()}')
print(f'[celery_app] DATABASE_URI: ***已配置***')

# 现在才导入app
from app import app
from extensions import celery, init_celery

# 初始化Celery配置并绑定Flask上下文
init_celery(app)

# 暴露给 celery -A 命令的实例
__all__ = ['celery', 'app']
