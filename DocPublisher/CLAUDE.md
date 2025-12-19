# DocPublisher 文档发布系统 - Claude Code 项目上下文

## 系统概述

DocPublisher 是 JZC 企业管理系统的文档发布模块，用于统一管理和发布作业指导书 (SOP)、通知公告、操作手册等企业文档。支持中文、英文、日文三种语言一键切换。

### 核心功能
- 多语言文档管理（中/英/日）
- SOP 标准作业程序模板
- 富文本 (CKEditor) 和 Markdown 双格式支持
- 文档分类管理
- 文件附件上传
- 客户端文档预览

### 部署状态
**开发中** - 尚未部署到生产环境

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 1337 (Strapi) |
| 前端端口(dev) | 6200 |
| 前端路径 | `/docs/` |
| API路径 | `/strapi-api/` |
| Admin路径 | `/strapi-admin/` |
| PM2服务名 | docs-strapi, docs-frontend |
| 数据库 | SQLite (开发) / MySQL (生产) |
| 健康检查 | `curl http://127.0.0.1:1337/_health` |

---

## 技术栈

### 前端
- React 19 + Vite
- Ant Design
- react-i18next (界面国际化)
- react-markdown + remark-gfm (Markdown 渲染)

### 后端
- Strapi 5 (Node.js Headless CMS)
- CKEditor 5 (富文本编辑器)
- i18n 插件 (内容国际化)

---

## 目录结构

```
DocPublisher/
├── strapi/                    # Strapi CMS 后端
│   ├── config/
│   │   ├── admin.js          # Admin panel 配置
│   │   ├── database.js       # 数据库配置
│   │   ├── middlewares.js    # 中间件配置
│   │   ├── plugins.js        # 插件配置
│   │   └── server.js         # 服务器配置
│   ├── src/
│   │   ├── api/              # 内容类型定义
│   │   ├── admin/            # Admin 自定义
│   │   └── index.js          # 应用入口
│   ├── public/uploads/       # 上传文件目录
│   ├── .tmp/                 # SQLite 数据库
│   └── .env                  # 环境变量
├── frontend/
│   ├── src/
│   │   ├── main.jsx          # React 入口
│   │   ├── App.jsx           # 主应用 (路由+布局)
│   │   ├── i18n/             # 前端界面翻译
│   │   │   ├── index.js      # i18n 配置
│   │   │   ├── zh.json       # 中文
│   │   │   ├── en.json       # 英文
│   │   │   └── ja.json       # 日文
│   │   ├── components/
│   │   │   └── LanguageSwitcher.jsx
│   │   ├── pages/
│   │   │   ├── DocumentList.jsx
│   │   │   └── DocumentView.jsx
│   │   └── services/
│   │       └── api.js        # Strapi API 客户端
│   ├── vite.config.js
│   └── package.json
└── CLAUDE.md
```

---

## API 路由清单

### 文档 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/documents` | 获取文档列表 |
| GET | `/api/documents/:id` | 获取单个文档 |
| GET | `/api/documents?filters[slug][$eq]=xxx` | 按 slug 查询文档 |
| POST | `/api/documents` | 创建文档 (需认证) |
| PUT | `/api/documents/:id` | 更新文档 (需认证) |
| DELETE | `/api/documents/:id` | 删除文档 (需认证) |

### 分类 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/categories` | 获取分类列表 |
| GET | `/api/categories/:id` | 获取单个分类 |

### 通用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| locale | 语言代码 | `?locale=zh` |
| populate | 关联数据 | `?populate=*` |
| sort | 排序 | `?sort=publishedDate:desc` |

---

## 数据模型

### Document 文档

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| title | String | 标题 (i18n) |
| slug | UID | URL 标识 |
| docType | Enum | 类型: SOP, Notice, Manual, Other |
| contentFormat | Enum | 格式: richtext, markdown |
| content | RichText | 富文本内容 (i18n) |
| markdownContent | Text | Markdown 内容 (i18n) |
| summary | Text | 摘要 (i18n) |
| version | String | 版本号 |
| publishedDate | Date | 发布日期 |
| category | Relation | 关联分类 |
| attachments | Media | 附件文件 |
| isPublic | Boolean | 是否公开 |

### Document SOP 扩展字段

