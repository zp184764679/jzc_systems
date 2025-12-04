#!/bin/bash
# ====================================================
# Ubuntu生产环境部署配置脚本
# 连接Windows MySQL数据库
# ====================================================

set -e  # 遇到错误立即退出

WINDOWS_IP="192.168.0.6"  # Windows的局域网IP,根据实际情况修改
BACKEND_DIR="/opt/caigou/backend"
FRONTEND_DIR="/opt/caigou/frontend"

echo "===================================================="
echo "🚀 采购系统Ubuntu部署配置"
echo "===================================================="
echo ""

# ============================================
# 步骤1: 检查网络连接
# ============================================
echo "[1/8] 检查Windows MySQL连接..."
if ping -c 2 $WINDOWS_IP > /dev/null 2>&1; then
    echo "✅ Windows主机 $WINDOWS_IP 可访问"
else
    echo "❌ 无法访问Windows主机 $WINDOWS_IP"
    echo "请检查:"
    echo "  1. Windows防火墙是否允许ICMP"
    echo "  2. 网络连接是否正常"
    echo "  3. IP地址是否正确"
    exit 1
fi

# 测试MySQL端口
if timeout 5 bash -c "cat < /dev/null > /dev/tcp/$WINDOWS_IP/3306" 2>/dev/null; then
    echo "✅ MySQL端口3306可访问"
else
    echo "❌ 无法访问MySQL端口3306"
    echo "请检查:"
    echo "  1. Windows防火墙是否允许3306端口"
    echo "  2. MySQL服务是否运行"
    echo "  3. MySQL配置bind-address = 0.0.0.0"
    exit 1
fi

echo ""

# ============================================
# 步骤2: 安装系统依赖
# ============================================
echo "[2/8] 安装系统依赖..."
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    redis-server \
    mysql-client \
    supervisor \
    git \
    curl

echo "✅ 系统依赖安装完成"
echo ""

# ============================================
# 步骤3: 创建部署目录
# ============================================
echo "[3/8] 创建部署目录..."
sudo mkdir -p $BACKEND_DIR
sudo mkdir -p $FRONTEND_DIR
sudo chown -R $USER:$USER /opt/caigou

echo "✅ 部署目录创建完成"
echo ""

# ============================================
# 步骤4: 配置Backend环境
# ============================================
echo "[4/8] 配置Backend环境..."

cat > $BACKEND_DIR/.env.ubuntu << EOF
# ==========================================
# 采购系统Backend配置文件 - Ubuntu生产环境
# ==========================================

# ========== MySQL数据库配置 ==========
# 连接Windows上的MySQL数据库
DB_HOST=$WINDOWS_IP
DB_PORT=3306
DB_USER=caigou_admin
DB_PASSWORD=caigou2025!@#
DB_NAME=caigou_local

# ========== Flask应用配置 ==========
FLASK_APP=app.py
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=CHANGE-THIS-IN-PRODUCTION-$(openssl rand -hex 32)

# ========== JWT配置 ==========
JWT_SECRET_KEY=CHANGE-THIS-IN-PRODUCTION-$(openssl rand -hex 32)
JWT_ACCESS_TOKEN_EXPIRES=86400

# ========== 文件上传配置 ==========
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# ========== 企业微信配置 ==========
WEWORK_CORP_ID=ww7f7bb9e8fc040434
WEWORK_AGENT_ID=1000010
WEWORK_SECRET=g_N-OEw3TsrBYyv07exCaUzCT56dCzvjN1G8TW1_NHM

# ========== Celery配置 ==========
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ========== OCR配置 ==========
USE_BAIDU_OCR=false

# ========== 日志配置 ==========
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF

echo "✅ Backend环境配置完成"
echo "   配置文件: $BACKEND_DIR/.env.ubuntu"
echo ""

# ============================================
# 步骤5: 测试MySQL连接
# ============================================
echo "[5/8] 测试MySQL连接..."

