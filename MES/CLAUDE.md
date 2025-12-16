# MES 制造执行系统 - Claude Code 项目上下文

## 系统概述

MES (Manufacturing Execution System) 是 JZC 企业管理系统的制造执行模块，负责生产计划执行、工单管理、工序管理、生产数据采集和质量管理。

**部署状态**: 未部署（开发完成度 90%）

### 核心功能
- 工单管理
- **工序管理**
  - 工序定义管理
  - 工艺路线管理
  - 工单工序跟踪
- 生产报工
- 生产看板
- **质量管理**
  - 检验标准管理
  - 质量检验单
  - 缺陷类型管理
  - 不合格品报告 (NCR)
- **生产排程**
  - 排程计划管理
  - 排程任务管理
  - 自动排程算法
  - 设备产能配置
  - 甘特图数据
- **物料追溯**
  - 物料批次管理
  - 产品批次管理
  - 物料消耗记录
  - 正向追溯（物料→产品）
  - 反向追溯（产品→物料）
  - 追溯统计分析
- **工时统计**（新）
  - 工时汇总统计
  - 按操作员统计
  - 按工序类型统计
  - 工时趋势分析
  - 按工单统计
  - 按设备统计
  - 加班统计
  - 效率排名

### 计划功能
- 生产数据采集
- 设备状态监控

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 8007 |
| 前端端口(dev) | 7800 |
| 前端路径 | `/mes/` |
| API路径 | `/mes/api/` |
| PM2服务名 | mes-backend |
| 数据库 | cncplan |
| 健康检查 | `curl http://127.0.0.1:8007/health` |

---

## 技术栈

### 前端
- React 19.2.0
- Vite
- 纯 CSS（无 Ant Design）
- Axios

### 后端
- Flask + Flask-CORS
- Flask-SQLAlchemy
- SQLAlchemy 2.0+
- PyMySQL

---

## 目录结构

```
MES/
├── backend/
│   ├── main.py                      # Flask 应用入口
│   ├── database.py                  # 数据库配置
│   ├── requirements.txt             # Python 依赖
│   ├── models/
│   │   ├── __init__.py              # 模型导出
│   │   ├── work_order.py            # 工单模型
│   │   ├── production_record.py     # 生产记录模型
│   │   ├── quality_inspection.py    # 质检模型（旧）
│   │   ├── base_data.py             # 基础数据（产线、工作中心）
│   │   ├── process.py               # 工序管理模型
│   │   ├── quality.py               # 质量管理模型
│   │   ├── schedule.py              # 生产排程模型
│   │   └── traceability.py          # 物料追溯模型（新）
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── work_order_routes.py     # 工单路由
│   │   ├── production_routes.py     # 生产路由
│   │   ├── dashboard_routes.py      # 看板路由
│   │   ├── integration_routes.py    # 集成路由
│   │   ├── base_data_routes.py      # 基础数据路由
│   │   ├── process_routes.py        # 工序管理路由
│   │   ├── quality_routes.py        # 质量管理路由
│   │   ├── schedule_routes.py       # 生产排程路由
│   │   ├── traceability_routes.py   # 物料追溯路由
│   │   └── labor_time_routes.py     # 工时统计路由（新）
│   ├── services/                    # 业务服务
│   │   ├── hr_service.py
│   │   ├── eam_service.py
│   │   ├── pdm_service.py
│   │   └── scm_service.py
│   └── instance/
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx                  # 主应用（含工序管理、质量管理页面）
│   │   ├── App.css                  # 样式
│   │   ├── services/
│   │   │   └── api.js               # API 调用封装
│   │   └── utils/
│   │       ├── ssoAuth.js           # SSO 认证
│   │       └── authEvents.js        # 认证事件
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

### 工序定义 API (/api/process/definitions) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/process/definitions` | 获取工序定义列表 |
| GET | `/api/process/definitions/<id>` | 获取工序定义详情 |
| POST | `/api/process/definitions` | 创建工序定义 |
| PUT | `/api/process/definitions/<id>` | 更新工序定义 |
| DELETE | `/api/process/definitions/<id>` | 删除工序定义 |
| GET | `/api/process/definitions/options` | 获取工序选项（下拉） |

