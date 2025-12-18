#!/bin/bash
# JZC Systems 部署脚本
# 在服务器上执行

# set -e  # 不要遇到错误就退出，让所有系统都尝试构建

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

        if [ -f "package.json" ]; then
            # 强制重新构建：删除旧的构建产物
            rm -rf dist
            echo "Installing dependencies for $name..."
            npm install || { echo "npm install failed for $name"; cd $PROJECT_DIR; return 1; }
            echo "Building $name..."
            npm run build || { echo "npm run build failed for $name"; cd $PROJECT_DIR; return 1; }
        fi

        cd $PROJECT_DIR
        echo -e "${GREEN}✓ $name 前端构建完成${NC}"
    else
        echo -e "${YELLOW}⚠ $dir/frontend 目录不存在，跳过${NC}"
    fi
}

# 部署各个系统
echo ""
echo "=== 部署后端服务 ==="

# 运行数据库迁移（如果有新的迁移文件）
run_migrations() {
    echo -e "${YELLOW}>>> 检查数据库迁移...${NC}"

    MIGRATION_DIR="$PROJECT_DIR/Portal/backend/migrations"
    MIGRATION_LOG="$PROJECT_DIR/.migration_log"

    if [ -d "$MIGRATION_DIR" ]; then
        for sql_file in "$MIGRATION_DIR"/*.sql; do
            if [ -f "$sql_file" ]; then
                filename=$(basename "$sql_file")

                # 检查是否已执行过
                if ! grep -q "$filename" "$MIGRATION_LOG" 2>/dev/null; then
                    echo "执行迁移: $filename"
                    mysql -u app -papp cncplan < "$sql_file" 2>/dev/null || {
                        echo "迁移警告: $filename 可能已执行或有错误，继续..."
                    }
                    echo "$filename" >> "$MIGRATION_LOG"
                    echo -e "${GREEN}✓ 迁移完成: $filename${NC}"
                else
                    echo "跳过已执行的迁移: $filename"
                fi
            fi
        done
    fi
}

run_migrations

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
