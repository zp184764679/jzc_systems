# EAM 设备资产管理系统 - Claude Code 项目上下文

## 系统概述

EAM (Enterprise Asset Management) 是 JZC 企业管理系统的设备资产管理模块，负责设备台账、维护保养、点检管理、故障报修等功能。

**部署状态**: 未部署（开发完成度 85%）

### 核心功能
- 设备台账管理
- 设备分类/基础数据管理
- **维护保养标准管理**
- **维护保养计划管理**
- **维护保养工单管理**
- **故障报修管理**
- **设备点检管理**
- 维护日历与统计
- **备件管理（新）**
  - 备件分类管理
  - 备件库存管理
  - 出入库记录
  - 库存预警
- **设备产能配置（新）**
  - 产能配置管理（按设备/班次/产品）
  - 产能调整记录
  - 每日产能日志（实际产出记录）
  - 产能统计分析（稼动率/良品率/OEE）

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 8008 |
| 前端端口(dev) | 7200 |
| 前端路径 | `/eam/` |
| API路径 | `/eam/api/` |
| PM2服务名 | eam-backend |
| 数据库 | cncplan |
| 健康检查 | `curl http://127.0.0.1:8008/health` |

---

## 技术栈

### 前端
- React 19.2.0
- Vite
- Ant Design 5.28.1
- TanStack React Query
- dayjs

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
│   │   ├── models/
│   │   │   ├── __init__.py          # 模型导出
│   │   │   ├── machine.py           # 设备模型
│   │   │   ├── base_data.py         # 基础数据模型
│   │   │   ├── maintenance.py       # 维护保养模型
│   │   │   └── spare_parts.py       # 备件管理模型（新）
│   │   ├── routes/
│   │   │   ├── __init__.py          # 路由导出
│   │   │   ├── machines.py          # 设备 API
│   │   │   ├── base_data.py         # 基础数据 API
│   │   │   ├── integration.py       # 集成 API
│   │   │   ├── maintenance.py       # 维护保养 API
│   │   │   └── spare_parts.py       # 备件管理 API（新）
│   │   └── services/
│   │       └── hr_service.py        # HR 集成服务
│   └── eam.db                       # SQLite 数据库（开发）
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── machines/
│   │   │   │   └── MachineList.jsx  # 设备台账页面
│   │   │   ├── maintenance/
│   │   │   │   └── MaintenanceManagement.jsx  # 维护保养页面
│   │   │   └── spare-parts/
│   │   │       └── SparePartManagement.jsx  # 备件管理页面（新）
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

### 设备 API (/api/machines)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/machines` | 获取设备列表 |
| GET | `/api/machines/<id>` | 获取设备详情 |
| POST | `/api/machines` | 创建设备 |
| PUT | `/api/machines/<id>` | 更新设备 |
| DELETE | `/api/machines/<id>` | 删除设备 |

### 维护保养标准 API (/api/maintenance/standards)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/maintenance/standards` | 获取标准列表 |
| GET | `/api/maintenance/standards/<id>` | 获取标准详情 |
| POST | `/api/maintenance/standards` | 创建标准 |
| PUT | `/api/maintenance/standards/<id>` | 更新标准 |
| DELETE | `/api/maintenance/standards/<id>` | 删除标准 |

### 维护保养计划 API (/api/maintenance/plans)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/maintenance/plans` | 获取计划列表 |
| GET | `/api/maintenance/plans/<id>` | 获取计划详情 |
| POST | `/api/maintenance/plans` | 创建计划 |
| PUT | `/api/maintenance/plans/<id>` | 更新计划 |
| DELETE | `/api/maintenance/plans/<id>` | 删除计划 |
| POST | `/api/maintenance/plans/<id>/generate-order` | 从计划生成工单 |

### 维护保养工单 API (/api/maintenance/orders)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/maintenance/orders` | 获取工单列表 |
| GET | `/api/maintenance/orders/<id>` | 获取工单详情 |
| POST | `/api/maintenance/orders` | 创建工单 |
| PUT | `/api/maintenance/orders/<id>` | 更新工单 |
| DELETE | `/api/maintenance/orders/<id>` | 删除工单 |
| POST | `/api/maintenance/orders/<id>/start` | 开始执行 |
| POST | `/api/maintenance/orders/<id>/complete` | 完成工单 |
| POST | `/api/maintenance/orders/<id>/cancel` | 取消工单 |

