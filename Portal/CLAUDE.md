# Portal 门户系统 - Claude Code 项目上下文

## 系统概述

Portal 是 JZC 企业管理系统的 SSO 认证中心和统一门户入口，负责用户登录认证、JWT Token 签发以及子系统导航。

**部署状态**: 已部署

### 核心功能
- 员工登录 / 供应商登录
- JWT Token 生成与验证
- 双因素认证 (2FA/TOTP)
- **密码管理**（修改密码、密码策略、密码状态）
- **审计日志**（操作记录、安全事件、统计分析）
- **登录历史**（登录记录、失败原因、设备信息）
- **会话管理**（查看活跃会话、注销会话、管理员批量管理）
- 子系统导航入口（按权限显示）
- PM2 服务管理（超级管理员）
- 邮件翻译助手（中英日三语）
- 文档翻译工具（PDF 购买仕样书翻译）

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 3002 |
| 前端端口(dev) | 3001 |
| 前端路径 | `/` |
| API路径 | `/api/` |
| PM2服务名 | portal-backend |
| 数据库 | cncplan (共享) |
| 健康检查 | `curl http://127.0.0.1:3002/health` |

---

## 技术栈

### 前端
- React 19.2.0
- Vite 7.2.2
- 纯 CSS (无 UI 框架)

### 后端
- Flask 3.0.0 + Flask-CORS 4.0.0
- PyJWT 2.8.0
- SQLAlchemy 2.0.23
- pyotp 2.9.0 (TOTP 2FA)
- bcrypt 4.1.2 (备用码加密)
- Anthropic 0.40.0 (Claude API)
- PyMuPDF 1.24.0 + reportlab 4.1.0 (PDF 处理)

---

## 目录结构

```
Portal/
├── backend/
│   ├── main.py                    # Flask 应用入口
│   ├── requirements.txt           # Python 依赖
│   ├── routes/
│   │   ├── system.py              # PM2 服务管理 API
│   │   ├── translate.py           # 文本翻译 API
│   │   ├── doc_translate.py       # 文档翻译 API
│   │   ├── two_factor.py          # 双因素认证 API
│   │   ├── password.py            # 密码管理 API
│   │   ├── audit.py               # 审计日志 API
│   │   └── sessions.py            # 会话管理 API
│   ├── translated_docs/           # 翻译后的 PDF 输出目录
│   └── venv/                      # Python 虚拟环境
├── src/
│   ├── main.jsx                   # React 入口
│   ├── App.jsx                    # 主应用组件
│   ├── Login.jsx                  # 员工登录页
│   ├── SupplierLogin.jsx          # 供应商登录页
│   ├── TwoFactorSetup.jsx         # 2FA 设置向导
│   ├── TwoFactorVerify.jsx        # 2FA 登录验证
│   ├── SystemManagement.jsx       # PM2 服务管理组件
│   ├── Translator.jsx             # 邮件翻译助手组件
│   ├── DocTranslator.jsx          # 文档翻译工具组件
│   ├── contexts/
│   │   └── AuthContext.jsx        # 认证上下文（含 2FA 支持）
│   └── pages/
│       └── Security/
│           ├── TwoFactorSettingsPage.jsx  # 2FA 设置页面
│           ├── PasswordSettingsPage.jsx   # 密码管理页面
│           ├── AuditLogsPage.jsx          # 审计日志页面
│           ├── LoginHistoryPage.jsx       # 登录历史页面
│           ├── SessionManagement.jsx      # 会话管理页面
│           └── SecurityPages.css          # 安全页面样式
├── dist/                          # 构建输出
├── package.json
├── vite.config.js
└── index.html
```

---

## API 路由清单

### 认证 API (main.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 员工登录 |
| POST | `/api/auth/supplier-login` | 供应商登录 |
| POST | `/api/auth/verify` | 验证 Token |
| GET | `/health` | 健康检查 |
| GET | `/` | 服务信息 |

### 系统管理 API (routes/system.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/system/services` | 获取所有 PM2 服务状态 |
| POST | `/api/system/service/<name>/start` | 启动指定服务 |
| POST | `/api/system/service/<name>/stop` | 停止指定服务 |
| POST | `/api/system/service/<name>/restart` | 重启指定服务 |
| GET | `/api/system/service/<name>/logs` | 获取服务日志 |
| POST | `/api/system/restart-all` | 重启所有服务 |
| POST | `/api/system/stop-all` | 停止所有服务 |

