#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Celery Worker 启动脚本
"""
import os
import sys

# 确保当前目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ['FLASK_APP'] = 'app.py'

# 导入并启动 Celery
from celery_app import celery

if __name__ == '__main__':
    # 使用 worker 命令启动
    celery.worker_main([
        'worker',
        '--loglevel=info',
        '--pool=solo',  # Windows 使用 solo 池
        '--concurrency=2',
    ])
