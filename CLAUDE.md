# JZC 企业管理系统 - Claude Code 项目上下文

## 项目概述

JZC 企业管理系统是一套完整的企业资源规划 (ERP) 解决方案，采用微服务架构，包含 13 个独立但互联的子系统，覆盖企业运营的各个核心环节。

### 项目目标
- 实现企业内部各业务系统的统一管理
- 提供统一的单点登录 (SSO) 认证机制
- 支持系统间数据互通与集成
- 实现自动化部署，提高运维效率

### 项目仓库
- **GitHub**: https://github.com/zp184764679/jzc_systems
- **生产环境**: https://jzchardware.cn

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端框架** | React 18/19 + Vite |
| **UI 组件库** | Ant Design 5/6, Tailwind CSS (采购) |
| **状态管理** | Zustand (报价), Context API |
| **后端框架** | Flask (大多数), FastAPI (报价), Strapi (DocPublisher) |
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
- **访问地址**: `https://jzchardware.cn`

### SSH 连接方式

> ⚠️ **安全提示**: SSH 私钥不应存储在代码仓库中。请向管理员获取访问凭据。

```bash
# 连接服务器 (需要配置私钥)
ssh -i ~/.ssh/jzc_server aaa@61.145.212.28

# 常用命令
ssh -i ~/.ssh/jzc_server aaa@61.145.212.28 "pm2 list"
ssh -i ~/.ssh/jzc_server aaa@61.145.212.28 "pm2 logs portal-backend --lines 50"
```

---

## 子系统配置 (生产环境)

| 系统 | 目录 | 后端端口 | 前端dev端口 | 前端路径 | API路径 | PM2服务名 | 数据库 | 状态 |
|------|------|----------|-------------|----------|---------|-----------|--------|------|
| Portal | Portal/ | 3002 | 3001 | `/` | `/api/` | portal-backend | cncplan | 已部署 |
| HR | HR/ | 8003 | 6002 | `/hr/` | `/hr/api/` | hr-backend | hr_system | 已部署 |
| Account | account/ | 8004 | 6003 | `/account/` | `/account/api/` | account-backend | account | 已部署 |
| Quotation | 报价/ | 8001 | 6001 | `/quotation/` | `/quotation/api/` | quotation-backend | cncplan | 已部署 |
| Caigou | 采购/ | 5001 | 5000 | `/caigou/` | `/caigou/api/` | caigou-backend | caigou | 已部署 |
| SHM | SHM/ | 8006 | 7500 | `/shm/` | `/shm/api/` | shm-backend | cncplan | 已部署 |
| CRM | CRM/ | 8002 | 6004 | `/crm/` | `/crm/api/` | crm-backend | crm | 已部署 |
| SCM | SCM/ | 8005 | 7000 | `/scm/` | `/scm/api/` | scm-backend | cncplan | 未部署 |
| EAM | EAM/ | 8008 | 7200 | `/eam/` | `/eam/api/` | eam-backend | cncplan | 未部署 |
| MES | MES/ | 8007 | 7800 | `/mes/` | `/mes/api/` | mes-backend | cncplan | 未部署 |
| Dashboard | Dashboard/ | 8100 | 6100 | `/dashboard/` | `/dashboard/api/` | dashboard-backend | cncplan | 未部署 |
| DocPublisher | DocPublisher/ | 1337 | 6200 | `/docs/` | `/strapi-api/` | docs-strapi | SQLite/MySQL | 开发中 |
| TDM | TDM/ | 8009 | 7600 | `/tdm/` | `/tdm/api/` | tdm-backend | cncplan | 开发中 |

---

## Nginx 路由规则

每个子系统的 nginx 配置模式：
- 静态文件: `/{system}/` -> `{system}/frontend/dist/`
- API代理: `/{system}/api/` -> `http://localhost:{port}/api/`

### 后端路由前缀规则（重要）

不同系统的后端路由前缀设计不同，nginx 配置必须匹配：

