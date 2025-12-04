# WSL 生产环境部署指南

## 📋 目录

1. [系统架构](#系统架构)
2. [环境准备](#环境准备)
3. [部署步骤](#部署步骤)
4. [服务配置](#服务配置)
5. [监控和维护](#监控和维护)
6. [问题排查](#问题排查)

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                Windows主机 (开发环境)                      │
│                                                          │
│  ┌──────────────┐                                       │
│  │ Vite Dev     │  http://localhost:3000               │
│  │ Flask Dev    │  http://localhost:5001               │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
                        │
                        │ 共享 MySQL
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  WSL (生产环境)                           │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ Nginx (反向代理)                                │    │
│  │   ├─ http://61.145.212.28:3000 → Frontend     │    │
│  │   └─ http://61.145.212.28:5001 → Backend      │    │
│  └────────────────────────────────────────────────┘    │
│         │                            │                  │
│         ↓                            ↓                  │
│  ┌────────────┐            ┌──────────────────┐       │
│  │  Frontend  │            │  Gunicorn        │       │
│  │  (静态文件) │            │  (4 workers)     │       │
│  └────────────┘            └──────────────────┘       │
│                                     │                   │
│                                     ↓                   │
│                            ┌──────────────────┐        │
│                            │  Celery Worker   │        │
│                            └──────────────────┘        │
│                                     │                   │
│                                     ↓                   │
│                            ┌──────────────────┐        │
│                            │  Redis           │        │
│                            └──────────────────┘        │
└─────────────────────────────────────────────────────────┘
                        │
                        ↓
              ┌──────────────────┐
              │  MySQL数据库      │ ← 当前共用Windows上的
              │  (localhost:3306) │
              └──────────────────┘
```

---

## 🔧 环境准备

### 1. WSL安装和配置

```bash
# Windows PowerShell中安装WSL2
wsl --install -d Ubuntu-22.04

# 进入WSL
wsl

# 更新系统
sudo apt update && sudo apt upgrade -y
```

### 2. 安装必要软件

```bash
# 安装Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# 安装Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# 安装Nginx
sudo apt install nginx -y

# 安装Redis
sudo apt install redis-server -y

# 安装MySQL客户端（连接Windows上的MySQL）
sudo apt install mysql-client -y

# 安装其他依赖
sudo apt install git supervisor -y
```

### 3. 验证安装

```bash
python3 --version    # 应该是 3.11.x
node --version       # 应该是 v18.x.x
npm --version
nginx -v
redis-cli --version
mysql --version
```

---

## 📦 部署步骤

### 步骤1：复制项目到WSL

```bash
# 方法A：直接访问Windows文件系统
cd ~
cp -r /mnt/c/Users/Admin/Desktop/采购 ~/caigou-system

# 方法B：使用git（推荐）
cd ~
git clone <your-repo-url> caigou-system

cd ~/caigou-system
```

### 步骤2：切换到生产环境配置

```bash
cd ~/caigou-system/backend
cp .env.production .env

# 验证配置
cat .env | grep FLASK_ENV
# 应该显示：FLASK_ENV=production
```

### 步骤3：安装后端依赖

```bash
cd ~/caigou-system/backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装Gunicorn
pip install gunicorn gevent

# 验证安装
gunicorn --version
```

### 步骤4：构建前端

```bash
cd ~/caigou-system/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 构建完成后，静态文件在 dist/ 目录
ls -la dist/
```

### 步骤5：配置MySQL连接

由于当前共用Windows上的MySQL，需要确保WSL可以访问：

```bash
# 测试连接Windows上的MySQL
# WSL访问Windows的localhost需要使用特殊地址

# 获取Windows主机IP（在WSL中）
cat /etc/resolv.conf | grep nameserver | awk '{print $2}'

# 或者使用这个命令
ip route show | grep -i default | awk '{ print $3}'

# 假设得到的IP是 172.24.208.1
# 修改 .env 文件中的 DB_HOST
nano ~/caigou-system/backend/.env

# 修改为：
# DB_HOST=172.24.208.1  （你实际得到的IP）
```

**重要：** 需要在Windows上的MySQL配置允许远程连接：

```sql
-- 在Windows上运行MySQL命令
mysql -u root -pexak472008

-- 允许从WSL IP连接
GRANT ALL PRIVILEGES ON caigou.* TO 'root'@'172.24.%' IDENTIFIED BY 'exak472008';
FLUSH PRIVILEGES;
```

### 步骤6：测试后端启动

```bash
cd ~/caigou-system/backend
source venv/bin/activate

# 测试Flask应用
python app.py

# 测试Gunicorn
gunicorn -w 1 -b 0.0.0.0:5001 app:app

# 如果启动成功，按Ctrl+C停止
```

---

## ⚙️ 服务配置

### 1. Gunicorn配置文件

创建 `~/caigou-system/backend/gunicorn_config.py`：

```python
# Gunicorn配置文件
import multiprocessing

# 服务器绑定
bind = "127.0.0.1:5001"

# 工作进程数
workers = 4

# 每个进程的线程数
threads = 2

# 工作模式
worker_class = "gevent"

# 超时时间
timeout = 120

# 最大请求数（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50

# 日志
accesslog = "/home/admin/caigou-system/logs/gunicorn-access.log"
errorlog = "/home/admin/caigou-system/logs/gunicorn-error.log"
loglevel = "info"

# 优雅重启
graceful_timeout = 30

# 守护进程（使用Supervisor时设为False）
daemon = False

# 进程名称
proc_name = "caigou-backend"
```

### 2. Nginx配置

创建 `/etc/nginx/sites-available/caigou`：

```bash
sudo nano /etc/nginx/sites-available/caigou
```

```nginx
# 采购系统 Nginx 配置

# 后端API服务
upstream backend {
    server 127.0.0.1:5001;
    keepalive 64;
}

# 前端静态文件服务
server {
    listen 3000;
    server_name 61.145.212.28;

    # 前端静态文件
    root /home/admin/caigou-system/frontend/dist;
    index index.html;

    # Gzip压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    gzip_min_length 1000;

    # 前端路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 访问日志
    access_log /var/log/nginx/caigou-frontend-access.log;
    error_log /var/log/nginx/caigou-frontend-error.log;
}

# 后端API服务
server {
    listen 5001;
    server_name 61.145.212.28;

    # 客户端最大请求体大小
    client_max_body_size 50M;

    # 代理到后端
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 访问日志
    access_log /var/log/nginx/caigou-backend-access.log;
    error_log /var/log/nginx/caigou-backend-error.log;
}
```

启用配置：

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/caigou /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

### 3. Supervisor配置（守护进程）

创建 `/etc/supervisor/conf.d/caigou-backend.conf`：

```bash
sudo nano /etc/supervisor/conf.d/caigou-backend.conf
```

```ini
[program:caigou-backend]
directory=/home/admin/caigou-system/backend
command=/home/admin/caigou-system/backend/venv/bin/gunicorn -c gunicorn_config.py app:app
user=admin
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/admin/caigou-system/logs/supervisor-backend.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=10
environment=PATH="/home/admin/caigou-system/backend/venv/bin"
```

创建 `/etc/supervisor/conf.d/caigou-celery.conf`：

```bash
sudo nano /etc/supervisor/conf.d/caigou-celery.conf
```

```ini
[program:caigou-celery]
directory=/home/admin/caigou-system/backend
command=/home/admin/caigou-system/backend/venv/bin/celery -A celery_app.celery worker --loglevel=info --concurrency=4
user=admin
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/admin/caigou-system/logs/supervisor-celery.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=10
environment=PATH="/home/admin/caigou-system/backend/venv/bin"
```

启动服务：

```bash
# 创建日志目录
mkdir -p ~/caigou-system/logs

# 重新加载Supervisor配置
sudo supervisorctl reread
sudo supervisorctl update

# 启动服务
sudo supervisorctl start caigou-backend
sudo supervisorctl start caigou-celery

# 查看状态
sudo supervisorctl status
```

### 4. Redis配置

```bash
# 编辑Redis配置
sudo nano /etc/redis/redis.conf

# 修改以下配置：
# 1. 绑定地址（仅本地访问）
bind 127.0.0.1

# 2. 设置密码（可选）
# requirepass your_strong_password

# 3. 持久化
save 900 1
save 300 10
save 60 10000

# 重启Redis
sudo systemctl restart redis
sudo systemctl enable redis
```

---

## 🚀 启动服务

### 一键启动所有服务

```bash
# 启动MySQL（如果需要）
# 当前共用Windows上的MySQL，无需启动

# 启动Redis
sudo systemctl start redis

# 启动Nginx
sudo systemctl start nginx

# 启动Backend和Celery（通过Supervisor）
sudo supervisorctl start caigou-backend
sudo supervisorctl start caigou-celery

# 查看状态
sudo supervisorctl status
```

### 验证服务

```bash
# 检查端口监听
sudo netstat -tlnp | grep -E "3000|5001|6379"

# 测试Backend
curl http://localhost:5001/api/health

# 测试Frontend
curl http://localhost:3000

# 从Windows访问
# 浏览器打开: http://61.145.212.28:3000
```

---

## 📊 监控和维护

### 查看日志

```bash
# Backend日志
tail -f ~/caigou-system/logs/gunicorn-error.log
tail -f ~/caigou-system/logs/supervisor-backend.log

# Celery日志
tail -f ~/caigou-system/logs/supervisor-celery.log

# Nginx日志
sudo tail -f /var/log/nginx/caigou-backend-access.log
sudo tail -f /var/log/nginx/caigou-frontend-access.log

# Redis日志
sudo tail -f /var/log/redis/redis-server.log
```

### 重启服务

```bash
# 重启Backend
sudo supervisorctl restart caigou-backend

# 重启Celery
sudo supervisorctl restart caigou-celery

# 重启Nginx
sudo systemctl restart nginx

# 重启Redis
sudo systemctl restart redis
```

### 更新代码

```bash
# 进入项目目录
cd ~/caigou-system

# 拉取最新代码
git pull

# 更新后端
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart caigou-backend
sudo supervisorctl restart caigou-celery

# 更新前端
cd ../frontend
npm install
npm run build
sudo systemctl reload nginx
```

---

## 🔍 问题排查

### 问题1：无法连接MySQL

```bash
# 检查Windows IP
ip route show | grep -i default | awk '{ print $3}'

# 测试连接
mysql -h 172.24.208.1 -u root -pexak472008 -e "SELECT 1"

# 如果连接失败：
# 1. 检查Windows防火墙是否允许3306端口
# 2. 检查MySQL是否允许远程连接
# 3. 确认.env中的DB_HOST配置正确
```

### 问题2：Gunicorn启动失败

```bash
# 查看详细错误
cd ~/caigou-system/backend
source venv/bin/activate
gunicorn -c gunicorn_config.py app:app --log-level debug

# 检查端口占用
sudo netstat -tlnp | grep 5001

# 检查Python路径
which python
which gunicorn
```

### 问题3：Nginx 502错误

```bash
# 检查Backend是否运行
sudo supervisorctl status caigou-backend

# 检查Backend端口
curl http://localhost:5001/api/health

# 查看Nginx错误日志
sudo tail -50 /var/log/nginx/caigou-backend-error.log

# 重启服务
sudo supervisorctl restart caigou-backend
sudo systemctl restart nginx
```

### 问题4：前端页面空白

```bash
# 检查dist目录
ls -la ~/caigou-system/frontend/dist/

# 检查Nginx配置
sudo nginx -t

# 查看浏览器控制台错误
# 检查API请求是否成功

# 重新构建
cd ~/caigou-system/frontend
npm run build
sudo systemctl reload nginx
```

---

## ✅ 部署检查清单

部署完成后，请检查以下项目：

### 基础服务
- [ ] Redis运行正常：`sudo systemctl status redis`
- [ ] Nginx运行正常：`sudo systemctl status nginx`
- [ ] Backend运行正常：`sudo supervisorctl status caigou-backend`
- [ ] Celery运行正常：`sudo supervisorctl status caigou-celery`

### 网络访问
- [ ] 前端页面可访问：http://61.145.212.28:3000
- [ ] 后端API可访问：http://61.145.212.28:5001/api/health
- [ ] 可以正常登录
- [ ] 企业微信扫码登录可用

### 功能测试
- [ ] 用户登录功能正常
- [ ] 数据库读写正常
- [ ] Celery任务执行正常
- [ ] 文件上传功能正常
- [ ] 企业微信通知功能正常

### 日志和监控
- [ ] 日志目录存在且可写
- [ ] 日志正常记录
- [ ] 错误日志无异常
- [ ] 监控告警配置（如有）

---

## 📞 技术支持

如遇到问题，请：

1. 查看对应服务的日志
2. 检查配置文件
3. 参考本文档的问题排查章节
4. 导出日志文件寻求帮助

---

**最后更新：2025-01-08**