### 翻译 API (routes/translate.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/translate/text` | 翻译文本 |
| POST | `/api/translate/detect` | 检测语言 |

### 文档翻译 API (routes/doc_translate.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/doc-translate/upload` | 上传 PDF 并开始翻译 |
| GET | `/api/doc-translate/status/<task_id>` | 获取翻译任务状态 |
| GET | `/api/doc-translate/download/<task_id>` | 下载翻译后的 PDF |
| GET | `/api/doc-translate/list` | 列出所有翻译任务 |

### 双因素认证 API (routes/two_factor.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/2fa/status` | 获取当前用户 2FA 状态 |
| POST | `/api/2fa/setup` | 开始 2FA 设置（生成密钥和二维码） |
| POST | `/api/2fa/verify-setup` | 验证设置并启用 2FA |
| POST | `/api/2fa/verify` | 登录时验证 2FA 码（TOTP 或备用码） |
| POST | `/api/2fa/disable` | 禁用 2FA（需密码验证） |
| GET | `/api/2fa/backup-codes` | 获取备用码列表 |
| POST | `/api/2fa/backup-codes/regenerate` | 重新生成备用码 |
| GET | `/api/2fa/check-required/<user_id>` | 检查用户是否需要 2FA |

### 密码管理 API (routes/password.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/change-password` | 用户修改自己的密码 |
| POST | `/api/auth/reset-password` | 管理员重置用户密码 |
| POST | `/api/auth/unlock-account` | 管理员解锁用户账户 |
| GET | `/api/auth/password-policy` | 获取密码策略 |
| GET | `/api/auth/password-status` | 获取当前用户密码状态 |

### 审计日志 API (routes/audit.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/audit/logs` | 获取审计日志（管理员） |
| GET | `/api/audit/login-history` | 获取所有登录历史（管理员） |
| GET | `/api/audit/my-login-history` | 获取当前用户登录历史 |
| GET | `/api/audit/security-events` | 获取安全事件 |
| GET | `/api/audit/stats` | 获取审计统计 |
| GET | `/api/audit/action-types` | 获取操作类型列表 |
| GET | `/api/audit/modules` | 获取模块列表 |

### 会话管理 API (routes/sessions.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sessions` | 获取当前用户的活跃会话列表 |
| GET | `/api/sessions/all` | 获取所有用户会话（管理员） |
| DELETE | `/api/sessions/<id>` | 注销特定会话 |
| DELETE | `/api/sessions/other` | 注销当前用户其他会话 |
| POST | `/api/sessions/revoke-all/<user_id>` | 强制下线用户所有会话（管理员） |
| GET | `/api/sessions/statistics` | 获取会话统计（管理员） |

### 文件管理 API (routes/files.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/files/project/<id>` | 获取项目文件列表 |
| POST | `/api/files/upload` | 上传文件 |
| GET | `/api/files/<id>` | 获取文件详情 |
| GET | `/api/files/<id>/download` | 下载文件 |
| DELETE | `/api/files/<id>` | 删除文件（软删除） |
| POST | `/api/files/<id>/upload-version` | 上传文件新版本 |
| GET | `/api/files/<id>/versions` | 获取文件版本历史 |
| PUT | `/api/files/<id>/set-latest` | 设置为最新版本 |
| GET | `/api/files/<id>/version-tree` | 获取版本树 |
| GET | `/api/files/<id>/history` | 获取文件操作历史 |
| GET | `/api/files/<id>/preview` | 预览文件 |
| GET | `/api/files/<id>/preview-info` | 获取预览信息 |
| GET | `/api/files/search` | 搜索文件 |
| POST | `/api/files/batch/delete` | 批量删除文件 |
| POST | `/api/files/batch/download` | 批量下载（ZIP） |
| POST | `/api/files/<id>/share` | 创建分享链接 |
| GET | `/api/files/<id>/shares` | 获取文件的分享链接列表 |
| DELETE | `/api/files/<id>/share/<code>` | 停用分享链接 |

### 文件分享公开访问 API (routes/files.py - share_bp)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/share/<code>` | 获取分享信息（公开） |
| POST | `/api/share/<code>/verify` | 验证分享密码（公开） |
| GET | `/api/share/<code>/download` | 下载分享文件（公开） |
| GET | `/api/share/<code>/preview` | 预览分享文件（公开） |

