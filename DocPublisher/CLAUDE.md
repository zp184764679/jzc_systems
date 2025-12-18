# DocPublisher - 文件发布器系统

## 系统概述

文件发布器 (DocPublisher) 是一个多语言文档管理和发布系统，用于统一管理和发布作业指导书、通知公告、操作手册等企业文档。支持中文、英文、日文三种语言一键切换。

### 技术架构

| 组件 | 技术 | 说明 |
|------|------|------|
| **后端 CMS** | Strapi 5 | Node.js headless CMS，内置 i18n |
| **前端** | React 19 + Vite + Ant Design | 遵循 JZC 项目标准 |
| **富文本编辑器** | CKEditor 5 | Strapi 集成 |
| **Markdown 渲染** | react-markdown + remark-gfm | 支持 GFM 语法 |
| **数据库** | SQLite (开发) / MySQL (生产) | 支持切换 |
| **语言支持** | zh, en, ja | 中文、英文、日文 |

---

## 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| Strapi 后端 | 1337 | Admin: http://localhost:1337/admin |
| 前端 (dev) | 6200 | http://localhost:6200/docs/ |

---

## 目录结构

```
DocPublisher/
├── strapi/                    # Strapi CMS 后端
│   ├── config/
│   │   ├── admin.js          # Admin panel 配置
│   │   ├── database.js       # 数据库配置 (SQLite/MySQL)
│   │   ├── middlewares.js    # 中间件配置
│   │   ├── plugins.js        # 插件配置
│   │   └── server.js         # 服务器配置
│   ├── src/
│   │   ├── api/              # 内容类型 (通过 Admin 创建)
│   │   ├── admin/            # Admin 自定义
│   │   └── index.js          # 应用入口
│   ├── public/
│   │   └── uploads/          # 上传文件目录
│   ├── .tmp/                  # SQLite 数据库
│   ├── .env                   # 环境变量
│   └── package.json
├── frontend/                  # React 前端
│   ├── src/
│   │   ├── main.jsx          # 应用入口
│   │   ├── App.jsx           # 主应用 (路由+布局)
│   │   ├── i18n/             # 前端界面翻译
│   │   │   ├── index.js      # i18n 配置
│   │   │   ├── zh.json       # 中文
│   │   │   ├── en.json       # 英文
│   │   │   └── ja.json       # 日文
│   │   ├── components/
│   │   │   └── LanguageSwitcher.jsx  # 语言切换器
│   │   ├── pages/
│   │   │   ├── DocumentList.jsx      # 文档列表页
│   │   │   └── DocumentView.jsx      # 文档查看页
│   │   └── services/
│   │       └── api.js        # Strapi API 客户端
│   ├── vite.config.js        # Vite 配置
│   └── package.json
└── CLAUDE.md                  # 本文档
```

---

## 常用命令

### 启动服务

```bash
# 使用 PM2 启动
pm2 start docs-strapi
pm2 start docs-frontend

# 或手动启动
cd DocPublisher/strapi && npm run develop
cd DocPublisher/frontend && npm run dev
```

### 查看日志

```bash
pm2 logs docs-strapi
pm2 logs docs-frontend
```

### 健康检查

```bash
curl http://127.0.0.1:1337/_health
```

### 构建前端

```bash
cd DocPublisher/frontend && npm run build
```

---

## Strapi 管理后台

访问地址: http://localhost:1337/admin

### 管理员账号

| 项目 | 值 |
|------|-----|
| 邮箱 | jzchardware@gmail.com |
| 密码 | ZPexak472008 |

### 配置步骤

1. **配置 i18n 语言**
   - Settings → Internationalization
   - 添加语言: zh (中文), en (English), ja (日本語)

2. **创建内容类型 Document**
   - Content-Type Builder → Create new collection type
   - 基础字段:
     - title (Text) - 启用 i18n
     - slug (UID)
     - docType (Enum: SOP, Notice, Manual, Other)
     - contentFormat (Enum: richtext, markdown) - 内容格式
     - content (Rich Text) - 启用 i18n，用于富文本
     - markdownContent (Text Long) - 启用 i18n，用于 Markdown
     - summary (Text Long) - 启用 i18n
     - version (Text)
     - publishedDate (Date)
     - category (Relation → Category)
     - attachments (Media Multiple)
     - isPublic (Boolean)
   - SOP 模板字段 (仅当 docType=SOP 时使用):
     - sopPurpose (Text Long) - 目的，启用 i18n
     - sopScope (Text Long) - 适用范围，启用 i18n
     - sopDefinitions (Text Long) - 定义，启用 i18n
     - sopResponsibilities (Text Long) - 职责，启用 i18n
     - sopProcedure (Text Long) - 操作步骤，启用 i18n
     - sopSafetyNotes (Text Long) - 安全注意事项，启用 i18n
     - sopReferences (Text Long) - 参考文档，启用 i18n
   - SOP 管理字段:
     - effectiveDate (Date) - 生效日期
     - reviewDate (Date) - 复审日期
     - author (Text) - 编写人
     - reviewer (Text) - 审核人
     - approver (Text) - 批准人

