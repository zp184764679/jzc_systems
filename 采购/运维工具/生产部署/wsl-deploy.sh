#!/bin/bash
# ============================================================
# WSL 生产环境一键部署脚本
# ============================================================

set -e  # 遇到错误立即退出

echo "============================================================"
echo "🚀 采购系统 - WSL 生产环境部署"
echo "============================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="caigou-system"
PROJECT_ROOT="$HOME/$PROJECT_NAME"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOG_DIR="$PROJECT_ROOT/logs"

# 用户名（根据实际情况修改）
DEPLOY_USER=$(whoami)

echo -e "${BLUE}📝 配置信息:${NC}"
echo "  项目目录: $PROJECT_ROOT"
echo "  部署用户: $DEPLOY_USER"
echo ""

# 检查是否在WSL中运行
if ! grep -qi microsoft /proc/version; then
    echo -e "${RED}❌ 错误：此脚本必须在WSL中运行${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 运行环境：WSL${NC}"
echo ""

# ============================================================
# 步骤1：检查依赖
# ============================================================
echo -e "${BLUE}[1/10] 检查系统依赖...${NC}"

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $1"
    else
        echo -e "  ${RED}✗${NC} $1 未安装"
        return 1
    fi
}

DEPS_OK=true
check_command python3 || DEPS_OK=false
check_command node || DEPS_OK=false
check_command npm || DEPS_OK=false
check_command nginx || DEPS_OK=false
check_command redis-cli || DEPS_OK=false
check_command mysql || DEPS_OK=false
check_command supervisor || DEPS_OK=false

if [ "$DEPS_OK" = false ]; then
    echo ""
    echo -e "${RED}❌ 缺少必要依赖，请先安装${NC}"
    echo "运行以下命令安装："
    echo "  sudo apt update"
    echo "  sudo apt install python3 python3-venv python3-pip nodejs npm nginx redis-server mysql-client supervisor -y"
    exit 1
fi

echo -e "${GREEN}✅ 所有依赖已安装${NC}"
echo ""

# ============================================================
# 步骤2：复制项目文件
# ============================================================
echo -e "${BLUE}[2/10] 复制项目文件...${NC}"

# 从Windows复制到WSL
WINDOWS_PROJECT="/mnt/c/Users/Admin/Desktop/采购"

