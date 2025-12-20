# TDM 产品技术标准管理系统

## 系统概述

TDM (Technical Data Management) 是集中管理和展示产品技术参数、检验标准、工艺文件的技术数据管理系统。

**部署状态**: 开发中

### 核心功能
- **产品主数据管理** - 以品番号为中心组织所有技术资料
- **技术规格管理** - 材料、尺寸、精度、处理要求等
- **检验标准管理** - IQC/IPQC/FQC/OQC 检验标准
- **工艺文件管理** - 工序、设备、参数等工艺信息
- **文件关联** - 与 Portal FileIndex 集成
- **版本控制** - 所有技术文档支持版本追溯

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 系统目录 | `TDM/` |
| 后端端口 | 8009 |
| 前端dev端口 | 7600 |
| 前端路径 | `/tdm/` |
| API路径 | `/tdm/api/` |
| PM2服务名 | tdm-backend |
| 数据库 | cncplan (共享) |

---

## 技术栈

### 后端
- Python 3.9+
- Flask 2.0+
- SQLAlchemy 2.0+
- PyMySQL
- PyJWT (SSO认证)

### 前端
- React 18
- Vite
- Ant Design 5
- Axios
- Day.js

---

## 目录结构

```
TDM/
├── backend/
│   ├── main.py                    # Flask 应用入口
│   ├── config.py                  # 配置文件
│   ├── requirements.txt           # Python 依赖
│   ├── models/
│   │   ├── __init__.py
│   │   ├── product_master.py      # 产品主数据模型
│   │   ├── technical_spec.py      # 技术规格模型
│   │   ├── inspection_criteria.py # 检验标准模型
│   │   ├── process_document.py    # 工艺文件模型
│   │   └── product_file_link.py   # 文件关联模型
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── products.py            # 产品 API
│   │   ├── technical_specs.py     # 技术规格 API
│   │   ├── inspection.py          # 检验标准 API
│   │   ├── process_docs.py        # 工艺文件 API
│   │   └── files.py               # 文件管理 API
│   └── services/
│       └── version_service.py     # 版本控制服务
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── ProductList.jsx    # 产品列表
│   │   │   └── ProductDetail.jsx  # 产品详情
│   │   ├── components/
│   │   │   ├── TechSpecPanel.jsx  # 技术规格面板
│   │   │   ├── InspectionPanel.jsx # 检验标准面板
│   │   │   ├── ProcessPanel.jsx   # 工艺文件面板
│   │   │   └── FilePanel.jsx      # 文件管理面板
│   │   ├── services/
│   │   │   └── api.js             # API 封装
│   │   └── utils/
│   │       └── ssoAuth.js         # SSO 认证
│   ├── package.json
│   ├── vite.config.js
│   └── dist/                      # 构建输出
└── CLAUDE.md
```

---

## API 路由清单

### 产品 API (`/api/products`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/products` | 产品列表 (分页+搜索) |
| GET | `/api/products/{id}` | 产品详情 |
| GET | `/api/products/by-part/{part_number}` | 按品番号查询 |
| POST | `/api/products` | 创建产品 |
| PUT | `/api/products/{id}` | 更新产品 |
| DELETE | `/api/products/{id}` | 删除产品 |
| GET | `/api/products/search` | 搜索产品 |
| GET | `/api/products/categories` | 分类列表 |
| GET | `/api/products/statistics` | 统计数据 |

### 技术规格 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/products/{id}/tech-specs` | 获取产品技术规格 |
| POST | `/api/products/{id}/tech-specs` | 创建技术规格 |
| GET | `/api/tech-specs/{id}` | 获取规格详情 |
| PUT | `/api/tech-specs/{id}` | 更新技术规格 |
| POST | `/api/tech-specs/{id}/new-version` | 创建新版本 |
| GET | `/api/tech-specs/{id}/versions` | 版本历史 |

### 检验标准 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/products/{id}/inspection` | 获取检验标准 |
| POST | `/api/products/{id}/inspection` | 创建检验标准 |
| GET | `/api/inspection/{id}` | 获取标准详情 |
| PUT | `/api/inspection/{id}` | 更新检验标准 |
| POST | `/api/inspection/{id}/new-version` | 创建新版本 |
| POST | `/api/inspection/{id}/approve` | 审批 |
| GET | `/api/inspection/{id}/versions` | 版本历史 |
| GET | `/api/inspection/stages` | 检验阶段列表 |

### 工艺文件 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/products/{id}/processes` | 获取工艺文件 |
| POST | `/api/products/{id}/processes` | 创建工艺 |
| GET | `/api/processes/{id}` | 获取工艺详情 |
| PUT | `/api/processes/{id}` | 更新工艺 |
| DELETE | `/api/processes/{id}` | 删除工艺 |
| POST | `/api/processes/{id}/new-version` | 创建新版本 |
| GET | `/api/processes/{id}/versions` | 版本历史 |
| POST | `/api/products/{id}/processes/reorder` | 重新排序 |

### 文件关联 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/products/{id}/files` | 获取关联文件 |
| GET | `/api/products/{id}/files/by-type` | 按类型分组获取 |
| POST | `/api/products/{id}/files/link` | 关联文件 |
| PUT | `/api/products/{id}/files/{link_id}` | 更新关联 |
| DELETE | `/api/products/{id}/files/{link_id}` | 取消关联 |
| GET | `/api/file-types` | 文件类型列表 |