### 故障报修 API (/api/maintenance/faults)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/maintenance/faults` | 获取报修列表 |
| GET | `/api/maintenance/faults/<id>` | 获取报修详情 |
| POST | `/api/maintenance/faults` | 创建报修 |
| PUT | `/api/maintenance/faults/<id>` | 更新报修 |
| POST | `/api/maintenance/faults/<id>/assign` | 指派处理人 |
| POST | `/api/maintenance/faults/<id>/start` | 开始处理 |
| POST | `/api/maintenance/faults/<id>/complete` | 完成处理 |
| POST | `/api/maintenance/faults/<id>/close` | 关闭报修 |

### 点检记录 API (/api/maintenance/inspections)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/maintenance/inspections` | 获取点检列表 |
| GET | `/api/maintenance/inspections/<id>` | 获取点检详情 |
| POST | `/api/maintenance/inspections` | 创建点检 |
| PUT | `/api/maintenance/inspections/<id>` | 更新点检 |
| DELETE | `/api/maintenance/inspections/<id>` | 删除点检 |

### 统计与日历 API (/api/maintenance)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/maintenance/calendar` | 获取维护日历 |
| GET | `/api/maintenance/statistics` | 获取维护统计 |
| GET | `/api/maintenance/overdue` | 获取逾期保养 |

### 集成 API (/api/integration)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/integration/machines` | 供 MES 查询设备列表 |
| GET | `/api/integration/machine-status/<id>` | 查询设备当前状态 |

### 备件分类 API (/api/spare-parts/categories) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/spare-parts/categories` | 获取分类列表（支持tree参数） |
| GET | `/api/spare-parts/categories/<id>` | 获取分类详情 |
| POST | `/api/spare-parts/categories` | 创建分类 |
| PUT | `/api/spare-parts/categories/<id>` | 更新分类 |
| DELETE | `/api/spare-parts/categories/<id>` | 删除分类 |

### 备件 API (/api/spare-parts) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/spare-parts` | 获取备件列表（分页筛选） |
| GET | `/api/spare-parts/options` | 获取备件选项（下拉） |
| GET | `/api/spare-parts/<id>` | 获取备件详情 |
| POST | `/api/spare-parts` | 创建备件 |
| PUT | `/api/spare-parts/<id>` | 更新备件 |
| DELETE | `/api/spare-parts/<id>` | 删除备件 |

### 出入库 API (/api/spare-parts/transactions) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/spare-parts/transactions` | 获取出入库记录 |
| GET | `/api/spare-parts/transactions/<id>` | 获取记录详情 |
| POST | `/api/spare-parts/transactions` | 创建出入库记录 |
| POST | `/api/spare-parts/issue` | 批量领用（关联工单） |

### 备件统计 API (/api/spare-parts/statistics) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/spare-parts/statistics/summary` | 统计概览 |
| GET | `/api/spare-parts/statistics/low-stock` | 库存预警列表 |
| GET | `/api/spare-parts/statistics/by-category` | 按分类统计 |
| GET | `/api/spare-parts/enums` | 获取枚举值 |

### 产能配置 API (/api/capacity/configs) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/capacity/configs` | 获取配置列表 |
| GET | `/api/capacity/configs/<id>` | 获取配置详情 |
| POST | `/api/capacity/configs` | 创建配置 |
| PUT | `/api/capacity/configs/<id>` | 更新配置 |
| DELETE | `/api/capacity/configs/<id>` | 删除配置 |
| POST | `/api/capacity/configs/<id>/activate` | 激活配置 |
| POST | `/api/capacity/configs/<id>/deactivate` | 停用配置 |
| GET | `/api/capacity/configs/by-machine/<machine_id>` | 获取设备配置 |
| GET | `/api/capacity/configs/current/<machine_id>` | 获取当前生效配置 |

### 产能调整 API (/api/capacity/adjustments) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/capacity/adjustments` | 获取调整列表 |
| POST | `/api/capacity/adjustments` | 创建调整 |
| DELETE | `/api/capacity/adjustments/<id>` | 取消调整 |

### 产能日志 API (/api/capacity/logs) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/capacity/logs` | 获取日志列表 |
| POST | `/api/capacity/logs` | 创建/更新日志 |
| DELETE | `/api/capacity/logs/<id>` | 删除日志 |

### 产能统计 API (/api/capacity/statistics) - 新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/capacity/statistics/summary` | 统计概览 |
| GET | `/api/capacity/statistics/by-machine` | 按设备统计 |
| GET | `/api/capacity/statistics/trend` | 产能趋势 |
| GET | `/api/capacity/enums` | 获取枚举值 |

---

## 数据模型

