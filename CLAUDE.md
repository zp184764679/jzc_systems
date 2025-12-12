# JZC 企业管理系统 - Claude Code 项目上下文

## 项目概述

JZC 企业管理系统是一套完整的企业资源规划 (ERP) 解决方案，采用微服务架构，包含 10 个独立但互联的子系统，覆盖企业运营的各个核心环节。

### 项目目标
- 实现企业内部各业务系统的统一管理
- 提供统一的单点登录 (SSO) 认证机制
- 支持系统间数据互通与集成
- 实现自动化部署，提高运维效率

### 项目仓库
- **GitHub**: https://github.com/zp184764679/jzc_systems
- **生产环境**: https://jzchardware.cn:8888

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端框架** | React 18/19 + Vite |
| **UI 组件库** | Ant Design 5/6, Tailwind CSS (采购) |
| **状态管理** | Zustand (报价), Context API |
| **后端框架** | Flask (大多数), FastAPI (报价) |
| **ORM** | SQLAlchemy 2.0+ |
| **数据库** | MySQL 8.0 |
| **认证** | JWT (PyJWT) - 统一 SSO |
| **进程管理** | PM2 |
| **Web服务器** | Nginx |
| **CI/CD** | GitHub Actions |
| **异步任务** | Celery + Redis (报价、采购) |

---

## 生产服务器信息

- **服务器地址**: 61.145.212.28 (jzchardware.cn)
- **用户**: aaa
- **代码目录**: `/www/jzc_systems/`
- **访问地址**: `https://jzchardware.cn:8888`

---

## 子系统配置 (生产环境)

| 系统 | 目录 | 后端端口 | 前端路径 | API路径 | PM2服务名 | 数据库 | 状态 |
|------|------|----------|----------|---------|-----------|--------|------|
| Portal | Portal/ | 3002 | `/` | `/api/` | portal-backend | cncplan | 已部署 |
| HR | HR/ | 8003 | `/hr/` | `/hr/api/` | hr-backend | hr_system | 已部署 |
| Account | account/ | 8004 | `/account/` | `/account/api/` | account-backend | cncplan | 已部署 |
| Quotation | 报价/ | 8001 | `/quotation/` | `/quotation/api/` | quotation-backend | cncplan | 已部署 |
| Caigou | 采购/ | 5001 | `/caigou/` | `/caigou/api/` | caigou-backend | cncplan | 已部署 |
| SHM | SHM/ | 8006 | `/shm/` | `/shm/api/` | shm-backend | cncplan | 已部署 |
| CRM | CRM/ | 8002 | `/crm/` | `/crm/api/` | - | cncplan | 未部署 |
| SCM | SCM/ | 8005 | `/scm/` | `/scm/api/` | - | cncplan | 未部署 |
| EAM | EAM/ | 8008 | `/eam/` | `/eam/api/` | - | cncplan | 未部署 |
| MES | MES/ | 8007 | `/mes/` | `/mes/api/` | - | cncplan | 未部署 |

---

## Nginx 路由规则

每个子系统的 nginx 配置模式：
- 静态文件: `/{system}/` -> `{system}/frontend/dist/`
- API代理: `/{system}/api/` -> `http://localhost:{port}/`

**重要**: nginx 代理时会去掉 `/{system}/api/` 前缀，后端路由不需要包含 `/api`

示例：
```
浏览器请求: /account/api/hr-sync/org-options
nginx 转发: http://localhost:8004/hr-sync/org-options
后端路由:   /hr-sync/org-options
```

---

## 目录结构

```
/www/jzc_systems/
├── Portal/              # 门户系统 (SSO认证中心)
├── HR/                  # 人力资源管理
├── account/             # 账户管理
├── 报价/                # 报价管理系统
├── 采购/                # 采购管理系统
├── SHM/                 # 出货管理
├── CRM/                 # 客户关系管理 (未部署)
├── SCM/                 # 仓库管理 (未部署)
├── EAM/                 # 设备资产管理 (未部署)
├── MES/                 # 制造执行系统 (未部署)
├── shared/              # 共享认证模块
│   └── auth/
└── .github/workflows/   # GitHub Actions
```

每个子系统详细信息请查看各子系统目录下的 `CLAUDE.md` 文件。

---

## 系统集成关系

```
                    ┌─────────────┐
                    │   Portal    │
                    │  (SSO认证)  │
                    └──────┬──────┘
                           │ 用户认证
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
    ┌─────────┐      ┌─────────┐      ┌─────────┐
    │   HR    │◄────►│   CRM   │◄────►│   SCM   │
    │ 人力资源 │      │ 客户管理 │      │ 仓库管理 │
    └────┬────┘      └────┬────┘      └────┬────┘
         │                │                 │
         │    员工信息    │    客户信息     │   库存信息
         │                │                 │
         ▼                ▼                 ▼
    ┌─────────┐      ┌─────────┐      ┌─────────┐
    │ Account │      │   SHM   │      │   MES   │
    │ 账户管理 │      │ 出货管理 │      │ 生产执行 │
    └─────────┘      └─────────┘      └────┬────┘
                                           │
                          ┌────────────────┼────────────────┐
                          │                │                │
                          ▼                ▼                ▼
                    ┌─────────┐      ┌─────────┐      ┌─────────┐
                    │   EAM   │      │   报价   │      │   采购   │
                    │ 设备管理 │      │ 报价系统 │      │ 采购系统 │
                    └─────────┘      └─────────┘      └─────────┘
```

**集成说明**：

| 调用方 | 被调用方 | 集成内容 |
|--------|----------|----------|
| 各子系统 | HR | 获取员工信息、部门信息 |
| SHM | CRM | 获取客户信息 |
| SHM | SCM | 扣减库存 |
| MES | SCM | 物料领用 |
| MES | EAM | 设备状态查询 |
| 采购 | CRM | 供应商信息同步 |
| 报价 | HR | 获取业务员信息 |

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

### 数据库备份
```bash
mysqldump -u root -p cncplan > backup.sql
mysqldump -u root -p hr_system > hr_backup.sql
```

### GitHub CLI
```bash
# 手动触发部署
gh workflow run deploy.yml --repo zp184764679/jzc_systems

# 查看 Actions 运行状态
gh run list --repo zp184764679/jzc_systems
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

## 环境变量配置

### 后端 .env.production
```bash
# 数据库
DB_HOST=localhost
MYSQL_USER=app
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=cncplan

# JWT
SECRET_KEY=your_super_secret_key

# Flask
FLASK_ENV=production

# CORS
CORS_ORIGINS=https://jzchardware.cn,https://jzchardware.cn:8888
```

### 前端 .env
```bash
VITE_API_BASE_URL=/api
VITE_PORTAL_URL=/
```

---

## 注意事项

1. **API路径**: nginx 会去掉 `/{system}/api/` 前缀，后端路由不要包含 `/api`
2. **共享模块**: 各后端通过 symlink 引用 `shared/`，修改会影响所有系统
3. **环境变量**: `.env` 不在 Git 中，需手动维护
4. **中文目录**: `报价/` 和 `采购/` 命令行操作时注意引号
5. **端口冲突**: Account 用 8004，不是 8001 (8001 是报价系统)
6. **SSO 认证**: 所有子系统使用统一的 JWT Token，由 Portal 签发

---

## 项目进展

### 已完成
- 统一的 SSO 单点登录系统
- JWT Token 认证机制
- 跨系统用户身份验证
- GitHub Actions 自动部署
- 6 个子系统已部署上线

### 待完成
- 完善各系统权限控制
- 添加操作日志审计
- 数据库索引优化
- API 请求限流
- 移动端适配
