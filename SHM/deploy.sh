#!/bin/bash
# SHM 出货管理系统部署脚本
# 使用方法: bash deploy.sh

echo "======================================"
echo "  SHM 出货管理系统部署脚本"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查Node.js
echo -e "${YELLOW}[1/7] 检查Node.js环境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到Node.js，请先安装Node.js${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js版本: $(node --version)${NC}"
echo ""

# 检查Python
echo -e "${YELLOW}[2/7] 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3，请先安装Python3${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python版本: $(python3 --version)${NC}"
echo ""

# 检查PM2
echo -e "${YELLOW}[3/7] 检查PM2...${NC}"
if ! command -v pm2 &> /dev/null; then
    echo -e "${YELLOW}未找到PM2，正在安装...${NC}"
    npm install -g pm2
fi
echo -e "${GREEN}✓ PM2已安装${NC}"
echo ""

# 安装serve (用于前端)
echo -e "${YELLOW}[4/7] 安装serve工具...${NC}"
if ! command -v serve &> /dev/null; then
    npm install -g serve
fi
echo -e "${GREEN}✓ serve已安装${NC}"
echo ""

# 设置后端Python虚拟环境
echo -e "${YELLOW}[5/7] 配置Python虚拟环境...${NC}"
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境已创建${NC}"
else
    echo -e "${GREEN}✓ 虚拟环境已存在${NC}"
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
echo -e "${YELLOW}  安装Python依赖...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Python依赖已安装${NC}"
deactivate
cd ..
echo ""

# 配置PM2服务
echo -e "${YELLOW}[6/7] 配置PM2服务...${NC}"

# 停止旧服务（如果存在）
pm2 delete shm-frontend 2>/dev/null || true
pm2 delete shm-backend 2>/dev/null || true

# 启动前端服务
echo -e "${YELLOW}  启动前端服务 (端口 7500)...${NC}"
cd frontend
pm2 start serve --name shm-frontend -- -s dist -l 7500
cd ..
echo -e "${GREEN}✓ 前端服务已启动${NC}"

# 启动后端服务
echo -e "${YELLOW}  启动后端服务 (端口 8006)...${NC}"
cd backend
pm2 start app.py --name shm-backend --interpreter $(pwd)/venv/bin/python
cd ..
echo -e "${GREEN}✓ 后端服务已启动${NC}"
echo ""

# 保存PM2配置
echo -e "${YELLOW}[7/7] 保存PM2配置...${NC}"
pm2 save
echo -e "${GREEN}✓ PM2配置已保存${NC}"
echo ""

# 显示服务状态
echo -e "${GREEN}======================================"
echo "  部署完成！"
echo "======================================${NC}"
echo ""
pm2 list

echo ""
echo -e "${GREEN}访问地址:${NC}"
echo -e "  前端: ${YELLOW}http://localhost:7500${NC}"
echo -e "  后端: ${YELLOW}http://localhost:8006${NC}"
echo ""
echo -e "${GREEN}常用命令:${NC}"
echo "  查看状态: pm2 list"
echo "  查看日志: pm2 logs shm-frontend"
echo "           pm2 logs shm-backend"
echo "  重启服务: pm2 restart shm-frontend"
echo "           pm2 restart shm-backend"
echo ""
