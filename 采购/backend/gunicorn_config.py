# Gunicorn配置文件
import multiprocessing
import os

# 监听地址和端口
bind = "0.0.0.0:5001"

# Worker进程数（推荐：CPU核心数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

# Worker类型（gevent适合IO密集型应用）
worker_class = "gevent"

# 每个Worker的协程数
worker_connections = 1000

# 超时时间（秒）
timeout = 120

# 保持连接时间
keepalive = 5

# 日志配置
accesslog = "/home/admin/caigou-prod/backend/logs/gunicorn_access.log"
errorlog = "/home/admin/caigou-prod/backend/logs/gunicorn_error.log"
loglevel = "info"

# 进程名称
proc_name = "caigou_backend"

# 后台运行
daemon = False

# PID文件
pidfile = "/home/admin/caigou-prod/backend/gunicorn.pid"

# 优雅重启超时
graceful_timeout = 30

# 预加载应用
preload_app = True

# 最大请求数（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50