### 工艺路线 API (/api/process/routes) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/process/routes` | 获取工艺路线列表 |
| GET | `/api/process/routes/<id>` | 获取工艺路线详情（含步骤） |
| POST | `/api/process/routes` | 创建工艺路线（含步骤） |
| PUT | `/api/process/routes/<id>` | 更新工艺路线 |
| DELETE | `/api/process/routes/<id>` | 删除工艺路线（仅草稿） |
| POST | `/api/process/routes/<id>/activate` | 激活工艺路线 |
| POST | `/api/process/routes/<id>/obsolete` | 废弃工艺路线 |
| POST | `/api/process/routes/<id>/copy` | 复制工艺路线 |
| GET | `/api/process/routes/options` | 获取路线选项 |

### 工单工序 API (/api/process/work-order) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/process/work-order/<id>/processes` | 获取工单工序列表 |
| POST | `/api/process/work-order/<id>/generate-processes` | 根据路线生成工序 |
| POST | `/api/process/work-order-process/<id>/start` | 开始执行工序 |
| POST | `/api/process/work-order-process/<id>/complete` | 完成工序 |
| POST | `/api/process/work-order-process/<id>/pause` | 暂停工序 |
| POST | `/api/process/work-order-process/<id>/skip` | 跳过工序 |
| POST | `/api/process/work-order-process/<id>/assign` | 派工 |

### 统计 API (/api/process/statistics)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/process/statistics/process-types` | 工序类型统计 |
| GET | `/api/process/statistics/route-status` | 路线状态统计 |
| GET | `/api/process/statistics/work-order-progress/<id>` | 工单进度统计 |

### 检验标准 API (/api/quality/standards) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/quality/standards` | 获取检验标准列表 |
| GET | `/api/quality/standards/<id>` | 获取检验标准详情 |
| POST | `/api/quality/standards` | 创建检验标准 |
| PUT | `/api/quality/standards/<id>` | 更新检验标准 |
| DELETE | `/api/quality/standards/<id>` | 删除检验标准 |
| GET | `/api/quality/standards/options` | 获取标准选项（下拉） |

### 缺陷类型 API (/api/quality/defect-types) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/quality/defect-types` | 获取缺陷类型列表 |
| POST | `/api/quality/defect-types` | 创建缺陷类型 |
| PUT | `/api/quality/defect-types/<id>` | 更新缺陷类型 |
| DELETE | `/api/quality/defect-types/<id>` | 删除缺陷类型 |
| GET | `/api/quality/defect-types/categories` | 获取缺陷分类 |

### 质量检验单 API (/api/quality/inspections) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/quality/inspections` | 获取检验单列表 |
| GET | `/api/quality/inspections/<id>` | 获取检验单详情（含缺陷） |
| POST | `/api/quality/inspections` | 创建检验单 |
| POST | `/api/quality/inspections/<id>/start` | 开始检验 |
| POST | `/api/quality/inspections/<id>/complete` | 完成检验 |
| POST | `/api/quality/inspections/<id>/review` | 复核检验 |
| POST | `/api/quality/inspections/<id>/dispose` | 处置检验结果 |
| POST | `/api/quality/inspections/<id>/defects` | 添加缺陷记录 |
| DELETE | `/api/quality/inspections/<id>/defects/<defect_id>` | 删除缺陷记录 |

### 不合格品报告 API (/api/quality/ncr) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/quality/ncr` | 获取 NCR 列表 |
| GET | `/api/quality/ncr/<id>` | 获取 NCR 详情 |
| POST | `/api/quality/ncr` | 创建 NCR |
| PUT | `/api/quality/ncr/<id>` | 更新 NCR |
| POST | `/api/quality/ncr/<id>/review` | 审核 NCR |
| POST | `/api/quality/ncr/<id>/dispose` | 处置 NCR |
| POST | `/api/quality/ncr/<id>/close` | 关闭 NCR |

### 质量统计 API (/api/quality/statistics) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/quality/statistics/summary` | 质量统计概览 |
| GET | `/api/quality/statistics/by-stage` | 按检验阶段统计 |
| GET | `/api/quality/statistics/defect-analysis` | 缺陷分析统计 |

### 质量枚举 API (/api/quality/enums) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/quality/enums` | 获取质量管理枚举值 |

