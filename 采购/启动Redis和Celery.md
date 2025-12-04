# Redis 和 Celery 快速启动指南

## 方案 A: Docker 启动 (推荐，最简单) 🐳

### 前置条件
下载安装 Docker Desktop for Windows: https://www.docker.com/products/docker-desktop

### 启动 Redis
```bash
# 启动Redis容器 (后台运行，开机自动启动)
docker run -d --name redis-caigou -p 6379:6379 --restart always redis:latest

# 验证
docker ps
redis-cli ping
# 应输出: PONG
```

---

## 方案 B: Windows 原生安装

### 下载 Redis for Windows
```bash
# 从 GitHub 下载最新版
# https://github.com/tporadowski/redis/releases

# 下载 Redis-x64-5.0.14.1.zip
# 解压到 C:\Redis
```

### 启动 Redis
```bash
cd C:\Redis
redis-server.exe
# 保持窗口开启
```

### 设置为Windows服务 (开机自启)
```bash
cd C:\Redis
redis-server.exe --service-install
redis-server.exe --service-start

# 验证
redis-cli ping
```

---

## 启动 Celery Worker ⚙️

### Windows 启动命令
```bash
cd C:\Users\Admin\Desktop\采购\backend

# 方式1: 使用 solo 池 (推荐，简单)
celery -A celery_app worker --pool=solo --loglevel=info

# 方式2: 使用 eventlet (需先安装)
pip install eventlet
celery -A celery_app worker --pool=eventlet --loglevel=info
```

---

## 一键启动脚本 🚀

创建 `启动后台服务.bat`:

```batch
@echo off
echo ========================================
echo 启动采购系统后台服务
echo ========================================

echo.
echo [1/3] 检查 Redis...
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Redis 未运行，正在启动...
    start "Redis Server" redis-server
    timeout /t 2 >nul
) else (
    echo ✅ Redis 已运行
)

echo.
echo [2/3] 启动 Celery Worker...
cd /d C:\Users\Admin\Desktop\采购\backend
start "Celery Worker" cmd /k "celery -A celery_app worker --pool=solo --loglevel=info"

echo.
echo [3/3] 启动 Flask 后端...
start "Flask Backend" cmd /k "python app.py"

echo.
echo ========================================
echo ✅ 所有服务已启动！
echo ========================================
echo.
echo 打开的窗口:
echo   - Redis Server (如果之前未运行)
echo   - Celery Worker
echo   - Flask Backend
echo.
echo 按任意键退出...
pause >nul
```

保存后双击运行。

---

## 验证服务状态 ✅

### 1. Redis
```bash
redis-cli ping
# 输出: PONG
```

### 2. Celery
```python
# 在Python中测试
from celery_app import celery

# 检查worker
celery.control.inspect().active()
# 应返回: {'celery@HOSTNAME': []}
```

### 3. 测试异步任务
```python
from tasks.notify_rfq import send_rfq_notification

# 创建测试任务
result = send_rfq_notification.delay(1)
print(f"Task ID: {result.id}")
print(f"Status: {result.status}")
```

---

## 故障排查 🔧

### 问题1: Redis 连接失败
```bash
# 检查端口占用
netstat -ano | findstr :6379

# 检查进程
tasklist | findstr redis

# 重启Redis
redis-cli shutdown
redis-server
```

### 问题2: Celery Worker 无法启动
```bash
# 检查错误日志
celery -A celery_app worker --pool=solo --loglevel=debug

# 常见问题：
# - 端口6379被占用 → 关闭其他Redis进程
# - 导入错误 → 检查celery_app.py路径
```

### 问题3: 任务不执行
```bash
# 检查Celery worker是否连接到Redis
celery -A celery_app inspect active

# 检查队列
celery -A celery_app inspect registered

# 清空队列（如果任务堆积）
celery -A celery_app purge
```

---

## 性能监控 📊

### Flower - Celery监控面板
```bash
# 安装
pip install flower

# 启动
celery -A celery_app flower --port=5555

# 访问
http://localhost:5555
```

---

## 开机自启动配置 (可选)

### 方式1: Windows 任务计划程序
1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：系统启动时
4. 操作：启动程序 → `C:\Users\Admin\Desktop\采购\启动后台服务.bat`

### 方式2: 注册为Windows服务
使用 NSSM (Non-Sucking Service Manager):
```bash
# 下载 NSSM: https://nssm.cc/download

# 安装Celery为服务
nssm install CeleryWorker "C:\Users\Admin\Desktop\采购\backend\venv\Scripts\celery.exe"
nssm set CeleryWorker AppParameters "-A celery_app worker --pool=solo --loglevel=info"
nssm set CeleryWorker AppDirectory "C:\Users\Admin\Desktop\采购\backend"
nssm start CeleryWorker
```

---

完成！现在你的系统支持后台任务处理了 🎉
