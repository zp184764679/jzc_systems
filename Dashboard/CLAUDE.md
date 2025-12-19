# Dashboard 可视化追踪系统 - Claude Code 项目上下文

## 系统概述

Dashboard 是 JZC 企业管理系统的可视化追踪模块，为精密加工行业提供订单追踪和生产流程可视化功能。

### 核心功能
- 时间轴视图（多维度切换：按客户/订单/工序/部门）
- 仪表盘（KPI 指标、订单状态分布、交付趋势分析）
- 待办事项管理（任务管理、截止日期提醒、优先级标记）
- 客户门户（客户可通过临时链接查看订单进度）
- **报表中心**（生产/订单/任务/KPI报表，支持Excel/PDF/CSV导出）

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 8100 |
| 前端端口(dev) | 6100 |
| 前端路径 | `/dashboard/` |
| API路径 | `/dashboard/api/` |
| PM2服务名 | dashboard-backend |
| 数据库 | cncplan |
| 健康检查 | `curl http://127.0.0.1:8100/health` |
| 部署状态 | 未部署 |

---

## 技术栈

### 前端
- React 18 + Vite
- Ant Design
- ECharts
- react-calendar-timeline

### 后端
- Flask 3.0
- SQLAlchemy 2.0
- PyMySQL
- openpyxl (Excel导出)
- reportlab (PDF导出)

---

## 目录结构

```
Dashboard/
├── backend/
│   ├── main.py                    # Flask 入口
│   ├── requirements.txt           # Python 依赖
│   ├── .env                       # 环境配置
│   ├── reports/                   # 生成的报表文件目录
│   ├── app/
│   │   ├── __init__.py           # Flask 应用工厂
│   │   ├── models/               # 数据模型
│   │   │   ├── production_plan.py
│   │   │   ├── task.py
│   │   │   ├── customer_token.py
│   │   │   └── report.py         # 报表记录模型
│   │   ├── routes/               # API 路由
│   │   │   ├── timeline.py
│   │   │   ├── dashboard.py
│   │   │   ├── tasks.py
│   │   │   ├── customer_portal.py
│   │   │   └── reports.py        # 报表 API
│   │   └── services/             # 业务服务
│   │       ├── data_aggregator.py
│   │       ├── report_generator.py  # 报表生成服务
│   │       └── export_service.py    # 导出服务(Excel/PDF/CSV)
│   └── migrations/               # 数据库迁移
│       └── create_tables.sql
└── frontend/
    ├── src/
    │   ├── main.jsx              # React 入口
    │   ├── App.jsx               # 主应用
    │   ├── components/           # 组件
    │   │   └── Layout/
    │   │       └── MainLayout.jsx
    │   ├── pages/                # 页面
    │   │   ├── Dashboard/
    │   │   ├── Tasks/
    │   │   └── Reports/          # 报表中心页面
    │   └── services/             # API 服务
    │       └── api.js
    ├── vite.config.js
    └── package.json
```

---

## API 路由清单

### 时间轴 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/timeline/data` | 获取时间轴数据 |
| GET | `/api/timeline/item/:type/:id` | 获取项目详情 |
| GET | `/api/timeline/stats` | 获取统计数据 |

### 仪表盘 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/dashboard/kpi/summary` | KPI 汇总 |
| GET | `/api/dashboard/charts/order-status` | 订单状态分布 |
| GET | `/api/dashboard/charts/delivery-trend` | 交付趋势 |

### 待办事项 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tasks` | 获取任务列表 |
| POST | `/api/tasks` | 创建任务 |
| PUT | `/api/tasks/:id` | 更新任务 |
| DELETE | `/api/tasks/:id` | 删除任务 |

### 客户门户 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/customer-portal/generate-link` | 生成访问链接 |
| GET | `/api/customer-portal/orders` | 获取客户订单 |
| GET | `/api/customer-portal/orders/:id` | 获取订单详情 |

### 报表中心 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/reports` | 获取报表历史列表 |
| GET | `/api/reports/:id` | 获取报表详情 |
| GET | `/api/reports/templates` | 获取报表模板 |
| GET | `/api/reports/statistics` | 获取报表统计 |
| GET | `/api/reports/enums` | 获取枚举值 |
| POST | `/api/reports/preview` | 预览报表数据 |
| POST | `/api/reports/generate` | 生成报表 |
| GET | `/api/reports/:id/download` | 下载报表文件 |
| DELETE | `/api/reports/:id` | 删除报表 |

---

## 数据模型

