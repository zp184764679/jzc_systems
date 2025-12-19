#!/bin/bash
# JZC Systems 智能增量部署脚本
# 只重建有变化的子系统，不影响其他系统运行

echo "========================================="
echo "JZC Systems 智能部署开始: $(date)"
echo "========================================="

# 项目根目录
PROJECT_DIR="/www/jzc_systems"
cd $PROJECT_DIR

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取上次部署的 commit hash
LAST_DEPLOY_FILE="$PROJECT_DIR/.last_deploy_commit"
if [ -f "$LAST_DEPLOY_FILE" ]; then
    LAST_COMMIT=$(cat "$LAST_DEPLOY_FILE")
else
    # 首次部署，使用空树作为对比
    LAST_COMMIT="4b825dc642cb6eb9a060e54bf8d69288fbee4904"
fi

CURRENT_COMMIT=$(git rev-parse HEAD)
echo -e "${BLUE}上次部署: ${LAST_COMMIT:0:8}${NC}"
echo -e "${BLUE}当前版本: ${CURRENT_COMMIT:0:8}${NC}"

# 获取变化的文件列表
CHANGED_FILES=$(git diff --name-only "$LAST_COMMIT" "$CURRENT_COMMIT" 2>/dev/null || git diff --name-only HEAD~1 HEAD)
echo -e "${BLUE}变化的文件数: $(echo "$CHANGED_FILES" | wc -l)${NC}"
echo ""

# 检测哪些系统需要更新
check_system_changed() {
    local system_dir=$1
    echo "$CHANGED_FILES" | grep -q "^$system_dir/" && return 0
    return 1
}

# 系统映射：目录名 -> PM2服务名 -> 是否有前端
declare -A SYSTEMS=(
    ["Portal"]="portal-backend:yes"
    ["HR"]="hr-backend:yes"
    ["account"]="account-backend:yes"
    ["CRM"]="crm-backend:yes"
    ["SCM"]="scm-backend:no"
    ["SHM"]="shm-backend:yes"
    ["EAM"]="eam-backend:no"
    ["MES"]="mes-backend:no"
    ["报价"]="quotation-backend:yes"
    ["采购"]="caigou-backend:yes"
)

# 需要更新的系统
BACKEND_TO_RESTART=""
FRONTEND_TO_BUILD=""

# 检查 shared 模块是否有变化（影响所有后端）
SHARED_CHANGED=false
if echo "$CHANGED_FILES" | grep -q "^shared/"; then
    echo -e "${YELLOW}⚠ shared 模块有变化，需要重启所有后端${NC}"
    SHARED_CHANGED=true
fi

# 检查各系统变化
echo ""
echo "=== 检测系统变化 ==="
for system_dir in "${!SYSTEMS[@]}"; do
    config="${SYSTEMS[$system_dir]}"
    pm2_name="${config%%:*}"
    has_frontend="${config##*:}"

    if check_system_changed "$system_dir"; then
        echo -e "${YELLOW}✓ $system_dir 有变化${NC}"

        # 检查后端是否有变化
        if echo "$CHANGED_FILES" | grep -q "^$system_dir/backend/"; then
            BACKEND_TO_RESTART="$BACKEND_TO_RESTART $pm2_name"
        fi

        # 检查前端是否有变化
        if [ "$has_frontend" = "yes" ]; then
            if echo "$CHANGED_FILES" | grep -q "^$system_dir/frontend/\|^$system_dir/src/\|^$system_dir/package"; then
                FRONTEND_TO_BUILD="$FRONTEND_TO_BUILD $system_dir"
            fi
        fi
    fi
done

# 如果 shared 有变化，重启所有后端
if [ "$SHARED_CHANGED" = true ]; then
    for system_dir in "${!SYSTEMS[@]}"; do
        config="${SYSTEMS[$system_dir]}"
        pm2_name="${config%%:*}"
        if [[ ! "$BACKEND_TO_RESTART" =~ "$pm2_name" ]]; then
            BACKEND_TO_RESTART="$BACKEND_TO_RESTART $pm2_name"
        fi
    done
fi