### 邮件集成 API (routes/email_integration.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/emails` | 获取邮件列表（代理邮件翻译系统） |
| GET | `/api/emails/<id>` | 获取邮件详情 |
| GET | `/api/emails/<id>/task-extraction` | 获取邮件的预提取任务信息 |
| POST | `/api/emails/<id>/extract` | 完整提取流程（含智能匹配） |
| POST | `/api/emails/<id>/trigger-extraction` | 手动触发任务提取 |
| GET | `/api/emails/health` | 检查邮件系统健康状态 |

---

## 邮件集成功能

### 功能概述

从「供应商邮件翻译系统」选择邮件，通过 Ollama LLM 自动提取任务信息并填充任务表单。

### 架构

```
Portal 前端 (React)
    ↓ emailAPI 调用
Portal 后端 (Flask @ 3002)
    ↓ 服务令牌认证
┌─────────────────────────────────┐
│ 邮件翻译系统 (FastAPI @ 2000)   │
│ 数据库: email_translate         │
│ 预提取: task_extractions 表     │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ Ollama LLM @ 11434              │
│ 模型: qwen2.5:7b (开发)         │
│       qwen3:8b (生产)           │
└─────────────────────────────────┘
```

### 核心文件

| 文件 | 说明 |
|------|------|
| `backend/services/email_integration_service.py` | 邮件服务代理 + 智能匹配 |
| `backend/routes/email_integration.py` | `/api/emails/*` API 路由 |
| `src/components/Tasks/EmailImportPanel.jsx` | 邮件导入面板组件 |
| `src/components/Tasks/TaskFormModal.jsx` | 任务表单（含邮件导入按钮） |
| `src/services/api.js` | `emailAPI` 客户端 |

### 智能匹配

1. **项目匹配**: 根据邮件中提取的品番号 (part_number) 模糊匹配 Portal 项目
2. **员工匹配**: 根据提取的负责人姓名匹配 HR 系统员工

### 提取字段

| 邮件内容 | 提取字段 | 任务字段 | 匹配逻辑 |
|---------|---------|---------|---------|
| 主题+正文 | project_name | - | AI 推断项目名 |
| 正文 | customer_name | - | 发件人公司 |
| 正文 | order_no | - | 订单号/PO号 |
| 主题+正文 | title | title | AI 摘要 |
| 正文 | description | description | AI 提取 |
| 紧急程度 | priority | priority | AI 判断 |
| 日期 | due_date | due_date | 正则+AI |
| 品番号 | part_number | → project_id | 数据库匹配 |
| 联系人 | assignee_name | → assigned_to_id | HR 匹配 |

### 环境配置

```bash
# Portal/backend/.env
EMAIL_TRANSLATE_API_URL=http://localhost:2000
LLM_BASE=http://localhost:11434
LLM_MODEL=qwen2.5:7b
PORTAL_SERVICE_TOKEN=jzc-portal-integration-token-2025
```

### 预提取机制

邮件翻译完成后，Celery 异步任务自动提取任务信息存入 `task_extractions` 表。Portal 导入时直接读取，实现秒级响应。

---

## 数据模型

Portal 使用共享认证模块 (`shared/auth/`)，主要模型：

### User 模型
```python
class User:
    id: int
    username: str           # 用户名
    hashed_password: str    # 密码哈希
    full_name: str          # 全名
    email: str              # 邮箱
    user_type: str          # 'employee' | 'supplier'
    role: str               # 'user' | 'supervisor' | 'admin' | 'super_admin'
    permissions: list       # 系统权限列表
    is_active: bool         # 是否激活
```

### TwoFactorAuth 模型
```python
class TwoFactorAuth:
    id: int
    user_id: int            # 关联用户 ID
    secret_key: str         # TOTP 密钥（32字符 Base32）
    is_enabled: bool        # 是否已启用
    is_verified: bool       # 是否已验证（设置完成）
    recovery_email: str     # 恢复邮箱（可选）
    enabled_at: datetime    # 启用时间
    last_used_at: datetime  # 最后使用时间
```

### TwoFactorBackupCode 模型
```python
class TwoFactorBackupCode:
    id: int
    user_id: int            # 关联用户 ID
    code_hash: str          # 备用码哈希（SHA256）
    is_used: bool           # 是否已使用
    used_at: datetime       # 使用时间
    created_at: datetime    # 创建时间
```

### AuditLog 模型
```python
class AuditLog:
    id: int
    user_id: int            # 用户 ID
    username: str           # 用户名
    action_type: str        # 操作类型
    module: str             # 模块
    description: str        # 描述
    ip_address: str         # IP 地址
    user_agent: str         # 浏览器信息
    status: str             # success/failed
    details: JSON           # 详细信息
    created_at: datetime    # 创建时间
```

