# MES 制造执行系统 - Claude Code 项目上下文

## 系统概述

MES (Manufacturing Execution System) 是 JZC 企业管理系统的制造执行模块，负责生产计划执行、工单管理、生产数据采集和质量管理。

**部署状态**: 未部署

### 计划功能
- 工单管理
- 生产排程
- 生产报工
- 质量检验
- 生产数据采集
- 生产进度跟踪
- 设备状态监控
- 生产看板

---

## 计划部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 8007 |
| 前端路径 | `/mes/` |
| API路径 | `/mes/api/` |
| PM2服务名 | mes-backend |
| 数据库 | cncplan |

---

## 技术栈

### 前端
- React 19.2.0
- Vite
- 纯 CSS（无 Ant Design）

### 后端
- Flask + Flask-CORS
- Flask-SQLAlchemy
- SQLAlchemy
- PyMySQL

---

## 目录结构

```
MES/
├── backend/
│   ├── app.py                       # Flask 应用入口
│   ├── database.py                  # 数据库配置
│   ├── requirements.txt             # Python 依赖
│   ├── models/
│   │   ├── work_order.py            # 工单模型
│   │   ├── production_record.py     # 生产记录模型
│   │   ├── quality_inspection.py    # 质检模型
│   │   └── base_data.py             # 基础数据
│   ├── routes/
│   │   ├── work_order_routes.py     # 工单路由
│   │   ├── production_routes.py     # 生产路由
│   │   ├── dashboard_routes.py      # 看板路由
│   │   ├── integration_routes.py    # 集成路由
│   │   └── base_data_routes.py      # 基础数据路由
│   ├── services/                    # 业务服务
│   └── instance/
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── assets/
│   │   └── utils/
│   ├── ecosystem.config.cjs         # PM2 配置
│   └── dist/
└── package.json
```

---

## API 路由清单

### 工单 API (/api/work-orders)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/work-orders` | 获取工单列表 |
| GET | `/api/work-orders/<id>` | 获取工单详情 |
| POST | `/api/work-orders` | 创建工单 |
| PUT | `/api/work-orders/<id>` | 更新工单 |
| PUT | `/api/work-orders/<id>/status` | 更新工单状态 |
| DELETE | `/api/work-orders/<id>` | 删除工单 |

### 生产 API (/api/production)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/production/records` | 获取生产记录 |
| POST | `/api/production/report` | 生产报工 |
| GET | `/api/production/progress/<work_order_id>` | 获取生产进度 |

### 看板 API (/api/dashboard)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/dashboard/summary` | 获取生产概况 |
| GET | `/api/dashboard/machine-status` | 获取设备状态 |
| GET | `/api/dashboard/production-trend` | 获取生产趋势 |

### 集成 API (/api/integration)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/integration/products` | 获取产品列表 |
| GET | `/api/integration/machines` | 获取设备列表 |
| POST | `/api/integration/material-request` | 物料领用请求 |

---

## 计划数据模型

### WorkOrder 工单

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| wo_number | String | 工单号 |
| product_id | Integer | 产品 ID |
| product_name | String | 产品名称 |
| planned_qty | Integer | 计划数量 |
| completed_qty | Integer | 完成数量 |
| start_date | Date | 开始日期 |
| due_date | Date | 截止日期 |
| status | String | 状态 |
| priority | String | 优先级 |

### ProductionRecord 生产记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| work_order_id | Integer | 工单 ID |
| machine_id | Integer | 设备 ID |
| operator_id | Integer | 操作员 ID |
| process_name | String | 工序名称 |
| quantity | Integer | 数量 |
| good_qty | Integer | 良品数 |
| defect_qty | Integer | 不良数 |
| start_time | DateTime | 开始时间 |
| end_time | DateTime | 结束时间 |

### QualityInspection 质量检验

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| work_order_id | Integer | 工单 ID |
| inspector_id | Integer | 检验员 ID |
| inspection_type | String | 检验类型 |
| result | String | 检验结果 |
| defect_details | JSON | 缺陷详情 |

---

## 本地开发

```bash
# 启动后端
cd MES/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py

# 启动前端
cd MES/frontend
npm install
npm run dev
```

---

## 开发状态

- [x] 基础框架搭建
- [x] 工单管理 API
- [x] 生产报工 API
- [x] 看板 API
- [x] 集成 API
- [ ] 前端界面
- [ ] 质量管理
- [ ] 实时数据采集

---

## 与其他系统的集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| SCM | API 调用 | 物料领用 |
| EAM | API 调用 | 查询设备状态 |
| HR | API 调用 | 获取操作员信息 |
| 报价 | API 调用 | 获取产品/工艺信息 |

---

## 注意事项

1. **未部署**: MES 系统尚未部署到生产环境
2. **端口**: 计划使用 8007 端口
3. **数据库**: 开发使用 SQLite (mes_system.db)
4. **前端最简**: 前端仅有基础 React，无 UI 框架
5. **后端相对完整**: 后端 API 框架已搭建