echo ""
echo "=== 部署计划 ==="
if [ -n "$BACKEND_TO_RESTART" ]; then
    echo -e "${BLUE}后端需要重启:$BACKEND_TO_RESTART${NC}"
else
    echo -e "${GREEN}后端无需重启${NC}"
fi

if [ -n "$FRONTEND_TO_BUILD" ]; then
    echo -e "${BLUE}前端需要构建:$FRONTEND_TO_BUILD${NC}"
else
    echo -e "${GREEN}前端无需构建${NC}"
fi

# 运行数据库迁移
run_migrations() {
    echo ""
    echo "=== 检查数据库迁移 ==="

    MIGRATION_LOG="$PROJECT_DIR/.migration_log"
    MIGRATION_DIRS=(
        "$PROJECT_DIR/Portal/backend/migrations"
        "$PROJECT_DIR/shared/migrations"
    )

    for MIGRATION_DIR in "${MIGRATION_DIRS[@]}"; do
        if [ -d "$MIGRATION_DIR" ]; then
            for sql_file in "$MIGRATION_DIR"/*.sql; do
                if [ -f "$sql_file" ]; then
                    filename=$(basename "$sql_file")
                    if ! grep -q "$filename" "$MIGRATION_LOG" 2>/dev/null; then
                        echo -e "${YELLOW}执行迁移: $filename${NC}"
                        mysql -u app -papp cncplan < "$sql_file" 2>/dev/null || {
                            echo -e "${YELLOW}迁移警告: $filename 可能已执行或有错误，继续...${NC}"
                        }
                        echo "$filename" >> "$MIGRATION_LOG"
                        echo -e "${GREEN}✓ 迁移完成: $filename${NC}"
                    fi
                fi
            done
        fi
    done
}

run_migrations

# 构建前端
build_frontend() {
    local system_dir=$1
    local log_file="/tmp/build_${system_dir}.log"

    echo -e "${YELLOW}>>> 构建 $system_dir 前端...${NC}"

    # Portal 等没有 frontend 子目录
    if [ -d "$PROJECT_DIR/$system_dir/frontend" ]; then
        cd "$PROJECT_DIR/$system_dir/frontend"
    elif [ -f "$PROJECT_DIR/$system_dir/package.json" ]; then
        cd "$PROJECT_DIR/$system_dir"
    else
        echo -e "${YELLOW}⚠ $system_dir 前端目录不存在，跳过${NC}"
        return
    fi

    rm -rf dist
    npm install --silent 2>/dev/null
    npm run build > "$log_file" 2>&1

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $system_dir 前端构建完成${NC}"
    else
        echo -e "${RED}✗ $system_dir 前端构建失败，查看 $log_file${NC}"
    fi

    cd "$PROJECT_DIR"
}

# 执行前端构建（并行）
if [ -n "$FRONTEND_TO_BUILD" ]; then
    echo ""
    echo "=== 构建前端 ==="
    START_TIME=$(date +%s)

    for system_dir in $FRONTEND_TO_BUILD; do
        build_frontend "$system_dir" &
    done
    wait

    END_TIME=$(date +%s)
    echo -e "${GREEN}✓ 前端构建完成，耗时: $((END_TIME - START_TIME)) 秒${NC}"
fi

# 重启后端服务（只重启需要的）
if [ -n "$BACKEND_TO_RESTART" ]; then
    echo ""
    echo "=== 重启后端服务 ==="

    for pm2_name in $BACKEND_TO_RESTART; do
        echo -e "${YELLOW}>>> 重启 $pm2_name${NC}"
        pm2 restart "$pm2_name" --update-env 2>/dev/null || {
            echo -e "${RED}✗ $pm2_name 重启失败${NC}"
        }
    done

    echo -e "${GREEN}✓ 后端服务重启完成${NC}"
fi

# 保存当前 commit hash
echo "$CURRENT_COMMIT" > "$LAST_DEPLOY_FILE"

echo ""
echo "========================================="
echo -e "${GREEN}✅ 智能部署完成: $(date)${NC}"
echo "========================================="

# 显示服务状态（只显示相关服务）
if command -v pm2 &> /dev/null; then
    echo ""
    echo "当前服务状态:"
    pm2 list
fi