### Machine 设备

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| machine_code | String | 设备编码（唯一） |
| name | String | 设备名称 |
| model | String | 型号 |
| group | String | 设备分组/产线 |
| dept_name | String | 部门 |
| sub_dept_name | String | 子部门/班组 |
| is_active | Boolean | 是否在用 |
| factory_location | String | 工厂所在地 |
| brand | String | 品牌 |
| serial_no | String | 序列号 |
| manufacture_date | Date | 出厂日期 |
| purchase_date | Date | 购入日期 |
| place | String | 放置场所 |
| manufacturer | String | 制造商 |
| capacity | Integer | 产能（件/天） |
| status | String | 状态 |

### MaintenanceStandard 保养标准

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String | 标准编码（唯一） |
| name | String | 标准名称 |
| description | Text | 标准描述 |
| machine_id | Integer | 适用设备ID |
| machine_model | String | 适用设备型号 |
| equipment_group | String | 适用设备组 |
| maintenance_type | String | 保养类型 |
| cycle | String | 保养周期 |
| cycle_days | Integer | 自定义周期天数 |
| estimated_hours | Float | 预计工时 |
| check_items | JSON | 检查项目列表 |
| tools_required | JSON | 所需工具 |
| spare_parts | JSON | 所需备件 |
| safety_notes | Text | 安全注意事项 |
| is_active | Boolean | 是否启用 |

### MaintenancePlan 保养计划

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String | 计划编码（唯一） |
| name | String | 计划名称 |
| machine_id | Integer | 设备ID |
| standard_id | Integer | 保养标准ID |
| cycle | String | 执行周期 |
| cycle_days | Integer | 自定义周期天数 |
| start_date | Date | 开始日期 |
| end_date | Date | 结束日期 |
| next_due_date | Date | 下次执行日期 |
| last_executed_date | Date | 上次执行日期 |
| advance_days | Integer | 提前提醒天数 |
| responsible_id | Integer | 负责人ID |
| responsible_name | String | 负责人姓名 |
| is_active | Boolean | 是否启用 |

### MaintenanceOrder 保养工单

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_no | String | 工单编号（唯一） |
| title | String | 工单标题 |
| description | Text | 工单描述 |
| machine_id | Integer | 设备ID |
| plan_id | Integer | 来源计划ID |
| standard_id | Integer | 保养标准ID |
| maintenance_type | String | 保养类型 |
| source | String | 来源(manual/plan/fault) |
| planned_date | Date | 计划执行日期 |
| due_date | Date | 截止日期 |
| started_at | DateTime | 实际开始时间 |
| completed_at | DateTime | 实际完成时间 |
| estimated_hours | Float | 预计工时 |
| actual_hours | Float | 实际工时 |
| assigned_to_id | Integer | 指派人ID |
| assigned_to_name | String | 指派人姓名 |
| executor_id | Integer | 执行人ID |
| executor_name | String | 执行人姓名 |
| status | String | 状态 |
| priority | String | 优先级 |
| check_results | JSON | 检查结果 |
| spare_parts_used | JSON | 使用的备件 |
| cost | Float | 维护费用 |
| remark | Text | 备注 |

### FaultReport 故障报修

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| report_no | String | 报修单号（唯一） |
| title | String | 故障标题 |
| description | Text | 故障描述 |
| machine_id | Integer | 设备ID |
| fault_type | String | 故障类型 |
| severity | String | 严重程度 |
| fault_time | DateTime | 故障发生时间 |
| reporter_id | Integer | 报修人ID |
| reporter_name | String | 报修人姓名 |
| reporter_phone | String | 报修人电话 |
| handler_id | Integer | 处理人ID |
| handler_name | String | 处理人姓名 |
| status | String | 状态 |
| diagnosis | Text | 故障诊断 |
| solution | Text | 解决方案 |
| spare_parts_used | JSON | 使用的备件 |
| cost | Float | 维修费用 |
| assigned_at | DateTime | 指派时间 |
| started_at | DateTime | 开始处理时间 |
| completed_at | DateTime | 完成时间 |
| closed_at | DateTime | 关闭时间 |
| downtime_hours | Float | 停机时长 |

### InspectionRecord 点检记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| record_no | String | 点检单号（唯一） |
| machine_id | Integer | 设备ID |
| standard_id | Integer | 点检标准ID |
| inspection_date | Date | 点检日期 |
| shift | String | 班次 |
| inspector_id | Integer | 点检人ID |
| inspector_name | String | 点检人姓名 |
| result | String | 结果(normal/abnormal) |
| check_items | JSON | 点检项目结果 |
| abnormal_items | JSON | 异常项 |
| remark | Text | 备注 |