### 排程计划 API (/api/schedule/schedules) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/schedule/schedules` | 获取排程列表 |
| GET | `/api/schedule/schedules/<id>` | 获取排程详情（含任务） |
| POST | `/api/schedule/schedules` | 创建排程 |
| PUT | `/api/schedule/schedules/<id>` | 更新排程 |
| DELETE | `/api/schedule/schedules/<id>` | 删除排程（仅草稿/取消） |
| POST | `/api/schedule/schedules/<id>/confirm` | 确认排程 |
| POST | `/api/schedule/schedules/<id>/start` | 开始执行排程 |
| POST | `/api/schedule/schedules/<id>/complete` | 完成排程 |
| POST | `/api/schedule/schedules/<id>/cancel` | 取消排程 |
| POST | `/api/schedule/schedules/<id>/auto-schedule` | 自动排程 |
| GET | `/api/schedule/schedules/<id>/gantt` | 获取甘特图数据 |

### 排程任务 API (/api/schedule/tasks) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/schedule/schedules/<id>/tasks` | 获取排程任务列表 |
| POST | `/api/schedule/schedules/<id>/tasks` | 添加排程任务 |
| PUT | `/api/schedule/tasks/<id>` | 更新任务 |
| DELETE | `/api/schedule/tasks/<id>` | 删除任务 |
| POST | `/api/schedule/tasks/<id>/start` | 开始执行任务 |
| POST | `/api/schedule/tasks/<id>/complete` | 完成任务 |

### 设备产能 API (/api/schedule/machine-capacities) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/schedule/machine-capacities` | 获取设备产能列表 |
| POST | `/api/schedule/machine-capacities` | 创建/更新设备产能 |
| POST | `/api/schedule/machine-capacities/batch` | 批量创建设备产能 |

### 排程统计 API (/api/schedule/statistics) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/schedule/statistics/summary` | 排程统计概览 |
| GET | `/api/schedule/statistics/machine-utilization` | 设备利用率统计 |

### 排程枚举 API (/api/schedule/enums)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/schedule/enums` | 获取排程相关枚举值 |

### 物料批次 API (/api/traceability/material-lots) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/traceability/material-lots` | 获取物料批次列表 |
| GET | `/api/traceability/material-lots/<id>` | 获取物料批次详情 |
| POST | `/api/traceability/material-lots` | 创建物料批次 |
| PUT | `/api/traceability/material-lots/<id>` | 更新物料批次 |
| DELETE | `/api/traceability/material-lots/<id>` | 删除物料批次 |

### 产品批次 API (/api/traceability/product-lots) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/traceability/product-lots` | 获取产品批次列表 |
| GET | `/api/traceability/product-lots/<id>` | 获取产品批次详情 |
| POST | `/api/traceability/product-lots` | 创建产品批次 |
| PUT | `/api/traceability/product-lots/<id>` | 更新产品批次 |
| POST | `/api/traceability/product-lots/<id>/complete` | 完成产品批次 |

### 物料消耗 API (/api/traceability/consumptions) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/traceability/consumptions` | 获取物料消耗记录 |
| POST | `/api/traceability/consumptions` | 记录物料消耗 |

### 追溯查询 API (/api/traceability/trace) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/traceability/trace/forward/<material_lot_id>` | 正向追溯：物料→产品 |
| GET | `/api/traceability/trace/backward/<product_lot_id>` | 反向追溯：产品→物料 |
| GET | `/api/traceability/trace/by-work-order/<work_order_id>` | 按工单追溯 |

### 追溯统计 API (/api/traceability/statistics) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/traceability/statistics/summary` | 追溯统计概览 |
| GET | `/api/traceability/statistics/by-material` | 按物料统计消耗 |

### 追溯枚举 API (/api/traceability/enums) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/traceability/enums` | 获取追溯相关枚举值 |

### 工时统计 API (/api/labor-time) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/labor-time/summary` | 获取工时汇总统计 |
| GET | `/api/labor-time/by-operator` | 按操作员统计工时 |
| GET | `/api/labor-time/by-process-type` | 按工序类型统计工时 |
| GET | `/api/labor-time/trend` | 获取工时趋势（按日/周/月） |
| GET | `/api/labor-time/by-work-order` | 按工单统计工时 |
| GET | `/api/labor-time/by-equipment` | 按设备统计工时 |
| GET | `/api/labor-time/overtime` | 获取加班统计 |
| GET | `/api/labor-time/efficiency-ranking` | 获取效率排名 |

