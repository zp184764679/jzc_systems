# JZC 企业管理系统 - Claude Code 项目上下文

## 项目概述
这是一个包含多个子系统的企业 ERP 系统，采用微服务架构。

## 技术栈
- **前端**: React 18 + Vite + Ant Design
- **后端**: Python Flask / FastAPI + SQLAlchemy
- **数据库**: MySQL 8.0
- **认证**: JWT (统一 SSO)
- **部署**: PM2 + Nginx + GitHub Actions

---

## 生产服务器信息

- **服务器地址**: 61.145.212.28 (jzchardware.cn)
- **用户**: aaa
- **代码目录**: `/www/jzc_systems/`
- **访问地址**: `https://jzchardware.cn:8888`
- **GitHub**: https://github.com/zp184764679/jzc_systems

---

## 子系统配置 (生产环境)

| 系统 | 目录 | 后端端口 | 前端路径 | API路径 | PM2服务名 |
|------|------|----------|----------|---------|-----------|
| Portal | Portal/ | 3002 | `/` | `/api/` | portal-backend |
| HR | HR/ | 8003 | `/hr/` | `/hr/api/` | hr-backend |
| Account | account/ | 8004 | `/account/` | `/account/api/` | account-backend |
| Quotation | 报价/ | 8001 | `/quotation/` | `/quotation/api/` | quotation-backend |
| Caigou | 采购/ | 5001 | `/caigou/` | `/caigou/api/` | caigou-backend |
| SHM | SHM/ | 8006 | `/shm/` | `/shm/api/` | shm-backend |

**未部署系统**: CRM, SCM, EAM, MES

---

## Nginx 路由规则

每个子系统的 nginx 配置模式：
- 静态文件: `/{system}/` -> `{system}/frontend/dist/`
- API代理: `/{system}/api/` -> `http://localhost:{port}/`

**重要**: nginx 代理时会去掉 `/{system}/api/` 前缀，后端路由不需要包含 `/api`

示例：
- 浏览器请求: `/account/api/hr-sync/org-options`
- nginx 转发到: `http://localhost:8004/hr-sync/org-options`
- 后端路由应为: `/hr-sync/org-options`

---

## 目录结构

```
/www/jzc_systems/
├── Portal/              # 门户系统
│   ├── backend/
│   └── dist/
├── HR/
│   ├── backend/
│   └── frontend/dist/
├── account/
│   ├── backend/
│   └── frontend/dist/
├── 报价/
│   ├── backend/
│   └── frontend/dist/
├── 采购/
│   ├── backend/
│   └── frontend/dist/
├── SHM/
│   ├── backend/
│   └── frontend/dist/
├── shared/              # 共享认证模块
│   └── auth/
└── .github/workflows/   # GitHub Actions
```

---

## 常用命令

### 开发
```bash
# 启动后端
cd {系统}/backend && python main.py

# 启动前端
cd {系统}/frontend && npm run dev

# 构建前端
npm run build
```

### PM2 管理
```bash
pm2 list                    # 查看所有服务
pm2 restart all             # 重启所有
pm2 restart account-backend # 重启单个
pm2 logs account-backend    # 查看日志
pm2 save                    # 保存配置
```

### Git 部署
```bash
git add . && git commit -m "更新说明" && git push origin main
# GitHub Actions 自动部署
```

### 服务器手动部署
```bash
cd /www/jzc_systems
git pull origin main
cd account/frontend && npm install && npm run build
pm2 restart account-backend
```

### 健康检查
```bash
curl http://127.0.0.1:3002/health   # Portal
curl http://127.0.0.1:8003/health   # HR
curl http://127.0.0.1:8004/health   # Account
curl http://127.0.0.1:8001/health   # Quotation
curl http://127.0.0.1:5001/api/health  # Caigou
curl http://127.0.0.1:8006/api/health  # SHM
```

---

## 配置文件位置

| 配置 | 路径 |
|------|------|
| Nginx配置 | `/etc/nginx/nginx.conf` |
| SSL证书 | `/etc/letsencrypt/live/jzchardware.cn/` |
| PM2配置 | `~/.pm2/dump.pm2` |
| 环境变量 | 各后端 `.env` 文件 |
| 共享认证 | `/www/jzc_systems/shared/` |

---

## 注意事项

1. **API路径**: nginx 会去掉 `/{system}/api/` 前缀，后端路由不要包含 `/api`
2. **共享模块**: 各后端通过symlink引用 `shared/`，修改会影响所有系统
3. **环境变量**: `.env` 不在Git中，需手动维护
4. **中文目录**: `报价/` 和 `采购/` 命令行操作时注意引号
5. **端口**: Account用8004，不是8001(8001是报价系统)
