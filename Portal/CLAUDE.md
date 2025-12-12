# Portal 门户系统 - Claude Code 项目上下文

## 系统概述

Portal 是 JZC 企业管理系统的 SSO 认证中心和统一门户入口，负责用户登录认证、JWT Token 签发以及子系统导航。

### 核心功能
- 员工登录 / 供应商登录
- JWT Token 生成与验证
- 子系统导航入口（按权限显示）
- PM2 服务管理（超级管理员）
- 邮件翻译助手（中英日三语）
- 文档翻译工具（PDF 购买仕样书翻译）

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 3002 |
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
│   │   └── doc_translate.py       # 文档翻译 API
│   ├── translated_docs/           # 翻译后的 PDF 输出目录
│   └── venv/                      # Python 虚拟环境
├── src/
│   ├── main.jsx                   # React 入口
│   ├── App.jsx                    # 主应用组件
│   ├── Login.jsx                  # 员工登录页
│   ├── SupplierLogin.jsx          # 供应商登录页
│   ├── SystemManagement.jsx       # PM2 服务管理组件
│   ├── Translator.jsx             # 邮件翻译助手组件
│   └── DocTranslator.jsx          # 文档翻译工具组件
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
- [x] 子系统导航入口
- [x] 基于角色的权限控制
- [x] PM2 服务管理界面
- [x] 邮件翻译助手（Claude Opus）
- [x] PDF 文档翻译工具
- [x] 移动端响应式适配

---

## 与其他系统的集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| 所有子系统 | JWT Token | Portal 签发的 Token 可在所有子系统验证 |
| shared/auth | symlink | 共享认证模块，User 模型和 Token 验证函数 |

---

## 注意事项

1. **认证入口分离**: 员工用 `/api/auth/login`，供应商用 `/api/auth/supplier-login`
2. **Token 传递**: 跳转子系统时通过 URL 参数 `?token=xxx` 传递
3. **权限过滤**: 子系统卡片根据用户 `permissions` 和 `role` 过滤显示
4. **翻译代理**: 翻译功能需要配置 HTTP 代理 (`127.0.0.1:8800`)
5. **PM2 命令**: 使用 PowerShell 执行 PM2 命令