---

## 数据模型

### WorkOrder 工单

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_no | String | 工单编号 |
| product_id | Integer | 产品 ID |
| product_code | String | 产品编码 |
| product_name | String | 产品名称 |
| planned_quantity | Integer | 计划数量 |
| completed_quantity | Integer | 完成数量 |
| defect_quantity | Integer | 不良数量 |
| planned_start/end | DateTime | 计划开始/结束 |
| actual_start/end | DateTime | 实际开始/结束 |
| status | String | 状态 |
| priority | Integer | 优先级 |
| process_route_id | Integer | 工艺路线ID |
| current_step | Integer | 当前工序步骤 |

### ProcessDefinition 工序定义 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String | 工序编码（唯一） |
| name | String | 工序名称 |
| process_type | String | 工序类型 |
| work_center_id | Integer | 默认工作中心 |
| default_machine_id | Integer | 默认设备ID |
| setup_time | Float | 准备时间（分钟） |
| standard_time | Float | 标准工时（分钟/件） |
| move_time | Float | 移动时间（分钟） |
| min_batch_size | Integer | 最小批量 |
| inspection_required | Boolean | 是否需要检验 |
| quality_standards | JSON | 质量标准 |
| required_tools | JSON | 所需工具 |
| safety_notes | Text | 安全注意事项 |
| is_active | Boolean | 是否启用 |

### ProcessRoute 工艺路线 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| route_code | String | 路线编码（唯一） |
| name | String | 路线名称 |
| product_id | Integer | 产品ID |
| product_code | String | 产品编码 |
| product_name | String | 产品名称 |
| version | String | 版本号 |
| is_default | Boolean | 是否默认路线 |
| total_steps | Integer | 总工序数 |
| total_standard_time | Float | 总标准工时 |
| status | String | 状态(draft/active/obsolete) |
| is_active | Boolean | 是否启用 |

### ProcessRouteStep 工艺路线步骤 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| route_id | Integer | 工艺路线ID |
| process_id | Integer | 工序定义ID |
| step_no | Integer | 步骤序号 |
| step_name | String | 步骤名称（可覆盖） |
| work_center_id | Integer | 工作中心 |
| machine_id | Integer | 指定设备 |
| setup_time | Float | 准备时间（可覆盖） |
| standard_time | Float | 标准工时（可覆盖） |
| inspection_required | Boolean | 需要检验 |
| is_optional | Boolean | 是否可选 |
| is_parallel | Boolean | 是否可并行 |

### WorkOrderProcess 工单工序

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| work_order_id | Integer | 工单ID |
| route_step_id | Integer | 路线步骤ID |
| process_id | Integer | 工序定义ID |
| step_no | Integer | 步骤序号 |
| process_name | String | 工序名称 |
| planned_quantity | Integer | 计划数量 |
| completed_quantity | Integer | 完成数量 |
| defect_quantity | Integer | 不良数量 |
| operator_id | Integer | 操作员ID |
| operator_name | String | 操作员姓名 |
| machine_id | Integer | 设备ID |
| status | String | 状态 |
| is_current | Boolean | 是否当前工序 |
| actual_start/end | DateTime | 实际开始/结束 |
| actual_hours | Float | 实际工时 |

### InspectionStandard 检验标准 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String | 标准编码（唯一） |
| name | String | 标准名称 |
| product_id/code/name | | 适用产品 |
| process_id/name | | 适用工序 |
| inspection_stage | String | 检验阶段(incoming/process/final/outgoing) |
| inspection_method | String | 检验方式(full/sampling/skip) |
| sample_plan | String | 抽样方案(如 AQL) |
| inspection_items | JSON | 检验项目列表 |
| aql_critical/major/minor | Float | AQL 标准 |
| version | String | 版本号 |
| is_active | Boolean | 是否启用 |

### DefectType 缺陷类型 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String | 缺陷编码（唯一） |
| name | String | 缺陷名称 |
| category | String | 缺陷分类 |
| severity | String | 严重程度(critical/major/minor) |
| description | Text | 缺陷描述 |
| cause_analysis | Text | 原因分析 |
| corrective_action | Text | 纠正措施 |
| is_active | Boolean | 是否启用 |