### SparePartCategory 备件分类 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String | 分类编码（唯一） |
| name | String | 分类名称 |
| parent_id | Integer | 父分类ID |
| level | Integer | 层级 |
| sort_order | Integer | 排序序号 |
| description | Text | 描述 |
| is_active | Boolean | 是否启用 |

### SparePart 备件 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String | 备件编码（唯一） |
| name | String | 备件名称 |
| category_id | Integer | 分类ID |
| specification | String | 规格型号 |
| brand | String | 品牌 |
| manufacturer | String | 制造商 |
| unit | String | 计量单位 |
| current_stock | Integer | 当前库存 |
| min_stock | Integer | 最低库存 |
| max_stock | Integer | 最高库存 |
| safety_stock | Integer | 安全库存 |
| unit_price | Float | 单价 |
| warehouse | String | 仓库 |
| location | String | 库位 |
| applicable_machines | JSON | 适用设备列表 |
| supplier | String | 供应商 |
| lead_time_days | Integer | 采购周期（天） |
| is_active | Boolean | 是否启用 |

### SparePartTransaction 出入库记录 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| transaction_no | String | 单据编号（唯一） |
| spare_part_id | Integer | 备件ID |
| transaction_type | String | 类型 |
| quantity | Integer | 数量（正入负出） |
| unit_price | Float | 单价 |
| total_amount | Float | 总金额 |
| before_stock | Integer | 变动前库存 |
| after_stock | Integer | 变动后库存 |
| reference_type | String | 关联单据类型 |
| reference_id | Integer | 关联单据ID |
| reference_no | String | 关联单据号 |
| machine_id | Integer | 关联设备ID |
| machine_code | String | 关联设备编码 |
| transaction_date | Date | 出入库日期 |
| operator_id | Integer | 操作人ID |
| operator_name | String | 操作人姓名 |
| remark | Text | 备注 |

### CapacityConfig 产能配置 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| config_code | String(50) | 配置编码（唯一） |
| machine_id | Integer | 设备ID |
| machine_code | String(64) | 设备编码 |
| machine_name | String(128) | 设备名称 |
| shift_type | String(20) | 班次类型（day/night/all） |
| standard_capacity | Integer | 标准产能（件/班次） |
| max_capacity | Integer | 最大产能 |
| min_capacity | Integer | 最小产能 |
| working_hours | Float | 班次工作小时数 |
| setup_time | Float | 换线时间（分钟） |
| cycle_time | Float | 节拍时间（秒/件） |
| product_type | String(100) | 产品类型 |
| product_code | String(50) | 产品编码 |
| effective_from | Date | 生效日期 |
| effective_to | Date | 失效日期 |
| status | String(20) | 状态（draft/active/inactive） |
| is_default | Boolean | 是否默认配置 |

**配置状态**:
- draft: 草稿
- active: 生效中
- inactive: 已停用

### CapacityAdjustment 产能调整 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| adjustment_code | String(50) | 调整编码（唯一） |
| machine_id | Integer | 设备ID |
| config_id | BigInteger | 关联配置ID |
| adjustment_type | String(30) | 调整类型 |
| reason | Text | 调整原因 |
| original_capacity | Integer | 原产能 |
| adjusted_capacity | Integer | 调整后产能 |
| adjustment_rate | Float | 调整比例（%） |
| effective_from | Date | 开始日期 |
| effective_to | Date | 结束日期 |
| is_active | Boolean | 是否生效 |

**调整类型**:
- temporary: 临时调整
- seasonal: 季节性调整
- maintenance: 维护调整
- upgrade: 设备升级
- other: 其他

### CapacityLog 产能日志 - 新

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| machine_id | Integer | 设备ID |
| log_date | Date | 日期 |
| shift_type | String(20) | 班次类型 |
| planned_capacity | Integer | 计划产能 |
| actual_output | Integer | 实际产出 |
| defective_count | Integer | 不良数量 |
| good_count | Integer | 良品数量 |
| utilization_rate | Float | 稼动率（%） |
| yield_rate | Float | 良品率（%） |
| oee | Float | OEE（%） |
| downtime_minutes | Integer | 停机时间（分钟） |
| downtime_reason | String(200) | 停机原因 |

**关键指标**:
- 稼动率 = 实际产出 / 计划产能 × 100%
- 良品率 = 良品数量 / 实际产出 × 100%
- OEE = 稼动率 × 良品率