### LoginHistory 模型
```python
class LoginHistory:
    id: int
    user_id: int            # 用户 ID
    username: str           # 用户名
    ip_address: str         # IP 地址
    is_success: bool        # 是否成功
    failure_reason: str     # 失败原因
    device_type: str        # 设备类型
    browser: str            # 浏览器
    os: str                 # 操作系统
    login_time: datetime    # 登录时间
```

---

## 前端页面/组件

### App.jsx - 主页面
- 显示时间和日期
- 子系统卡片网格（按用户权限过滤）
- 工具区域（翻译助手、文档翻译）
- 用户信息和退出登录

### Login.jsx - 员工登录
- 用户名密码表单
- JWT Token 存储到 localStorage
- 2FA 验证流程集成

### TwoFactorSetup.jsx - 2FA 设置向导
- 二维码显示（扫描添加到验证器应用）
- 手动输入密钥选项
- 备用码显示和保存提醒
- 验证码输入确认启用

### TwoFactorVerify.jsx - 登录 2FA 验证
- TOTP 验证码输入
- 备用码输入切换
- 验证失败错误提示

### TwoFactorSettingsPage.jsx - 2FA 设置页面
- 2FA 状态展示
- 启用/禁用 2FA
- 重新生成备用码

### PasswordSettingsPage.jsx - 密码管理页面
- 密码状态卡片（过期时间、账户状态、上次修改时间）
- 密码策略展示（最小长度、复杂度要求、历史限制、过期天数）
- 修改密码表单（当前密码、新密码、确认密码）
- 密码强度实时检测（弱/中/强）
- 过期/锁定提醒

### AuditLogsPage.jsx - 审计日志页面
- 操作记录表格（时间、用户、操作类型、模块、描述、IP、状态）
- 多条件筛选（操作类型、模块、状态、搜索、日期范围）
- 分页导航
- 管理员专用

### LoginHistoryPage.jsx - 登录历史页面
- 统计卡片（7天总登录、成功/失败登录、成功率、活跃用户）
- 登录记录表格（时间、用户、状态、IP、设备、浏览器、OS、失败原因）
- 筛选功能（登录状态、日期范围）
- 分页导航
- 普通用户可查看自己的记录，管理员可查看所有

### SessionManagement.jsx - 会话管理页面
- 我的会话视图（查看当前用户所有活跃会话）
- 管理员视图（查看所有用户会话、按用户名筛选）
- 统计卡片（活跃会话数、活跃用户数、今日登录）
- 设备分布展示（桌面、移动端、平板）
- 注销会话功能
- 注销其他会话（一键注销当前用户的其他会话）
- 强制下线功能（管理员可强制下线指定用户所有会话）
- 当前会话标记

### SupplierLogin.jsx - 供应商登录
- 供应商专用登录入口
- 仅允许 user_type='supplier' 的用户

### SystemManagement.jsx - PM2 服务管理
- 服务状态列表
- 启动/停止/重启按钮
- 日志查看
- 仅 super_admin 可见

### Translator.jsx - 邮件翻译助手
- 中英日三语互译
- 支持上下文语境翻译
- 使用 Claude Opus 模型

### DocTranslator.jsx - 文档翻译工具
- PDF 上传
- 逐页图片识别翻译
- 生成带翻译的新 PDF

---

## 配置文件

### vite.config.js
```javascript
export default defineConfig({
  plugins: [react()],
  base: '/',
  server: {
    proxy: {
      '/api': 'http://localhost:3002'
    }
  }
})
```

### 前端环境变量 (.env)
```bash
VITE_API_BASE_URL=/api
VITE_SYSTEM_BASE_URL=            # 子系统基础 URL
VITE_PROCUREMENT_URL=/caigou
VITE_HR_URL=/hr
VITE_QUOTATION_URL=/quotation
VITE_ACCOUNT_URL=/account
VITE_CRM_URL=/crm
VITE_SCM_URL=/scm
VITE_SHM_URL=/shm
VITE_EAM_URL=/eam
VITE_MES_URL=/mes
```

---

## 本地开发

```bash
# 启动后端
cd Portal/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py

# 启动前端
cd Portal
npm install
npm run dev

# 构建前端
npm run build
```

---

## 已完成功能