if [ -d "$WINDOWS_PROJECT" ]; then
    echo "  从 Windows 复制项目..."
    mkdir -p $PROJECT_ROOT
    cp -r "$WINDOWS_PROJECT"/* $PROJECT_ROOT/
    echo -e "  ${GREEN}✓${NC} 项目文件已复制"
else
    echo -e "  ${YELLOW}⚠️  找不到 Windows 项目目录${NC}"
    echo "  请手动复制项目到: $PROJECT_ROOT"
    exit 1
fi

echo ""

# ============================================================
# 步骤3：配置生产环境
# ============================================================
echo -e "${BLUE}[3/10] 配置生产环境...${NC}"

cd $BACKEND_DIR

if [ ! -f ".env.production" ]; then
    echo -e "  ${RED}✗${NC} 找不到 .env.production"
    exit 1
fi

# 备份现有.env
if [ -f ".env" ]; then
    cp .env .env.backup
    echo "  ✓ 已备份 .env"
fi

# 应用生产配置
cp .env.production .env
echo "  ✓ 已应用生产环境配置"

# 获取Windows主机IP
WINDOWS_IP=$(ip route show | grep -i default | awk '{ print $3}')
echo "  Windows 主机 IP: $WINDOWS_IP"

# 更新数据库配置
sed -i "s/DB_HOST=localhost/DB_HOST=$WINDOWS_IP/" .env
echo "  ✓ 已更新数据库连接地址"

echo ""

# ============================================================
# 步骤4：安装后端依赖
# ============================================================
echo -e "${BLUE}[4/10] 安装后端依赖...${NC}"

cd $BACKEND_DIR

# 创建虚拟环境
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  ✓ 创建虚拟环境"
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn gevent

echo -e "  ${GREEN}✓${NC} 后端依赖安装完成"
echo ""

# ============================================================
# 步骤5：测试数据库连接
# ============================================================
echo -e "${BLUE}[5/10] 测试数据库连接...${NC}"

if mysql -h $WINDOWS_IP -u root -pexak472008 -e "SELECT 1" &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} 数据库连接成功"
else
    echo -e "  ${RED}✗${NC} 数据库连接失败"
    echo ""
    echo "  请确保："
    echo "  1. Windows上的MySQL正在运行"
    echo "  2. MySQL允许从 $WINDOWS_IP 连接"
    echo "  3. 运行以下SQL授权："
    echo "     GRANT ALL PRIVILEGES ON caigou.* TO 'root'@'172.24.%' IDENTIFIED BY 'exak472008';"
    echo "     FLUSH PRIVILEGES;"
    exit 1
fi

echo ""

# ============================================================
# 步骤6：构建前端
# ============================================================
echo -e "${BLUE}[6/10] 构建前端...${NC}"

cd $FRONTEND_DIR

# 安装依赖
npm install

# 构建
npm run build

if [ -d "dist" ]; then
    echo -e "  ${GREEN}✓${NC} 前端构建完成"
else
    echo -e "  ${RED}✗${NC} 前端构建失败"
    exit 1
fi

echo ""

# ============================================================
# 步骤7：创建日志目录
# ============================================================
echo -e "${BLUE}[7/10] 创建日志目录...${NC}"

mkdir -p $LOG_DIR
echo -e "  ${GREEN}✓${NC} 日志目录: $LOG_DIR"
echo ""

# ============================================================
# 步骤8：配置Gunicorn
# ============================================================
echo -e "${BLUE}[8/10] 配置 Gunicorn...${NC}"

cat > $BACKEND_DIR/gunicorn_config.py << EOF
# Gunicorn配置文件
import multiprocessing

bind = "127.0.0.1:5001"
workers = 4
threads = 2
worker_class = "gevent"
timeout = 120
max_requests = 1000
max_requests_jitter = 50
accesslog = "$LOG_DIR/gunicorn-access.log"
errorlog = "$LOG_DIR/gunicorn-error.log"
loglevel = "info"
graceful_timeout = 30
daemon = False
proc_name = "caigou-backend"
EOF

echo -e "  ${GREEN}✓${NC} Gunicorn配置完成"
echo ""

# ============================================================
# 步骤9：配置Nginx
# ============================================================
echo -e "${BLUE}[9/10] 配置 Nginx...${NC}"

sudo tee /etc/nginx/sites-available/caigou > /dev/null << EOF
# 采购系统 Nginx 配置

upstream backend {
    server 127.0.0.1:5001;
    keepalive 64;
}

server {
    listen 3000;
    server_name _;

    root $FRONTEND_DIR/dist;
    index index.html;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

server {
    listen 5001;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# 启用配置
sudo ln -sf /etc/nginx/sites-available/caigou /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置
if sudo nginx -t &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Nginx配置成功"
    sudo systemctl restart nginx
else
    echo -e "  ${RED}✗${NC} Nginx配置错误"
    sudo nginx -t
    exit 1
fi

echo ""

# ============================================================
# 步骤10：配置Supervisor
# ============================================================
echo -e "${BLUE}[10/10] 配置 Supervisor...${NC}"

# Backend配置
sudo tee /etc/supervisor/conf.d/caigou-backend.conf > /dev/null << EOF
[program:caigou-backend]
directory=$BACKEND_DIR
command=$BACKEND_DIR/venv/bin/gunicorn -c gunicorn_config.py app:app
user=$DEPLOY_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$LOG_DIR/supervisor-backend.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=10
environment=PATH="$BACKEND_DIR/venv/bin"
EOF

# Celery配置
sudo tee /etc/supervisor/conf.d/caigou-celery.conf > /dev/null << EOF
[program:caigou-celery]
directory=$BACKEND_DIR
command=$BACKEND_DIR/venv/bin/celery -A celery_app.celery worker --loglevel=info --concurrency=4
user=$DEPLOY_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$LOG_DIR/supervisor-celery.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=10
environment=PATH="$BACKEND_DIR/venv/bin"
EOF

# 重新加载Supervisor
sudo supervisorctl reread
sudo supervisorctl update

echo -e "  ${GREEN}✓${NC} Supervisor配置完成"
echo ""

# ============================================================
# 启动服务
# ============================================================
echo -e "${BLUE}启动所有服务...${NC}"

# 启动Redis
sudo systemctl start redis
echo "  ✓ Redis"

# 启动Backend
sudo supervisorctl start caigou-backend
echo "  ✓ Backend"

# 启动Celery
sudo supervisorctl start caigou-celery
echo "  ✓ Celery"

# Nginx已在配置时重启
echo "  ✓ Nginx"

echo ""

# ============================================================
# 验证部署
# ============================================================
echo -e "${BLUE}验证部署...${NC}"

sleep 3

# 检查Backend
if curl -s http://localhost:5001/api/health &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Backend运行正常"
else
    echo -e "  ${YELLOW}⚠️${NC}  Backend可能未完全启动，请稍后检查"
fi

# 检查Frontend
if curl -s http://localhost:3000 &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Frontend运行正常"
else
    echo -e "  ${YELLOW}⚠️${NC}  Frontend可能未完全启动，请稍后检查"
fi

# 显示服务状态
echo ""
echo -e "${BLUE}服务状态:${NC}"
sudo supervisorctl status

echo ""
echo "============================================================"
echo -e "${GREEN}✅ 部署完成！${NC}"
echo "============================================================"
echo ""
echo "📱 访问地址："
echo "  前端: http://61.145.212.28:3000"
echo "  后端: http://61.145.212.28:5001"
echo ""
echo "👤 测试账号："
echo "  管理员: 周鹏 / exak472008"
echo "  测试用户: exzzz / exak472008"
echo ""
echo "🔧 常用命令："
echo "  查看服务状态: sudo supervisorctl status"
echo "  重启Backend: sudo supervisorctl restart caigou-backend"
echo "  重启Celery: sudo supervisorctl restart caigou-celery"
echo "  查看日志: tail -f $LOG_DIR/supervisor-backend.log"
echo ""
echo "📖 详细文档："
echo "  WSL部署指南: 运维工具/生产部署/WSL部署指南.md"
echo ""
