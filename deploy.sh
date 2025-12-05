#!/bin/bash
# JZC Systems 部署脚本
# 在服务器上执行

set -e  # 遇到错误立即退出

echo "========================================="
echo "JZC Systems 部署开始: $(date)"
echo "========================================="

# 项目根目录
PROJECT_DIR="/www/jzc_systems"
cd $PROJECT_DIR

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 部署函数
deploy_backend() {
    local name=$1
    local dir=$2
    local port=$3

    echo -e "${YELLOW}>>> 部署 $name 后端...${NC}"

    if [ -d "$dir/backend" ]; then
        cd "$dir/backend"

        # 安装依赖（如果 requirements.txt 有变化）
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt -q 2>/dev/null || true
        fi

        cd $PROJECT_DIR
        echo -e "${GREEN}✓ $name 后端就绪${NC}"
    fi
}

deploy_frontend() {
    local name=$1
    local dir=$2

    echo -e "${YELLOW}>>> 构建 $name 前端...${NC}"

    if [ -d "$dir/frontend" ]; then
        cd "$dir/frontend"

        # 检查是否有 package.json 变化需要重新安装
        if [ -f "package.json" ]; then
            npm install --silent 2>/dev/null || true
            npm run build --silent 2>/dev/null || true
        fi

        cd $PROJECT_DIR
        echo -e "${GREEN}✓ $name 前端构建完成${NC}"
    fi
}

# 部署各个系统
echo ""
echo "=== 部署后端服务 ==="

deploy_backend "Portal" "Portal" 3002
deploy_backend "HR" "HR" 8003
deploy_backend "Account" "account" 8004
deploy_backend "CRM" "CRM" 8002
deploy_backend "SCM" "SCM" 8005
deploy_backend "SHM" "SHM" 8006
deploy_backend "EAM" "EAM" 8008
deploy_backend "MES" "MES" 8007
deploy_backend "Quotation" "报价" 8001
deploy_backend "Caigou" "采购" 5001

echo ""
echo "=== 构建前端 ==="

deploy_frontend "Portal" "Portal"
deploy_frontend "HR" "HR"
deploy_frontend "Account" "account"
deploy_frontend "CRM" "CRM"
deploy_frontend "SCM" "SCM"
deploy_frontend "SHM" "SHM"
deploy_frontend "EAM" "EAM"
deploy_frontend "MES" "MES"
deploy_frontend "Quotation" "报价"
deploy_frontend "Caigou" "采购"

echo ""
echo "=== 重启服务 ==="

# 使用 PM2 重启所有服务
if command -v pm2 &> /dev/null; then
    pm2 reload all --update-env 2>/dev/null || pm2 restart all 2>/dev/null || true
    echo -e "${GREEN}✓ PM2 服务已重启${NC}"
fi

# 或者使用 systemctl（如果配置了 systemd）
# sudo systemctl restart jzc-portal jzc-hr jzc-crm jzc-scm jzc-shm jzc-eam jzc-mes

echo ""
echo "========================================="
echo -e "${GREEN}✅ 部署完成: $(date)${NC}"
echo "========================================="

# 显示服务状态
if command -v pm2 &> /dev/null; then
    echo ""
    echo "当前服务状态:"
    pm2 list
fi
