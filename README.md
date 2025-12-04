# JZC Systems - 企业管理系统

## 系统组成

| 系统 | 说明 | 后端端口 | 前端路径 |
|------|------|---------|---------|
| Portal | 门户/SSO认证 | 3002 | / |
| HR | 人力资源管理 | 8003 | /hr |
| CRM | 客户关系管理 | 8002 | /crm |
| SCM | 仓库管理 | 8005 | /scm |
| SHM | 出货管理 | 8006 | /shm |
| EAM | 设备资产管理 | 8008 | /eam |
| MES | 制造执行系统 | 8007 | /mes |
| account | 账户管理 | 8001 | /account |
| 报价 | 报价管理系统 | 8009 | /quote |
| 采购 | 采购管理系统 | 8010 | /purchase |

## 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/zp184764679/jzc_systems.git
cd jzc_systems
```

### 2. 配置环境变量
```bash
cp .env.production.example .env.production
# 编辑 .env.production 填写实际配置
```

### 3. 部署
```bash
chmod +x deploy.sh
./deploy.sh
```

## 自动部署 (GitHub Actions)

Push 到 `main` 分支会自动触发部署。

需要在 GitHub 仓库设置以下 Secrets:
- `SERVER_HOST` - 服务器IP/域名
- `SERVER_USER` - SSH用户名
- `SSH_PRIVATE_KEY` - SSH私钥
- `SERVER_PORT` - SSH端口 (默认22)

## 技术栈

- **前端**: React + Vite + Ant Design
- **后端**: Python Flask
- **数据库**: MySQL
- **进程管理**: PM2