| 系统 | 后端 url_prefix | nginx rewrite | 示例请求 |
|------|-----------------|---------------|----------|
| Portal | `/api/xxx` | 不 rewrite | `/api/auth/me` → `/api/auth/me` |
| HR | `/api` | `/api/$1` | `/hr/api/employees` → `/api/employees` |
| Account | 无前缀 | `/$1` | `/account/api/users` → `/users` |
| SHM | `/api/xxx` | `/api/$1` | `/shm/api/base/warehouses` → `/api/base/warehouses` |
| CRM | `/api/xxx` | `/api/$1` | `/crm/api/customers` → `/api/customers` |
| 报价 | `/api/xxx` | `/api/$1` | `/quotation/api/quotes` → `/api/quotes` |
| 采购 | `/api/v1/xxx` | `/api/$1` | `/caigou/api/v1/pr` → `/api/v1/pr` |
| TDM | `/api/xxx` | `/api/$1` | `/tdm/api/products` → `/api/products` |

**nginx rewrite 规则示例**：
```nginx
# HR/SHM/CRM/报价/采购 - 保留 /api 前缀
location /hr/api/ {
    rewrite ^/hr/api/(.*)$ /api/$1 break;
    proxy_pass http://hr-backend;
}

# Account - 去掉 /api 前缀
location /account/api/ {
    rewrite ^/account/api/(.*)$ /$1 break;
    proxy_pass http://account-backend;
}
```

**SSO Token 验证路由**：
5 个子系统 (HR, Account, SHM, 报价, 采购) 使用 `/portal-api/auth/verify` 进行 SSO Token 验证：
```nginx
location /portal-api/ {
    rewrite ^/portal-api/(.*)$ /api/$1 break;
    proxy_pass http://portal-backend;
}
```

**DocPublisher 特殊路由**:
- 静态文件: `/docs/` -> `DocPublisher/frontend/dist/`
- Strapi API: `/strapi-api/` -> `http://localhost:1337/api/`
- Strapi Admin: `/strapi-admin/` -> `http://localhost:1337/admin/`

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
├── Dashboard/           # 可视化追踪系统 (未部署)
├── DocPublisher/        # 文档发布系统 (开发中)
├── TDM/                 # 产品技术标准管理 (开发中)
├── shared/              # 共享认证模块
│   ├── auth/            # JWT认证、用户模型、权限
│   └── frontend/        # 前端共享工具
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
curl http://127.0.0.1:8001/health   # Quotation (报价)
curl http://127.0.0.1:5001/health   # Caigou (采购)
curl http://127.0.0.1:8006/health   # SHM
curl http://127.0.0.1:8002/health   # CRM
curl http://127.0.0.1:8005/health   # SCM
curl http://127.0.0.1:8008/health   # EAM
curl http://127.0.0.1:8007/health   # MES
curl http://127.0.0.1:8100/health   # Dashboard
curl http://127.0.0.1:1337/_health  # DocPublisher (Strapi)
curl http://127.0.0.1:8009/health   # TDM
```

**规范**: 所有系统健康检查统一使用 `/health` 路径（不带 `/api` 前缀），DocPublisher (Strapi) 使用 `/_health`

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

### 端口管理（重要）

**问题**: `netstat` 在 Windows 上有时无法正确显示被占用的端口，导致端口冲突难以排查。

**正确的端口检查方式** (使用 PowerShell):
```powershell
# 检查特定端口占用情况
Get-NetTCPConnection -LocalPort 3001,3002,3003 -ErrorAction SilentlyContinue | Select-Object LocalPort,OwningProcess,State

# 查看进程详情
Get-Process -Id <PID> | Select-Object Id,ProcessName,Path
```

**清理端口**:
```powershell
# 强制杀掉占用端口的进程
Stop-Process -Id <PID> -Force