- [x] 员工登录/供应商登录
- [x] JWT Token 生成与验证
- [x] 双因素认证 (2FA/TOTP)
  - [x] TOTP 验证器支持（Google/Microsoft Authenticator）
  - [x] 备用码支持（10个一次性码）
  - [x] 登录流程集成
  - [x] 设置向导（二维码+手动密钥）
- [x] 密码管理
  - [x] 用户修改密码
  - [x] 密码策略（最小8字符、复杂度要求）
  - [x] 密码历史记录（不能重复最近5次）
  - [x] 密码过期提醒（90天）
  - [x] 密码状态展示
  - [x] 管理员重置密码
  - [x] 账户锁定/解锁
- [x] 审计日志
  - [x] 操作记录查询
  - [x] 安全事件查看
  - [x] 统计分析
  - [x] 多条件筛选
- [x] 登录历史
  - [x] 用户登录记录查看
  - [x] 登录失败原因追踪
  - [x] 设备/浏览器/OS 信息
  - [x] 统计卡片（管理员）
- [x] 会话管理
  - [x] 用户查看自己的活跃会话
  - [x] 注销其他会话
  - [x] 管理员查看所有会话
  - [x] 管理员强制下线用户
  - [x] 会话统计与设备分布
- [x] 子系统导航入口
- [x] 基于角色的权限控制
- [x] PM2 服务管理界面
- [x] 邮件翻译助手（Claude Opus）
- [x] PDF 文档翻译工具
- [x] 移动端响应式适配
- [x] 邮件集成 - 智能任务创建
  - [x] 邮件列表代理（从翻译系统获取）
  - [x] AI 任务信息提取（Ollama LLM）
  - [x] 预提取机制（翻译后自动提取）
  - [x] 智能匹配项目（品番号）
  - [x] 智能匹配员工（姓名匹配 HR）
  - [x] EmailImportPanel 组件
  - [x] 集成到 TaskFormModal

---

## 与其他系统的集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| 所有子系统 | JWT Token | Portal 签发的 Token 可在所有子系统验证 |
| shared/auth | symlink | 共享认证模块，User 模型和 Token 验证函数 |
| 邮件翻译系统 | 服务令牌 API | 获取邮件列表和预提取的任务信息 |
| HR 系统 | JWT Token 代理 | 员工姓名匹配查询 |

---

## 注意事项

1. **认证入口分离**: 员工用 `/api/auth/login`，供应商用 `/api/auth/supplier-login`
2. **Token 传递**: 跳转子系统时通过 URL 参数 `?token=xxx` 传递
3. **权限过滤**: 子系统卡片根据用户 `permissions` 和 `role` 过滤显示
4. **翻译代理**: 翻译功能需要配置 HTTP 代理 (`127.0.0.1:8800`)
5. **PM2 命令**: 使用 PowerShell 执行 PM2 命令
6. **2FA 流程**: 启用 2FA 后，登录时返回 `requires_2fa: true`，前端需跳转到 2FA 验证页面
7. **备用码安全**: 备用码使用 SHA256 哈希存储，每个码只能使用一次
8. **2FA 依赖**: 需要安装 `pyotp` 和 `bcrypt` 库

---

## 功能模块 UI 设计规范（重要）

Portal 内的功能模块（如项目管理、通知中心）**必须遵循其他子系统的布局模式**：

### 布局要求

```
┌─────────────────────────────────────────────────────────────────┐
│ Header                                                          │
│ [系统标题] | 用户信息 | [回到主页] [退出登录]                    │
├───────────┬─────────────────────────────────────────────────────┤
│ Sider     │                                                     │
│ 侧边菜单   │              Content (内容区域)                     │
│ - 项目列表 │                                                     │
│ - 通知中心 │                                                     │
│ - 设置    │                                                     │
└───────────┴─────────────────────────────────────────────────────┘
```

### 必需元素

| 元素 | 说明 |
|------|------|
| Header "回到主页"按钮 | 从项目详情等页面返回 Portal 主页 |
| Sider 侧边菜单 | 功能导航（项目列表、通知、设置等） |
| 移动端 Drawer | 屏幕 < 768px 时使用抽屉菜单 |
| 用户信息显示 | Header 右侧显示用户名和角色 |

### 参考文件

开发 Portal 内功能模块时，**必须参考**：
- `HR/frontend/src/App.jsx` - 标准布局模板
- `account/frontend/src/App.jsx` - 标准布局模板

### 已修复

- [x] `src/components/Layout/AppLayout.jsx` - 已添加 Sider 侧边栏
- [x] 项目管理模块已与其他子系统布局一致