### QualityInspectionOrder 质量检验单 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| inspection_no | String | 检验单号（唯一） |
| work_order_id | Integer | 关联工单ID |
| standard_id | Integer | 检验标准ID |
| inspection_stage | String | 检验阶段 |
| inspection_method | String | 检验方式 |
| product_code/name | String | 产品信息 |
| process_name | String | 工序名称 |
| batch_no | String | 批次号 |
| lot_size | Integer | 批量大小 |
| sample_size | Integer | 抽样数量 |
| pass_quantity | Integer | 合格数量 |
| fail_quantity | Integer | 不合格数量 |
| result | String | 结果(pending/pass/fail/conditional) |
| pass_rate | Float | 合格率 |
| item_results | JSON | 检验项结果 |
| inspector_id/name | | 检验员 |
| disposition | String | 处置方式 |
| status | String | 状态(pending/inspecting/completed/closed) |

### DefectRecord 缺陷记录 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| inspection_order_id | Integer | 检验单ID |
| defect_type_id | Integer | 缺陷类型ID |
| defect_code/name | String | 缺陷信息 |
| severity | String | 严重程度 |
| quantity | Integer | 缺陷数量 |
| inspection_item | String | 检验项 |
| specification | String | 规格要求 |
| actual_value | String | 实测值 |
| description | Text | 缺陷描述 |
| location | String | 缺陷位置 |
| images | JSON | 缺陷图片URL |

### NonConformanceReport 不合格品报告(NCR) - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| ncr_no | String | NCR编号（唯一） |
| inspection_order_id | Integer | 关联检验单ID |
| work_order_id | Integer | 关联工单ID |
| product_code/name | String | 产品信息 |
| batch_no | String | 批次号 |
| quantity | Integer | 不合格数量 |
| nc_type | String | 不合格类型 |
| nc_description | Text | 不合格描述 |
| severity | String | 严重程度 |
| root_cause | Text | 根本原因 |
| disposition | String | 处置方式 |
| corrective_action | Text | 纠正措施 |
| preventive_action | Text | 预防措施 |
| status | String | 状态(open/reviewing/dispositioned/closed) |
| reporter_id/name | | 发起人 |

### ProductionSchedule 生产排程 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| schedule_code | String | 排程编号（唯一） |
| name | String | 排程名称 |
| plan_start_date | Date | 计划开始日期 |
| plan_end_date | Date | 计划结束日期 |
| actual_start_date | Date | 实际开始日期 |
| actual_end_date | Date | 实际结束日期 |
| status | String | 状态 |
| priority | Integer | 优先级(1-5) |
| total_tasks | Integer | 任务总数 |
| completed_tasks | Integer | 完成任务数 |
| total_hours | Float | 总工时 |
| scheduled_hours | Float | 已排工时 |
| description | Text | 排程说明 |
| created_by | Integer | 创建人ID |
| confirmed_by | Integer | 确认人ID |
| confirmed_at | DateTime | 确认时间 |

### ScheduleTask 排程任务 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| schedule_id | Integer | 排程ID |
| work_order_id | Integer | 工单ID |
| work_order_no | String | 工单编号 |
| process_id | Integer | 工序ID |
| process_name | String | 工序名称 |
| machine_id | Integer | 设备ID |
| machine_name | String | 设备名称 |
| operator_id | Integer | 操作员ID |
| operator_name | String | 操作员姓名 |
| planned_start | DateTime | 计划开始时间 |
| planned_end | DateTime | 计划结束时间 |
| actual_start | DateTime | 实际开始时间 |
| actual_end | DateTime | 实际结束时间 |
| planned_quantity | Integer | 计划数量 |
| completed_quantity | Integer | 完成数量 |
| status | String | 状态 |
| priority | Integer | 优先级(1-5) |
| sequence | Integer | 执行顺序 |
| setup_time | Float | 准备时间(分钟) |
| process_time | Float | 加工时间(分钟) |
| remarks | Text | 备注 |

### MachineCapacity 设备产能 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| machine_id | Integer | 设备ID |
| machine_name | String | 设备名称 |
| capacity_date | Date | 产能日期 |
| shift | String | 班次(day/night/full) |
| available_hours | Float | 可用工时 |
| scheduled_hours | Float | 已排工时 |
| utilization_rate | Float | 利用率 |
| max_capacity | Float | 最大产能(件/小时) |
| remarks | Text | 备注 |