# 或者批量清理
Stop-Process -Id 12345,12346,12347 -Force
```

**本地开发端口规范**:

| 系统 | 后端端口 | 前端dev端口 | 入口文件 |
|------|----------|-------------|----------|
| Portal | 3002 | 3001 | main.py |
| HR | 8003 | 6002 | main.py |
| Account | 8004 | 6003 | main.py |
| 报价 (Quotation) | 8001 | 6001 | main.py |
| 采购 (Caigou) | 5001 | 5000 | main.py |
| SHM | 8006 | 7500 | main.py |
| CRM | 8002 | 6004 | main.py |
| SCM | 8005 | 7000 | main.py |
| EAM | 8008 | 7200 | main.py |
| MES | 8007 | 7800 | main.py |
| Dashboard | 8100 | 6100 | main.py |
| DocPublisher | 1337 | 6200 | Strapi |
| TDM | 8009 | 7600 | main.py |

**最佳实践**:
1. 后端服务使用 PM2 管理，避免僵尸进程: `pm2 start main.py --name xxx-backend --interpreter python`
2. 启动前端前先检查端口是否被占用
3. 不要同时启动多个前端 dev server
4. 定期运行 `pm2 list` 检查服务状态
5. 后端入口文件统一使用 `main.py`（规范化）

---

## 配置文件位置

| 配置 | 路径 |
|------|------|
| Nginx配置模板 | `nginx.conf.example` (项目根目录) |
| Nginx配置(服务器) | `/etc/nginx/conf.d/jzc.conf` |
| SSL证书 | `/etc/letsencrypt/live/jzchardware.cn/` |
| PM2配置 | `ecosystem.config.js` (项目根目录) |
| PM2状态 | `~/.pm2/dump.pm2` |
| 部署脚本 | `deploy.sh` (项目根目录) |
| 环境变量 | 各后端 `.env` 文件 |
| 共享认证 | `/www/jzc_systems/shared/` |

---

## Chrome 浏览器集成 (调试辅助)

**Claude Code 可以通过 Claude for Chrome 插件直接读取浏览器信息，用于前端调试。**

### 启用方式

```bash
# 方式1: 启动时带 --chrome 参数
claude --chrome

# 方式2: 在会话中使用 /chrome 命令
/chrome
```

### 可用功能

| 功能 | 说明 | 使用场景 |
|------|------|----------|
| **读取 Console** | 获取浏览器控制台日志/错误 | 调试前端 JS 错误 |
| **查看 Network** | 读取网络请求和响应 | 排查 API 调用问题 |
| **DOM 检查** | 读取页面元素状态 | 验证 UI 渲染 |
| **表单填充** | 自动填充表单测试 | E2E 测试 |
| **页面导航** | 访问指定 URL | 自动化测试流程 |
| **录制 GIF** | 记录操作过程 | Bug 复现文档 |

### 调试工作流示例

```text
# 让 Claude 帮你调试前端问题:
1. 用户: "打开 https://jzchardware.cn/account/register 检查有没有控制台错误"
2. Claude 会自动:
   - 导航到页面
   - 读取 Console 日志
   - 报告发现的错误
   - 建议修复方案

# 让 Claude 测试 API 调用:
1. 用户: "点击登录按钮，检查网络请求是否正确"
2. Claude 会:
   - 执行点击操作
   - 捕获 Network 请求
   - 分析响应状态和数据
```

### 权限管理

- 站点权限由 Chrome 插件设置控制
- 使用 `/chrome` 命令查看当前权限状态
- 可在插件设置中启用/禁用特定站点

### 注意事项

1. **需要可见窗口**: 不支持 headless 模式
2. **使用现有登录状态**: 会复用浏览器的 Cookie/Session
3. **增加上下文消耗**: 启用 Chrome 工具会增加 token 使用量
4. **仅支持 Chrome**: Arc、Dia 等浏览器暂不支持
5. **WSL 不支持**: Windows 上请直接运行 Claude Code，不要在 WSL 中

---

## PM2 WSL 服务

以下服务运行在 WSL Ubuntu-22.04 环境中，由 PM2 管理：

| 服务 | 说明 |
|------|------|
| ollama | AI 模型服务 (本地 LLM) |
| celery-worker | 采购系统异步任务队列 |

启动 WSL 服务：
```bash
pm2 start ollama
pm2 start celery-worker
```

---

## 环境变量配置

### SSO 认证配置（重要）

**所有 12 个子系统必须使用统一的 JWT 密钥和认证数据库配置：**

```bash
# 认证数据库 - 所有子系统统一使用 cncplan
AUTH_DB_USER=<db_user>
AUTH_DB_PASSWORD=<db_password>
AUTH_DB_HOST=localhost
AUTH_DB_NAME=cncplan        # 重要：必须是 cncplan，不是 account

# JWT配置 - 所有子系统必须相同
SECRET_KEY=<your_secret_key>
JWT_SECRET_KEY=<your_jwt_secret_key>
ALGORITHM=HS256
```

> ⚠️ **安全提示**: 实际密钥请从 `.env` 文件获取，不要在文档中存储真实密钥。

⚠️ **警告**：如果 JWT_SECRET_KEY 或 AUTH_DB_NAME 配置不一致，会导致：
- Token 验证失败（用户从 Portal 登录后无法访问子系统）
- 用户数据不一致（不同系统读取不同数据库的用户信息）

### 后端 .env.production
```bash
# 数据库
DB_HOST=localhost
MYSQL_USER=<db_user>
MYSQL_PASSWORD=<db_password>
MYSQL_DATABASE=cncplan

