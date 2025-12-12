# SCM 仓库管理系统 - Claude Code 项目上下文

## 系统概述

SCM (Supply Chain Management - Warehouse) 是 JZC 企业管理系统的仓库管理模块，负责库存管理、入库出库、仓位管理等。

**部署状态**: 未部署

### 计划功能
- 物料管理
- 库存管理
- 入库管理
- 出库管理
- 仓位管理
- 库存盘点
- 库存预警
- 物料领用

---

## 计划部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 8005 |
| 前端路径 | `/scm/` |
| API路径 | `/scm/api/` |
| PM2服务名 | scm-backend |
| 数据库 | cncplan |

---

## 技术栈

### 前端
- React 19.2.0
- Vite
- Ant Design 5.28.1

### 后端
- Flask 3.1.0 + Flask-CORS
- Flask-SQLAlchemy + Flask-Migrate
- PyMySQL
- SQLAlchemy >= 2.0

---

## 目录结构

```
SCM/
├── backend/
│   ├── main.py                      # Flask 应用入口
│   ├── requirements.txt             # Python 依赖
│   ├── app/
│   │   ├── __init__.py              # Flask 应用工厂
│   │   ├── models/                  # 数据模型
│   │   ├── routes/                  # API 路由
│   │   └── services/                # 业务服务
│   ├── scm.db                       # SQLite 数据库（开发）
│   └── venv/
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── inventory/           # 库存模块
│   │   │   └── settings/            # 设置模块
│   │   ├── services/
│   │   └── utils/
│   └── dist/
└── package.json
```

---

## 计划 API 路由

### 物料 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/materials` | 获取物料列表 |
| GET | `/api/materials/<id>` | 获取物料详情 |
| POST | `/api/materials` | 创建物料 |
| PUT | `/api/materials/<id>` | 更新物料 |
| DELETE | `/api/materials/<id>` | 删除物料 |

### 库存 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/inventory` | 获取库存列表 |
| GET | `/api/inventory/<id>` | 获取库存详情 |
| POST | `/api/inventory/in` | 入库 |
| POST | `/api/inventory/out` | 出库 |
| POST | `/api/inventory/check` | 库存盘点 |

### 集成 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/integration/inventory` | 供其他系统查询库存 |
| POST | `/api/integration/deduct` | 扣减库存（出货系统调用） |

---

## 计划数据模型

### Material 物料

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String | 物料编码 |
| name | String | 物料名称 |
| category | String | 分类 |
| unit | String | 单位 |
| spec | String | 规格 |
| min_stock | Float | 最低库存 |
| max_stock | Float | 最高库存 |

### Inventory 库存

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| material_id | Integer | 物料 ID |
| warehouse_id | Integer | 仓库 ID |
| bin_code | String | 仓位 |
| quantity | Float | 数量 |
| batch_no | String | 批次号 |

---

## 本地开发

```bash
# 启动后端
cd SCM/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py

# 启动前端
cd SCM/frontend
npm install
npm run dev
```

---

## 开发状态

- [ ] 基础框架搭建
- [ ] 物料管理
- [ ] 库存管理
- [ ] 入库/出库
- [ ] 仓位管理
- [ ] 库存盘点
- [ ] 系统集成 API

---

## 与其他系统的集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| SHM | API 调用 | 出货时扣减库存 |
| MES | API 调用 | 生产领料 |
| 采购 | API 调用 | 采购入库 |

---

## 注意事项

1. **未部署**: SCM 系统尚未部署到生产环境
2. **端口**: 计划使用 8005 端口
3. **数据库**: 开发使用 SQLite，生产需配置 MySQL