---

## 工序状态流转

```
┌─────────┐   开始执行   ┌───────────┐   完成    ┌──────────┐
│  待开始  │ ──────────► │  进行中   │ ───────► │  已完成  │
│(pending) │             │(in_progress)│          │(completed)│
└────┬────┘             └─────┬──────┘          └──────────┘
     │                        │
     │ 等待/跳过              │ 暂停
     ▼                        ▼
┌──────────┐            ┌──────────┐
│ 等待中    │            │  暂停    │ ─► 继续执行
│(waiting) │            │ (paused) │
└─────┬────┘            └──────────┘
      │ 跳过
      ▼
┌──────────┐
│  已跳过   │
│ (skipped)│
└──────────┘
```

---

## 工艺路线状态流转

```
┌─────────┐   激活    ┌──────────┐   废弃    ┌──────────┐
│  草稿   │ ───────► │  生效    │ ───────► │  废弃    │
│ (draft) │          │ (active) │          │(obsolete)│
└────┬────┘          └──────────┘          └──────────┘
     │
     │ 删除（可删除）
     ▼
   [删除]
```

---

## 质量检验单状态流转

```
┌─────────┐   开始检验   ┌───────────┐   完成检验   ┌──────────┐   关闭   ┌─────────┐
│  待检验  │ ──────────► │  检验中   │ ──────────► │  已完成  │ ──────► │  已关闭  │
│(pending) │             │(inspecting)│             │(completed)│         │ (closed) │
└─────────┘             └───────────┘             └────┬─────┘         └─────────┘
                                                       │
                                                       │ 需要复核
                                                       ▼
                                                 ┌──────────┐   复核通过
                                                 │  复核中   │ ──────────► 已完成
                                                 │(reviewing)│
                                                 └──────────┘
```

### 检验结果类型

| 结果 | 说明 | 处理 |
|------|------|------|
| pass | 合格 | 正常入库/放行 |
| fail | 不合格 | 创建 NCR |
| conditional | 条件接受 | 记录让步条件 |

### 处置方式

| 处置 | 英文 | 说明 |
|------|------|------|
| 接受 | accept | 检验合格，接受 |
| 拒收 | reject | 不合格，拒收 |
| 返工 | rework | 返回重新加工 |
| 返修 | repair | 修复后可接受 |
| 报废 | scrap | 无法使用，报废 |
| 让步 | concession | 让步接收 |
| 降级 | downgrade | 降级使用 |

---

## NCR 状态流转

```
┌─────────┐   提交审核   ┌───────────┐   审核通过   ┌──────────┐   关闭    ┌─────────┐
│  开启   │ ──────────► │  审核中   │ ──────────► │  已处置  │ ──────► │  已关闭  │
│ (open)  │             │(reviewing) │             │(dispositioned)│       │ (closed) │
└─────────┘             └─────┬─────┘             └──────────┘         └─────────┘
                              │
                              │ 审核拒绝
                              ▼
                        ┌──────────┐
                        │ 退回修改 │ ──► 开启
                        └──────────┘
```

---

## 排程状态流转 - 新

```
┌─────────┐   确认排程   ┌───────────┐   开始执行   ┌──────────┐   完成    ┌─────────┐
│  草稿   │ ──────────► │  已确认   │ ──────────► │  执行中  │ ──────► │  已完成  │
│ (draft) │             │(confirmed) │             │(in_progress)│        │(completed)│
└────┬────┘             └───────────┘             └──────────┘         └─────────┘
     │                        │
     │ 取消                   │ 取消
     ▼                        ▼
┌─────────┐              ┌─────────┐
│  已取消  │              │  已取消  │
│(cancelled)│            │(cancelled)│
└─────────┘              └─────────┘
```

### 排程状态说明

| 状态 | 英文 | 说明 | 允许操作 |
|------|------|------|----------|
| 草稿 | draft | 初始状态，可编辑 | 编辑、删除、确认 |
| 已确认 | confirmed | 排程已审核确认 | 开始、取消 |
| 执行中 | in_progress | 正在执行 | 完成 |
| 已完成 | completed | 全部完成 | - |
| 已取消 | cancelled | 已取消 | 删除 |