### ProductionPlan 生产计划

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_no | String | 订单号 |
| customer_name | String | 客户名称 |
| product_name | String | 产品名称 |
| start_date | Date | 开始日期 |
| end_date | Date | 结束日期 |
| status | String | 状态 |

### Task 待办任务

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| title | String | 任务标题 |
| description | Text | 任务描述 |
| due_date | DateTime | 截止日期 |
| priority | String | 优先级 |
| status | String | 状态 |
| assignee_id | Integer | 负责人 |

### CustomerToken 客户访问令牌

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| token | String | 访问令牌 |
| customer_id | Integer | 客户 ID |
| expires_at | DateTime | 过期时间 |
| order_ids | String | 可访问订单 ID |

### Report 报表记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| report_no | String | 报表编号 (RPT-YYYYMMDD-XXX) |
| report_type | String | 报表类型 (production/order/task/kpi) |
| report_name | String | 报表名称 |
| date_range_start | Date | 数据范围开始 |
| date_range_end | Date | 数据范围结束 |
| filters | JSON | 筛选条件 |
| data_snapshot | JSON | 数据快照 |
| file_path | String | 文件路径 |
| file_format | String | 文件格式 (excel/pdf/csv) |
| file_size | Integer | 文件大小(字节) |
| status | String | 状态 (pending/generating/completed/failed) |
| created_by | Integer | 创建人ID |
| created_by_name | String | 创建人姓名 |
| created_at | DateTime | 创建时间 |
| completed_at | DateTime | 完成时间 |

---

## 前端页面/组件

### 页面列表

| 页面 | 路径 | 说明 |
|------|------|------|
| 仪表盘 | `/dashboard/` | KPI 指标、订单状态分布、交付趋势图表 |
| 时间轴 | `/dashboard/timeline` | 生产进度可视化，支持按客户/订单/工序/部门切换 |
| 待办事项 | `/dashboard/tasks` | 任务管理，支持优先级、截止日期、状态筛选 |
| 客户门户 | `/dashboard/portal` | 生成客户访问链接，管理客户可见订单 |
| 报表中心 | `/dashboard/reports` | 报表生成、下载、历史记录管理 |

### 核心组件

| 组件 | 位置 | 说明 |
|------|------|------|
| MainLayout | `components/Layout/MainLayout.jsx` | 主布局（Header + Sider + Content） |
| TimelineChart | `components/Timeline/TimelineChart.jsx` | 时间轴图表组件 |
| KPICard | `components/Dashboard/KPICard.jsx` | KPI 指标卡片 |
| TaskCard | `components/Tasks/TaskCard.jsx` | 任务卡片组件 |
| ReportGenerator | `components/Reports/ReportGenerator.jsx` | 报表生成表单 |

---

## 配置文件

### 后端环境变量 (.env)
```bash
SQLALCHEMY_DATABASE_URI=mysql+pymysql://app:app@localhost/cncplan?charset=utf8mb4
FLASK_DEBUG=false
```

---

## 本地开发

```bash
# 启动后端
cd Dashboard/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
# 后端运行在 http://localhost:8100

# 启动前端
cd Dashboard/frontend
npm install
npm run dev
# 前端运行在 http://localhost:6100
```

---

## 已完成功能

- [x] 仪表盘 KPI 指标展示
- [x] 订单状态分布图表
- [x] 交付趋势分析图表
- [x] 时间轴多维度视图（客户/订单/工序/部门）
- [x] 待办事项 CRUD 操作
- [x] 任务优先级和截止日期管理
- [x] 客户门户临时链接生成
- [x] 报表中心 - 生产报表
- [x] 报表中心 - 订单报表
- [x] 报表中心 - 任务报表
- [x] 报表中心 - KPI 报表
- [x] 报表导出（Excel/PDF/CSV）
- [ ] 实时数据刷新
- [ ] 移动端适配
- [ ] 邮件通知集成

---

## 与其他系统的集成

| 调用方 | 被调用方 | 集成内容 | 状态 |
|--------|----------|----------|------|
| Dashboard | Portal | SSO 认证、用户信息 | 待实现 |
| Dashboard | 报价 | 订单数据、生产计划 | 待实现 |
| Dashboard | MES | 生产进度、工序状态 | 待实现 |
| Dashboard | HR | 员工信息、部门数据 | 待实现 |

---

## 注意事项

1. **数据库**: 使用共享的 `cncplan` 数据库
2. **客户门户**: 支持生成临时访问链接，有过期时间
3. **时间轴**: 支持多维度数据聚合展示
4. **部署状态**: 尚未部署到生产环境
5. **报表存储**: 生成的报表文件保存在 `backend/reports/` 目录