# 认证数据库 (shared/auth)
AUTH_DB_USER=<db_user>
AUTH_DB_PASSWORD=<db_password>
AUTH_DB_HOST=localhost
AUTH_DB_NAME=cncplan

# JWT - 统一密钥
SECRET_KEY=<your_secret_key>
JWT_SECRET_KEY=<your_jwt_secret_key>

# Flask
FLASK_ENV=production

# CORS
CORS_ORIGINS=https://jzchardware.cn
```

### 前端 .env
```bash
VITE_API_BASE_URL=/api
VITE_PORTAL_URL=/
```

---

## 注意事项

1. **API路径**: 不同系统的后端路由前缀不同，详见上方「Nginx 路由规则」章节。大多数系统需要保留 `/api` 前缀，仅 Account 系统例外
2. **共享模块**: 各后端通过 symlink 引用 `shared/`，修改会影响所有系统
3. **环境变量**: `.env` 不在 Git 中，需手动维护
4. **中文目录**: `报价/` 和 `采购/` 命令行操作时注意引号
5. **端口冲突**: Account 用 8004，不是 8001 (8001 是报价系统)
6. **SSO 认证**: 所有子系统使用统一的 JWT Token，由 Portal 签发
7. **端口检查**: Windows 下 `netstat` 不可靠，必须用 PowerShell `Get-NetTCPConnection` 检查端口
8. **进程管理**: 后端必须用 PM2 管理，避免僵尸进程；前端 dev server 同时只运行一个
9. **配置统一**: 所有 12 个子系统的 `JWT_SECRET_KEY` 和 `AUTH_DB_NAME` 必须相同（见上方 SSO 认证配置）
10. **数据库迁移**: CRM 系统新增字段时需同步更新数据库表结构（如 `grade`、`is_key_account` 等客户分级字段）

---

## 前端 UI/UX 设计规范（重要）

**开发新功能或新子系统时，必须遵循以下设计规范，确保系统一致性。**

### 子系统布局标准

所有子系统（包括 Portal 内的功能模块）必须使用统一的 **Header + Sider + Content** 布局：

```
┌─────────────────────────────────────────────────────────────────┐
│ Header                                                          │
│ [系统标题] | 用户信息 | [回到门户] [退出登录]                    │
├───────────┬─────────────────────────────────────────────────────┤
│ Sider     │                                                     │
│ 侧边菜单   │              Content (内容区域)                     │
│ - 菜单项1  │                                                     │
│ - 菜单项2  │                                                     │
│ - 菜单项3  │                                                     │
└───────────┴─────────────────────────────────────────────────────┘
```

### 必需的导航元素

| 元素 | 位置 | 功能 | 必需 |
|------|------|------|------|
| 系统标题 | Header 左侧 | 显示当前系统名称 | ✅ |
| 用户信息 | Header 右侧 | 显示当前登录用户名、角色 | ✅ |
| 回到门户 | Header 右侧按钮 | 跳转到 Portal 主页 (`/`) | ✅ |
| 退出登录 | Header 右侧按钮 | 清除 Token 并跳转登录页 | ✅ |
| 侧边菜单 | Sider | 系统内功能导航 | ✅ |
| 移动端抽屉 | Drawer | 响应式菜单（< 768px） | ✅ |

### 参考实现

开发新功能时，**必须参考以下文件**：

| 参考文件 | 说明 |
|----------|------|
| `HR/frontend/src/App.jsx` | 标准子系统布局模板 |
| `account/frontend/src/App.jsx` | 标准子系统布局模板 |
| `SHM/frontend/src/App.jsx` | 标准子系统布局模板 |

### 代码复用

1. **SSO 认证**: 使用 `shared/frontend/ssoAuth.js` 或各系统的 `utils/ssoAuth.js`
2. **认证事件**: 使用 `utils/authEvents.js` 处理 Token 过期等事件
3. **API 服务**: 统一使用 `services/api.js` 封装 API 调用

### Portal 内功能模块

Portal 内新增功能模块（如项目管理）也必须遵循上述规范：
- 使用 Sider 侧边栏提供功能导航
- Header 提供"回到主页"按钮
- 布局与其他子系统保持一致

### 移动端适配

- 屏幕宽度 < 768px 时，Sider 切换为 Drawer 抽屉菜单
- Header 按钮文字隐藏，仅显示图标
- 使用 `isMobile` 状态判断并调整布局

---

## 文档维护规范

### CLAUDE.md 标准章节结构

所有子系统的 CLAUDE.md 文件必须包含以下章节（按顺序）：

1. **系统概述** - 包含部署状态和核心功能
2. **部署信息** - 表格格式，包含端口、路径、PM2服务名等
3. **技术栈** - 分前端、后端列出
4. **目录结构** - 树形结构
5. **API 路由清单** - 分类表格
6. **数据模型** - 表格格式
7. **前端页面/组件** - 列表说明
8. **配置文件** - 后端.env 和 前端.env 示例
9. **本地开发** - 命令示例
10. **已完成功能** - 复选框列表
11. **与其他系统的集成** - 表格
12. **注意事项** - 编号列表

### 文档更新规则

1. **新增功能时**: 同步更新 API 路由清单、数据模型、已完成功能
2. **修改端口时**: 同步更新主 CLAUDE.md 的子系统配置表
3. **新增子系统时**: 创建完整的 CLAUDE.md 并更新主文件
4. **重命名文件时**: 更新目录结构和相关引用

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 后端入口 | `main.py` | `Portal/backend/main.py` |
| 健康检查 | `/health` | `curl http://localhost:PORT/health` |
| API蓝图前缀 | `/api/xxx` | `url_prefix='/api/auth'` |
| PM2服务名 | `{系统小写}-backend` | `portal-backend` |