---

## 状态流转

### 保养工单状态

```
┌─────────┐   开始执行   ┌───────────┐   完成    ┌──────────┐
│  待执行  │ ──────────► │  执行中   │ ───────► │  已完成  │
│(pending) │             │(in_progress)│          │(completed)│
└────┬────┘             └─────┬──────┘          └──────────┘
     │                        │
     │ 取消                   │ 取消
     ▼                        ▼
┌──────────┐            ┌──────────┐
│  已取消   │            │  已取消   │
│(cancelled)│            │(cancelled)│
└──────────┘            └──────────┘
```

### 故障报修状态

```
┌─────────┐   指派    ┌──────────┐   开始处理   ┌───────────┐
│  已报修  │ ───────► │  已指派   │ ──────────► │  处理中   │
│(reported)│          │(assigned) │             │(in_progress)│
└────┬────┘          └──────────┘             └─────┬──────┘
     │                                              │
     │ 关闭                                         │ 完成
     ▼                                              ▼
┌──────────┐          ┌──────────┐   关闭    ┌──────────┐
│  已关闭   │ ◄─────── │  已完成   │ ◄─────── │  处理中   │
│ (closed) │          │(completed)│          │(in_progress)│
└──────────┘          └──────────┘          └──────────┘
```

---

## 前端页面

| 页面 | 路径 | 说明 |
|------|------|------|
| MachineList | /machines | 设备台账管理 |
| MaintenanceManagement | /maintenance | 维护保养综合管理（含4个Tab） |
| SparePartManagement | /spare-parts | 备件管理（新） |

### MaintenanceManagement 页面功能

1. **保养工单** Tab
   - 工单列表（分页、筛选）
   - 新建/编辑工单
   - 开始执行、完成、取消操作
   - 状态/优先级标签展示

2. **保养计划** Tab
   - 计划列表（周期、负责人）
   - 新建/编辑计划
   - 从计划生成工单

3. **故障报修** Tab
   - 报修列表（严重程度、状态）
   - 新建报修
   - 指派、开始处理、完成、关闭操作

4. **点检记录** Tab
   - 点检记录列表
   - 新建点检记录
   - 结果（正常/异常）展示

### SparePartManagement 页面功能（新）

1. **备件列表** Tab
   - 备件列表（编码、名称、规格、库存、状态）
   - 搜索、分类筛选、库存状态筛选
   - 新建/编辑备件弹窗
   - 库存状态颜色标签

2. **分类管理** Tab
   - 树形分类展示
   - 新增/删除分类
   - 支持多层级

3. **出入库记录** Tab
   - 出入库记录列表
   - 新增出入库弹窗
   - 入库/出库方向标签

4. **库存预警** Tab
   - 统计概览（总数、缺货、库存不足、总值）
   - 本月出入库统计
   - 库存不足备件列表

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

# 构建前端
npm run build
```

---

## 已完成功能

- [x] 设备台账管理（CRUD）
- [x] 设备基础数据管理
- [x] **维护保养标准管理**
- [x] **维护保养计划管理**
- [x] **维护保养工单管理**
- [x] **故障报修管理**
- [x] **设备点检管理**
- [x] **维护日历与统计**
- [x] 系统集成 API（供 MES 调用）
- [x] **备件管理**（新）
  - [x] 备件分类管理（多层级）
  - [x] 备件信息管理（CRUD）
  - [x] 出入库管理
  - [x] 库存预警
  - [x] 备件统计
- [x] **设备产能配置**（新）
  - [x] 产能配置管理（CRUD、激活/停用）
  - [x] 产能调整记录
  - [x] 每日产能日志
  - [x] 产能统计分析（稼动率/良品率/OEE）

---

## 与其他系统的集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| Portal | JWT Token | 使用 Portal 签发的 Token |
| MES | API 调用 | MES 查询设备状态 |
| HR | API 调用 | 获取设备负责人信息 |

---

## 注意事项

1. **未部署**: EAM 系统尚未部署到生产环境
2. **端口**: 使用 8008 端口
3. **数据库**: 开发使用 SQLite，生产需配置 MySQL
4. **健康检查**: `/health` 路径
5. **维护工单**: 只有待执行或已取消状态的工单可以删除
6. **故障报修**: 创建报修会自动将设备状态改为"维修中"，完成后恢复"正常"
7. **备件管理**:
   - 有出入库记录的备件无法删除
   - 有子分类或备件的分类无法删除
   - 出库时自动检查库存是否足够
   - 库存低于安全库存时显示预警