---

## 任务状态流转 - 新

```
┌─────────┐   开始执行   ┌───────────┐   完成任务   ┌──────────┐
│  待排程  │ ──────────► │  执行中   │ ──────────► │  已完成  │
│(pending) │             │(in_progress)│             │(completed)│
└─────────┘             └─────┬─────┘             └──────────┘
                              │
                              │ 暂停
                              ▼
                        ┌──────────┐
                        │  已暂停   │ ──► 继续执行
                        │ (paused) │
                        └──────────┘
```

### 任务状态说明

| 状态 | 英文 | 说明 |
|------|------|------|
| 待排程 | pending | 等待分配设备和人员 |
| 执行中 | in_progress | 正在执行 |
| 已暂停 | paused | 暂停中 |
| 已完成 | completed | 任务完成 |

---

## 前端页面

| 页面/Tab | 路径 | 说明 |
|----------|------|------|
| 生产看板 | /dashboard | 生产概览、统计 |
| 工单管理 | /workorders | 工单列表 |
| 生产报工 | /production | 生产报工表单 |
| **工序管理** | /process | **工序定义 + 工艺路线** |
| **质量管理** | /quality | **检验单、NCR、标准、缺陷** |
| **生产排程** | /schedule | **排程计划 + 任务管理** |
| **工时统计** | /labortime | **工时汇总、操作员、工序、趋势、加班、排名**（新） |

### 工序管理页面功能

1. **工序定义** Tab
   - 工序列表（编码、名称、类型、工时、状态）
   - 新建/编辑工序弹窗
   - 删除工序（无引用时）

2. **工艺路线** Tab
   - 路线列表（编码、名称、产品、版本、工序数、状态）
   - 新建/编辑路线弹窗（含工序步骤管理）
   - 激活/废弃/删除操作

### 质量管理页面功能（新）

1. **质量检验单** Tab
   - 检验单列表（单号、产品、批次、检验阶段、结果、状态）
   - 新建检验单弹窗
   - 开始检验/完成检验/复核/处置操作
   - 检验结果颜色标签（合格绿/不合格红/条件黄）

2. **不合格品报告 (NCR)** Tab
   - NCR 列表（单号、产品、数量、严重程度、状态）
   - 新建 NCR 弹窗
   - 审核/处置/关闭操作
   - 严重程度颜色标签（严重红/主要橙/轻微灰）

3. **检验标准** Tab
   - 标准列表（编码、名称、产品、检验阶段、方式、版本）
   - 新建/编辑标准弹窗
   - 删除标准

4. **缺陷类型** Tab
   - 缺陷列表（编码、名称、分类、严重程度）
   - 新建/编辑缺陷类型弹窗
   - 删除缺陷类型

### 生产排程页面功能（新）

1. **排程列表** Tab（默认视图）
   - 排程统计卡片（总数、草稿、执行中、已完成、今日任务）
   - 排程列表（编号、名称、日期范围、优先级、进度、状态）
   - 状态颜色标签（草稿灰/已确认蓝/执行中橙/已完成绿/已取消红）
   - 优先级星标展示
   - 进度条展示
   - 新建/编辑排程弹窗
   - 确认/开始/完成/取消操作按钮
   - 自动排程功能
   - 查看详情按钮

2. **排程详情** Tab（点击查看进入）
   - 排程基本信息展示
   - 任务列表表格（工单、工序、设备、操作员、时间、数量、状态）
   - 任务状态颜色标签
   - 开始任务/完成任务操作
   - 返回列表按钮

3. **排程表单弹窗**
   - 排程名称输入
   - 计划日期范围选择
   - 优先级选择（1-5）
   - 排程说明输入

### 工时统计页面功能（新）

1. **汇总统计** Tab
   - 总工时、标准工时、效率统计卡片
   - 操作员数、报工次数、工序次数统计
   - 环比增长率指示

2. **按操作员** Tab
   - 操作员工时列表（总工时、报工工时、工序工时、计划工时）
   - 效率和良率计算

3. **按工序类型** Tab
   - 工序类型工时分布
   - 实际工时 vs 计划工时

4. **工时趋势** Tab
   - 按日期统计工时趋势
   - 效率变化曲线

5. **按工单** Tab
   - 工单工时明细（分页）
   - 实际工时 vs 标准工时