---

## 企业级文件存储系统

所有子系统共享统一的文件存储架构，位于 `storage/` 目录。

### 存储结构

```
storage/
├── active/                           # 活跃文件
│   └── {system}/{YYYY}/{MM}/{entity_type}/{entity_id}/
│       ├── _meta.json                # 元数据索引
│       ├── documents/                # 文档
│       ├── drawings/                 # 图纸
│       ├── contracts/                # 合同
│       └── versions/{file_id}/v1.0/  # 历史版本
├── archive/                          # 归档文件
│   └── {YYYY}/{system}/{entity_type}/{entity_id}.tar.gz
├── temp/                             # 临时文件（7天后清理）
└── quarantine/                       # 隔离区（30天后清理）
```

### 系统代码映射

| 代码 | 系统 | 实体类型示例 |
|------|------|-------------|
| portal | 门户系统 | projects, announcements |
| caigou | 采购系统 | suppliers, purchase_orders, contracts |
| quotation | 报价系统 | quotes, drawings |
| hr | 人事系统 | employees, contracts |
| crm | CRM系统 | customers, contacts |
| scm | 仓库系统 | inventory, warehouses |
| shm | 出货系统 | shipments, deliveries |
| eam | 设备系统 | equipment, maintenance |
| mes | 生产系统 | work_orders, production |

### 管理命令

```bash
# 初始化存储目录结构
python shared/storage_utils.py init

# 清理临时和隔离文件
python shared/storage_utils.py cleanup

# 查看存储统计
python shared/storage_utils.py stats

# 生成存储报告
python shared/storage_utils.py report --output report.json
```

### 核心模块

| 文件 | 说明 |
|------|------|
| `shared/file_storage_v2.py` | 企业级存储管理器 |
| `shared/storage_utils.py` | 存储管理工具 |
| `shared/migrations/create_file_storage_table.sql` | 数据库表结构 |

详细文档参见 `shared/CLAUDE.md` 和 `storage/README.md`。

---

## 项目进展

### 已完成
- 统一的 SSO 单点登录系统
- JWT Token 认证机制
- 跨系统用户身份验证
- GitHub Actions 自动部署
- 7 个子系统已部署上线 (Portal, HR, Account, Quotation, Caigou, SHM, CRM)
- DocPublisher 文档发布系统开发中
- TDM 产品技术标准管理系统开发中
- 企业级文件存储系统 (v2.0)
- Portal 项目管理功能 (P2: 回收站、看板视图、项目聊天)

### 待完成
- 完善各系统权限控制
- 添加操作日志审计
- 数据库索引优化
- API 请求限流
- 移动端适配
