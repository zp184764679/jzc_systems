#!/bin/bash
# 前端生产环境服务脚本
# 使用vite preview命令服务已构建的dist目录

cd /home/admin/caigou-prod/frontend
npx vite preview --host 0.0.0.0 --port 5003
