# EAM 设备资产管理系统 - Claude Code 项目上下文

## 系统概述

EAM (Enterprise Asset Management) 是 JZC 企业管理系统的设备资产管理模块，负责设备台账、维护保养、点检管理等。

**部署状态**: 未部署

### 计划功能
- 设备台账管理
- 设备分类管理
- 设备维护保养计划
- 设备点检管理
- 设备故障报修
- 备件管理
- 设备利用率统计

---

## 计划部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 8008 |
| 前端路径 | `/eam/` |
| API路径 | `/eam/api/` |
| PM2服务名 | eam-backend |
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
EAM/
├── backend/
│   ├── main.py                      # Flask 应用入口
│   ├── requirements.txt             # Python 依赖
│   ├── app/
│   │   ├── __init__.py              # Flask 应用工厂
│   │   ├── models/                  # 数据模型
│   │   ├── routes/                  # API 路由
│   │   └── services/                # 业务服务
│   ├── eam.db                       # SQLite 数据库（开发）
│   └── (无 venv)
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   └── machines/            # 设备管理模块
│   │   ├── services/
│   │   └── utils/
│   ├── ecosystem.config.cjs         # PM2 配置
│   └── dist/
└── package.json
```

---

## 计划 API 路由

### 设备 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/machines` | 获取设备列表 |
| GET | `/api/machines/<id>` | 获取设备详情 |
| POST | `/api/machines` | 创建设备 |
| PUT | `/api/machines/<id>` | 更新设备 |
| DELETE | `/api/machines/<id>` | 删除设备 |

### 维护保养 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/maintenance` | 获取维护计划 |
| POST | `/api/maintenance` | 创建维护记录 |
| PUT | `/api/maintenance/<id>` | 更新维护记录 |

### 点检 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/inspections` | 获取点检记录 |
| POST | `/api/inspections` | 创建点检记录 |

### 集成 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/integration/machines` | 供 MES 查询设备状态 |
| GET | `/api/integration/machine-status/<id>` | 查询设备当前状态 |

---

## 计划数据模型

### Machine 设备

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String | 设备编码 |
| name | String | 设备名称 |
| category | String | 设备分类 |
| brand | String | 品牌 |
| model | String | 型号 |
| serial_no | String | 序列号 |
| location | String | 位置 |
| purchase_date | Date | 购置日期 |
| status | String | 状态（正常/维修/停用） |
| responsible_person | String | 负责人 |

### Maintenance 维护记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| machine_id | Integer | 设备 ID |
| type | String | 类型（保养/维修） |
| description | Text | 描述 |
| cost | Float | 费用 |
| date | Date | 日期 |
| operator | String | 操作人 |

---

## 本地开发

```bash
# 启动后端
cd EAM/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py

# 启动前端
cd EAM/frontend
npm install
npm run dev
```

---

## 开发状态

- [ ] 基础框架搭建
- [ ] 设备台账管理
- [ ] 设备分类管理
- [ ] 维护保养计划
- [ ] 点检管理
- [ ] 故障报修
- [ ] 系统集成 API

---

## 与其他系统的集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| MES | API 调用 | MES 查询设备状态 |
| HR | API 调用 | 获取设备负责人信息 |

---

## 注意事项

1. **未部署**: EAM 系统尚未部署到生产环境
2. **端口**: 计划使用 8008 端口
3. **数据库**: 开发使用 SQLite，生产需配置 MySQL
4. **无 venv**: 后端目录暂无虚拟环境
