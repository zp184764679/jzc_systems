#!/bin/bash
# Gunicorn启动脚本

cd /home/admin/caigou-prod/backend
source venv/bin/activate

# 设置环境变量
export FLASK_APP=app.py
export PYTHONPATH=/home/admin/caigou-prod/backend

# 启动Gunicorn
gunicorn -c gunicorn_config.py app:app