3. **创建内容类型 Category**
   - name (Text) - 启用 i18n
   - slug (UID)
   - description (Text) - 启用 i18n
   - sortOrder (Number)

4. **设置 API 权限**
   - Settings → Users & Permissions → Roles → Public
   - 勾选 Document: find, findOne
   - 勾选 Category: find, findOne

---

## 环境变量

### Strapi (.env)

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

---

## API 接口

### 获取文档列表

```
GET /api/documents?locale=zh&populate=*
```

### 获取单个文档

```
GET /api/documents?filters[slug][$eq]=doc-slug&locale=zh&populate=*
```

### 获取分类列表

```
GET /api/categories?locale=zh&sort=sortOrder:asc
```

---

## 前端国际化

前端使用 `react-i18next` 实现界面翻译。

### 语言切换

语言偏好存储在 `localStorage.getItem('docs-lang')`。

切换语言时会触发 `langChange` 事件，页面组件监听此事件重新加载对应语言的内容。

### 翻译文件

- `src/i18n/zh.json` - 中文界面
- `src/i18n/en.json` - 英文界面
- `src/i18n/ja.json` - 日文界面

---

## 已完成功能

- [x] 安装 CKEditor 插件
- [x] 在 Strapi Admin 配置 i18n 语言 (zh/en/ja)
- [x] 创建 Document 和 Category 内容类型
- [x] 设置 Public 角色 API 权限
- [x] 创建测试数据
- [x] 添加 Markdown 编辑支持 (react-markdown + remark-gfm)
- [x] 添加 SOP 模板字段 (目的、范围、定义、职责、步骤、安全、参考)
- [x] 前端支持 SOP 结构化显示
- [x] 添加 Strapi Admin 预览按钮 (在文档编辑页可预览前端效果)

## 待完成功能

- [ ] 添加 SSO 认证集成
- [ ] 添加 Portal 菜单入口
- [ ] 生产环境 Nginx 配置
- [ ] 多语言内容翻译 (英文/日文版本)

---

## 文档编辑指南

### 内容格式选择

| 格式 | 适用场景 | 编辑方式 |
|------|----------|----------|
| **richtext** | 简单文档、公告 | 使用 CKEditor 可视化编辑 |
| **markdown** | 技术文档、带代码的文档 | 使用 Markdown 语法编辑 |

### SOP 模板使用

当 `docType` 选择 **SOP** 时，可以使用结构化的 SOP 字段：

1. **目的 (sopPurpose)**: 说明该 SOP 的目的和意义
2. **适用范围 (sopScope)**: 定义 SOP 适用的人员、设备、场景
3. **定义 (sopDefinitions)**: 解释文档中使用的专业术语
4. **职责 (sopResponsibilities)**: 明确各角色的责任
5. **操作步骤 (sopProcedure)**: 详细的操作流程 (支持 Markdown)
6. **安全注意事项 (sopSafetyNotes)**: 安全警告和注意事项
7. **参考文档 (sopReferences)**: 相关的参考资料链接

**提示**: SOP 字段内容支持 Markdown 语法，可以使用列表、表格等格式。

### Markdown 语法示例

```markdown
## 二级标题

### 三级标题

**粗体文本** 和 *斜体文本*

- 无序列表项 1
- 无序列表项 2

1. 有序列表项 1
2. 有序列表项 2

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |

> 引用文本

`行内代码`

```
代码块
```
```

### 预览功能

在 Strapi Admin 编辑文档时，点击右上角的 **👁 预览文档** 按钮可以查看前端渲染效果。

---

## 注意事项

1. **多语言内容**: Strapi 的 i18n 管理文档内容的多语言版本，前端 i18n 管理界面文字的多语言
2. **API 路径**: 前端通过 `/strapi-api` 代理访问 Strapi API
3. **认证**: 公开文档不需要认证，管理后台需要单独的 Strapi 账号
4. **文件上传**: 上传的文件存储在 `strapi/public/uploads/` 目录