| 字段 | 类型 | 说明 |
|------|------|------|
| sopPurpose | Text | 目的 (i18n) |
| sopScope | Text | 适用范围 (i18n) |
| sopDefinitions | Text | 定义 (i18n) |
| sopResponsibilities | Text | 职责 (i18n) |
| sopProcedure | Text | 操作步骤 (i18n) |
| sopSafetyNotes | Text | 安全注意事项 (i18n) |
| sopReferences | Text | 参考文档 (i18n) |
| effectiveDate | Date | 生效日期 |
| reviewDate | Date | 复审日期 |
| author | String | 编写人 |
| reviewer | String | 审核人 |
| approver | String | 批准人 |

### Category 分类

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String | 名称 (i18n) |
| slug | UID | URL 标识 |
| description | Text | 描述 (i18n) |
| sortOrder | Number | 排序顺序 |

---

## 前端页面/组件

### 页面列表

| 页面 | 路径 | 说明 |
|------|------|------|
| 文档列表 | `/docs/` | 按分类浏览文档，支持搜索筛选 |
| 文档详情 | `/docs/:slug` | 查看文档内容，支持 Markdown/富文本渲染 |

### 核心组件

| 组件 | 位置 | 说明 |
|------|------|------|
| LanguageSwitcher | `components/LanguageSwitcher.jsx` | 语言切换器 (中/英/日) |
| DocumentCard | `components/DocumentCard.jsx` | 文档卡片 |
| SOPViewer | `components/SOPViewer.jsx` | SOP 结构化显示 |
| MarkdownRenderer | `components/MarkdownRenderer.jsx` | Markdown 渲染器 |

---

## 配置文件

### Strapi 环境变量 (.env)
```bash
HOST=0.0.0.0
PORT=1337
APP_KEYS=your-app-keys
API_TOKEN_SALT=your-salt
ADMIN_JWT_SECRET=your-admin-secret
JWT_SECRET=jzc-dev-shared-secret-key-2025

# 开发环境使用 SQLite
DATABASE_CLIENT=sqlite
DATABASE_FILENAME=data.db

# 生产环境使用 MySQL
# DATABASE_CLIENT=mysql
# DATABASE_HOST=localhost
# DATABASE_PORT=3306
# DATABASE_NAME=cncplan
# DATABASE_USERNAME=app
# DATABASE_PASSWORD=app

# 默认语言
STRAPI_PLUGIN_I18N_INIT_LOCALE_CODE=zh
```

### 前端环境变量 (.env)
```bash
VITE_STRAPI_URL=http://localhost:1337
VITE_API_BASE_URL=/strapi-api
```

---

## 本地开发

```bash
# 启动 Strapi 后端
cd DocPublisher/strapi
npm install
npm run develop
# Admin: http://localhost:1337/admin

# 启动前端
cd DocPublisher/frontend
npm install
npm run dev
# 前端运行在 http://localhost:6200
```

### Strapi Admin 账号

| 项目 | 值 |
|------|-----|
| 邮箱 | jzchardware@gmail.com |
| 密码 | ZPexak472008 |

---

## 已完成功能

- [x] Strapi CMS 安装配置
- [x] CKEditor 富文本插件集成
- [x] i18n 多语言配置 (zh/en/ja)
- [x] Document 内容类型创建
- [x] Category 分类类型创建
- [x] Public API 权限配置
- [x] Markdown 内容支持
- [x] SOP 模板字段 (目的、范围、职责等)
- [x] 前端文档列表页
- [x] 前端文档详情页
- [x] 语言切换功能
- [x] SOP 结构化显示
- [x] Admin 预览按钮
- [ ] SSO 认证集成
- [ ] Portal 菜单入口
- [ ] 生产环境 Nginx 配置
- [ ] 多语言内容翻译

---

## 与其他系统的集成

| 调用方 | 被调用方 | 集成内容 | 状态 |
|--------|----------|----------|------|
| DocPublisher | Portal | SSO 认证、用户信息 | 待实现 |
| Portal | DocPublisher | 菜单入口链接 | 待实现 |
| MES | DocPublisher | 工序 SOP 文档查看 | 待实现 |

---

## 注意事项

1. **多语言内容**: Strapi i18n 管理文档内容多语言，前端 i18n 管理界面文字多语言
2. **API 路径**: 前端通过 `/strapi-api` 代理访问 Strapi API
3. **认证分离**: 公开文档不需要认证，Strapi Admin 使用独立账号
4. **文件上传**: 上传文件存储在 `strapi/public/uploads/`
5. **语言存储**: 语言偏好存储在 `localStorage.getItem('docs-lang')`
6. **后端特殊**: 使用 Strapi (Node.js) 而非 Flask，健康检查路径为 `/_health`