mysql -h $WINDOWS_IP -u caigou_admin -pcaigou2025!@# caigou_local -e "SELECT 'MySQL连接成功!' AS status;" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ MySQL连接测试成功"
else
    echo "❌ MySQL连接失败"
    echo "请检查:"
    echo "  1. MySQL用户权限"
    echo "  2. 数据库是否存在"
    echo "  3. 用户名密码是否正确"
    exit 1
fi

echo ""

# ============================================
# 步骤6: 配置Nginx
# ============================================
echo "[6/8] 配置Nginx..."

sudo tee /etc/nginx/sites-available/caigou > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    # Frontend静态文件
    location / {
        root /opt/caigou/frontend/build;
        try_files $uri /index.html;

        # 缓存配置
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API代理
    location /api {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 上传文件访问
    location /uploads {
        alias /opt/caigou/backend/uploads;
        expires 30d;
        add_header Cache-Control "public";
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # 文件上传大小限制
    client_max_body_size 16M;
}
EOF

# 启用站点配置
sudo ln -sf /etc/nginx/sites-available/caigou /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试Nginx配置
sudo nginx -t

echo "✅ Nginx配置完成"
echo ""

# ============================================
# 步骤7: 配置Supervisor管理服务
# ============================================
echo "[7/8] 配置Supervisor..."

sudo tee /etc/supervisor/conf.d/caigou.conf > /dev/null << EOF
[program:caigou-backend]
command=/opt/caigou/backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:5001 app:app
directory=/opt/caigou/backend
user=$USER
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/caigou/backend.err.log
stdout_logfile=/var/log/caigou/backend.out.log
environment=PATH="/opt/caigou/backend/venv/bin"

[program:caigou-celery-worker]
command=/opt/caigou/backend/venv/bin/celery -A celery_worker.celery worker --loglevel=info
directory=/opt/caigou/backend
user=$USER
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/caigou/celery.err.log
stdout_logfile=/var/log/caigou/celery.out.log
environment=PATH="/opt/caigou/backend/venv/bin"

[program:caigou-celery-beat]
command=/opt/caigou/backend/venv/bin/celery -A celery_worker.celery beat --loglevel=info
directory=/opt/caigou/backend
user=$USER
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/caigou/celery-beat.err.log
stdout_logfile=/var/log/caigou/celery-beat.out.log
environment=PATH="/opt/caigou/backend/venv/bin"
EOF

# 创建日志目录
sudo mkdir -p /var/log/caigou
sudo chown -R $USER:$USER /var/log/caigou

echo "✅ Supervisor配置完成"
echo ""

# ============================================
# 步骤8: 显示后续步骤
# ============================================
echo "[8/8] 配置完成，后续步骤..."
echo ""
echo "===================================================="
echo "✅ Ubuntu环境配置完成！"
echo "===================================================="
echo ""
echo "📝 后续步骤:"
echo ""
echo "1. 部署Backend代码:"
echo "   cd /opt/caigou/backend"
echo "   git clone <your-repo-url> ."
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "   cp .env.ubuntu .env"
echo ""
echo "2. 部署Frontend代码:"
echo "   cd /opt/caigou/frontend"
echo "   git clone <your-repo-url> ."
echo "   npm install"
echo "   npm run build"
echo ""
echo "3. 启动服务:"
echo "   sudo systemctl restart nginx"
echo "   sudo supervisorctl reread"
echo "   sudo supervisorctl update"
echo "   sudo supervisorctl start all"
echo ""
echo "4. 查看服务状态:"
echo "   sudo supervisorctl status"
echo "   sudo systemctl status nginx"
echo ""
echo "5. 查看日志:"
echo "   tail -f /var/log/caigou/backend.out.log"
echo "   tail -f /var/log/caigou/celery.out.log"
echo ""
echo "===================================================="
echo ""
echo "🌐 访问地址:"
echo "   http://$(hostname -I | awk '{print $1}')"
echo ""
echo "📊 数据库连接:"
echo "   Windows MySQL: $WINDOWS_IP:3306"
echo "   数据库: caigou_local"
echo "   用户: caigou_admin"
echo ""
echo "===================================================="