---

## 数据模型

### tdm_product_master (产品主数据)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| part_number | VARCHAR(100) | 品番号 (唯一) |
| product_name | VARCHAR(200) | 产品名称 |
| product_name_en | VARCHAR(200) | 英文名称 |
| customer_id | INT | 客户ID |
| customer_name | VARCHAR(200) | 客户名称 |
| customer_part_number | VARCHAR(100) | 客户料号 |
| category | VARCHAR(50) | 产品分类 |
| sub_category | VARCHAR(50) | 子分类 |
| status | ENUM | draft/active/discontinued/obsolete |
| current_version | VARCHAR(20) | 当前版本 |
| description | TEXT | 产品描述 |
| remarks | TEXT | 备注 |

### tdm_technical_specs (技术规格)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| product_id | BIGINT | 产品ID (外键) |
| part_number | VARCHAR(100) | 品番号 |
| material_code | VARCHAR(50) | 材料编码 |
| material_name | VARCHAR(100) | 材料名称 |
| material_spec | VARCHAR(200) | 材料规格 |
| density | DECIMAL(10,4) | 密度 g/cm³ |
| outer_diameter | DECIMAL(10,4) | 外径 mm |
| length | DECIMAL(10,4) | 长度 mm |
| weight | DECIMAL(10,4) | 重量 kg |
| tolerance_class | VARCHAR(50) | 公差等级 |
| surface_roughness | VARCHAR(50) | 表面粗糙度 Ra |
| heat_treatment | VARCHAR(200) | 热处理 |
| surface_treatment | VARCHAR(200) | 表面处理 |
| special_requirements | TEXT | 特殊要求 |
| version | VARCHAR(20) | 版本 |
| is_current | BOOLEAN | 是否当前版本 |

### tdm_inspection_criteria (检验标准)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| product_id | BIGINT | 产品ID (外键) |
| criteria_code | VARCHAR(50) | 标准编码 |
| criteria_name | VARCHAR(200) | 标准名称 |
| inspection_stage | ENUM | incoming/process/final/outgoing |
| inspection_method | ENUM | full/sampling/skip |
| sampling_plan | VARCHAR(100) | 抽样方案 |
| inspection_items | JSON | 检验项目列表 |
| aql_critical | DECIMAL(5,2) | AQL 严重 |
| aql_major | DECIMAL(5,2) | AQL 主要 |
| aql_minor | DECIMAL(5,2) | AQL 次要 |
| status | ENUM | draft/active/deprecated |
| version | VARCHAR(20) | 版本 |
| is_current | BOOLEAN | 是否当前版本 |

### tdm_process_documents (工艺文件)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| product_id | BIGINT | 产品ID (外键) |
| process_code | VARCHAR(50) | 工艺编码 |
| process_name | VARCHAR(100) | 工艺名称 |
| process_sequence | INT | 工序顺序 |
| setup_time | DECIMAL(10,4) | 准备时间 (分钟) |
| cycle_time | DECIMAL(10,4) | 加工周期 (分钟) |
| machine_type | VARCHAR(100) | 设备类型 |
| machine_model | VARCHAR(100) | 设备型号 |
| parameters | JSON | 工艺参数 |
| version | VARCHAR(20) | 版本 |
| is_current | BOOLEAN | 是否当前版本 |

### tdm_product_file_links (文件关联)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| product_id | BIGINT | 产品ID (外键) |
| file_index_id | BIGINT | FileIndex表ID |
| file_type | ENUM | drawing/specification/... |
| is_primary | BOOLEAN | 是否主文件 |
| display_order | INT | 显示顺序 |

---

## 配置文件

### 后端 .env

```bash
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# 数据库
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=cncplan

# 认证数据库
AUTH_DB_HOST=localhost
AUTH_DB_PORT=3306
AUTH_DB_USER=root
AUTH_DB_PASSWORD=your-password
AUTH_DB_NAME=cncplan
```

### 前端 .env

```bash
VITE_API_BASE_URL=/tdm/api
VITE_PORTAL_URL=/
```

---

## 本地开发

### 后端

```bash
cd TDM/backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

### 前端

```bash
cd TDM/frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建
npm run build
```

---

## 与其他系统的集成

| 集成系统 | 集成方式 | 说明 |
|----------|----------|------|
| Portal | SSO Token | 统一身份认证 |
| Portal FileIndex | file_index_id 关联 | 文件中心集成 |
| 报价系统 | quotation_product_id | 产品数据同步 |

---

## 已完成功能

- [x] 产品主数据 CRUD
- [x] 技术规格管理 (含版本控制)
- [x] 检验标准管理 (含审批、版本控制)
- [x] 工艺文件管理 (含排序、版本控制)
- [x] 文件关联管理
- [x] SSO 单点登录
- [x] 响应式布局

---

## 注意事项

1. **品番号唯一性**: part_number 在 tdm_product_master 表中唯一
2. **版本控制**: 技术规格、检验标准、工艺文件均支持版本控制，通过 is_current 标识当前版本
3. **文件关联**: 通过 file_index_id 关联 Portal 的 FileIndex 表，不存储实际文件
4. **SSO 认证**: 使用 Portal 签发的 JWT Token，需确保 JWT_SECRET_KEY 一致
5. **数据库**: 与 Portal/SHM 共享 cncplan 数据库