6. **加班统计** Tab
   - 操作员加班工时列表
   - 正常工时、加班工时、加班天数

7. **效率排名** Tab
   - Top 10 效率排名
   - 支持按操作员/设备/工序类型排名

---

## 本地开发

```bash
# 启动后端
cd MES/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py

# 启动前端
cd MES/frontend
npm install
npm run dev
```

---

## 已完成功能

- [x] 基础框架搭建
- [x] 工单管理 API
- [x] 生产报工 API
- [x] 看板 API
- [x] 集成 API
- [x] **工序定义管理**（后端 + 前端）
- [x] **工艺路线管理**（后端 + 前端）
- [x] **工单工序跟踪 API**
- [x] 前端界面（生产看板、工单管理、生产报工、工序管理）
- [x] **质量管理系统**
  - [x] 检验标准管理（后端 + 前端）
  - [x] 缺陷类型管理（后端 + 前端）
  - [x] 质量检验单管理（后端 + 前端）
  - [x] 检验单状态流转（待检验→检验中→完成→关闭）
  - [x] 不合格品报告 (NCR)（后端 + 前端）
  - [x] NCR 状态流转（开启→审核→处置→关闭）
  - [x] 质量统计 API
  - [x] 质量枚举 API
- [x] **生产排程系统**（新）
  - [x] 排程计划管理（后端 + 前端）
  - [x] 排程任务管理（后端 + 前端）
  - [x] 排程状态流转（草稿→确认→执行→完成）
  - [x] 任务状态流转（待排程→执行中→完成）
  - [x] 自动排程算法（基于工单工序）
  - [x] 甘特图数据 API
  - [x] 设备产能配置
  - [x] 排程统计 API
  - [x] 排程枚举 API
- [x] **工时统计系统**（新）
  - [x] 工时汇总统计（后端 + 前端）
  - [x] 按操作员统计（后端 + 前端）
  - [x] 按工序类型统计（后端 + 前端）
  - [x] 工时趋势分析（后端 + 前端）
  - [x] 按工单统计（后端 + 前端）
  - [x] 按设备统计（后端）
  - [x] 加班统计（后端 + 前端）
  - [x] 效率排名（后端 + 前端）
- [x] **物料追溯系统**
  - [x] 物料批次管理（后端 + 前端）
  - [x] 产品批次管理（后端 + 前端）
  - [x] 物料消耗记录（后端 + 前端）
  - [x] 正向追溯（物料→产品）
  - [x] 反向追溯（产品→物料）
  - [x] 追溯统计分析（后端 + 前端）
- [ ] 实时数据采集

---

## 与其他系统的集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| Portal | JWT Token | 使用 Portal 签发的 Token |
| SCM | API 调用 | 物料领用 |
| EAM | API 调用 | 查询设备状态 |
| HR | API 调用 | 获取操作员信息 |
| 报价 | API 调用 | 获取产品/工艺信息 |

---

## 注意事项

1. **未部署**: MES 系统尚未部署到生产环境
2. **端口**: 后端 8007，前端 dev 7800
3. **数据库**: 开发使用 SQLite (mes_system.db)，生产需配置 MySQL
4. **健康检查**: `/health` 路径
5. **前端简洁**: 前端使用纯 CSS，无 UI 框架
6. **工序定义**: 删除前需确保无工艺路线引用
7. **工艺路线**: 只有草稿状态可编辑和删除
8. **工单工序**: 由工艺路线自动生成，支持状态流转
9. **排程计划**: 只有草稿或已取消状态可删除
10. **排程任务**: 关联排程后自动级联删除
11. **自动排程**: 基于未完成工单的工序生成任务

---

## 工序类型说明

| 类型 | 英文 | 说明 |
|------|------|------|
| 机加工 | machining | CNC、车床、铣床等 |
| 装配 | assembly | 组装工序 |
| 焊接 | welding | 焊接工序 |
| 喷涂 | painting | 喷漆、喷粉 |
| 测试 | testing | 功能测试 |
| 检验 | inspection | 质量检验 |
| 包装 | packaging | 包装工序 |
| 热处理 | heat_treatment | 淬火、回火等 |
| 表面处理 | surface_treatment | 电镀、氧化等 |
| 其他 | other | 其他工序 |
