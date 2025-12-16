# SCM 仓库管理系统 - Claude Code 项目上下文

## 系统概述

SCM (Supply Chain Management - Warehouse) 是 JZC 企业管理系统的仓库管理模块，负责库存管理、入库出库、仓位管理等。

**部署状态**: 未部署

### 核心功能
- 物料分类管理（多层级树形结构）
- 物料主数据管理（完整属性）
- 仓库/库位管理
- 库存管理
- 入库/出库登记
- 库存预警（低库存提醒）
- 库存盘点
- **库存转移**
  - 仓库间转移
  - 库位间转移
  - 跨仓库库位转移
  - 快速转移
- **库存报表**
  - 库存汇总报表
  - 低库存预警报表
  - 周转率分析报表
  - 库龄分析报表
  - 库存价值报表
  - 库存变动报表
  - 分类统计报表
- **批次/序列号追踪**（新）
  - 批次管理（创建、质检、冻结/解冻）
  - 批次过期预警
  - 批次追溯
  - 序列号管理（单个/批量创建）
  - 序列号状态跟踪
  - 序列号追溯
  - 保修期管理
- 交货核销

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 8005 |
| 前端端口(dev) | 7000 |
| 前端路径 | `/scm/` |
| API路径 | `/scm/api/` |
| PM2服务名 | scm-backend |
| 数据库 | cncplan |
| 健康检查 | `curl http://127.0.0.1:8005/health` |

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
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base_data.py         # 基础数据模型
│   │   │   ├── inbound.py           # 入库单模型
│   │   │   ├── inventory.py         # 库存流水模型
│   │   │   ├── material.py          # 物料/仓库/库位/库存模型
│   │   │   ├── pending_shipment.py  # 待出货模型
│   │   │   ├── stocktake.py         # 盘点单模型
│   │   │   ├── transfer.py          # 库存转移模型
│   │   │   └── batch_serial.py      # 批次/序列号模型
│   │   ├── routes/
│   │   │   ├── auth.py              # 认证路由
│   │   │   ├── base_data.py         # 基础数据路由
│   │   │   ├── inbound.py           # 入库管理路由
│   │   │   ├── integration.py       # 集成API路由
│   │   │   ├── inventory.py         # 库存路由
│   │   │   ├── materials.py         # 物料/分类/仓库/库位路由
│   │   │   ├── pending_shipment.py  # 待出货路由
│   │   │   ├── stocktake.py         # 盘点管理路由
│   │   │   ├── transfer.py          # 库存转移路由
│   │   │   └── batch_serial.py      # 批次/序列号路由
│   │   └── services/                # 业务服务
│   │       └── hr_service.py        # HR集成服务
│   ├── scm.db                       # SQLite 数据库（开发）
│   └── venv/
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # 仪表板
│   │   │   ├── inventory/           # 库存模块
│   │   │   │   ├── Stock.jsx        # 库存总览
│   │   │   │   ├── In.jsx           # 入库登记
│   │   │   │   ├── Out.jsx          # 出库登记
│   │   │   │   ├── DeliveryCheck.jsx      # 交货核销
│   │   │   │   ├── TransactionHistory.jsx # 流水历史
│   │   │   │   └── PendingShipments.jsx   # 待出货
│   │   │   ├── materials/           # 物料模块
│   │   │   │   └── MaterialList.jsx # 物料管理页面
│   │   │   ├── inbound/             # 入库模块
│   │   │   │   └── InboundList.jsx  # 入库管理页面
│   │   │   ├── stocktake/           # 盘点模块
│   │   │   │   └── StocktakeList.jsx # 盘点管理页面
│   │   │   ├── transfer/            # 转移模块
│   │   │   │   └── TransferList.jsx # 库存转移页面
│   │   │   ├── batch-serial/        # 批次/序列号模块
│   │   │   │   ├── BatchList.jsx    # 批次管理页面
│   │   │   │   └── SerialList.jsx   # 序列号管理页面
│   │   │   └── settings/
│   │   │       └── BaseDataSettings.jsx # 基础设置
│   │   ├── services/
│   │   │   └── api.js               # API服务
│   │   └── utils/
│   │       ├── ssoAuth.js           # SSO认证
│   │       └── authEvents.js        # 认证事件
│   └── dist/
└── package.json
```

---

## API 路由清单

### 物料分类 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/categories` | 获取分类列表（支持树形） |
| GET | `/api/categories/<id>` | 获取分类详情 |
| POST | `/api/categories` | 创建分类 |
| PUT | `/api/categories/<id>` | 更新分类 |
| DELETE | `/api/categories/<id>` | 删除分类 |

### 物料 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/materials` | 获取物料列表 |
| GET | `/api/materials/search` | 搜索物料 |
| GET | `/api/materials/types` | 获取物料类型 |
| GET | `/api/materials/low-stock` | 获取低库存物料 |
| GET | `/api/materials/<id>` | 获取物料详情 |
| POST | `/api/materials` | 创建物料 |
| PUT | `/api/materials/<id>` | 更新物料 |
| DELETE | `/api/materials/<id>` | 删除物料 |

### 仓库 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/warehouses` | 获取仓库列表 |
| GET | `/api/warehouses/types` | 获取仓库类型 |
| GET | `/api/warehouses/<id>` | 获取仓库详情 |
| POST | `/api/warehouses` | 创建仓库 |
| PUT | `/api/warehouses/<id>` | 更新仓库 |
| DELETE | `/api/warehouses/<id>` | 删除仓库 |

### 库位 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/warehouses/<id>/bins` | 获取仓库库位列表 |
| POST | `/api/warehouses/<id>/bins` | 创建库位 |
| PUT | `/api/warehouses/<id>/bins/<bin_id>` | 更新库位 |
| DELETE | `/api/warehouses/<id>/bins/<bin_id>` | 删除库位 |
| POST | `/api/warehouses/<id>/bins/batch` | 批量创建库位 |

### 库存 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/inventory/stock` | 获取库存列表 |
| GET | `/api/inventory/transactions` | 获取库存流水 |
| POST | `/api/inventory/in` | 入库 |
| POST | `/api/inventory/out` | 出库 |
| POST | `/api/inventory/delivery` | 交货核销 |
| POST | `/api/inventory/adjust` | 库存调整 |

### 入库单 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/inbound` | 获取入库单列表 |
| GET | `/api/inbound/<id>` | 获取入库单详情 |
| POST | `/api/inbound` | 创建入库单 |
| PUT | `/api/inbound/<id>` | 更新入库单 |
| DELETE | `/api/inbound/<id>` | 删除入库单 |
| POST | `/api/inbound/<id>/submit` | 提交入库单 |
| POST | `/api/inbound/<id>/cancel` | 取消入库单 |
| POST | `/api/inbound/<id>/receive` | 执行入库收货 |
| GET | `/api/inbound/<id>/receive-logs` | 获取收货记录 |
| GET | `/api/inbound/types` | 获取入库类型 |
| GET | `/api/inbound/statuses` | 获取入库状态 |
| GET | `/api/inbound/statistics` | 获取入库统计 |
| POST | `/api/inbound/from-po` | 从采购订单创建入库单 |
| GET | `/api/inbound/pending-po` | 获取待入库采购订单 |

### 盘点单 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stocktake` | 获取盘点单列表 |
| GET | `/api/stocktake/<id>` | 获取盘点单详情（含明细） |
| POST | `/api/stocktake` | 创建盘点单 |
| PUT | `/api/stocktake/<id>` | 更新盘点单 |
| DELETE | `/api/stocktake/<id>` | 删除盘点单（仅草稿） |
| POST | `/api/stocktake/<id>/start` | 开始盘点（生成明细） |
| POST | `/api/stocktake/<id>/submit` | 提交审核 |
| POST | `/api/stocktake/<id>/approve` | 审核通过 |
| POST | `/api/stocktake/<id>/reject` | 审核拒绝 |
| POST | `/api/stocktake/<id>/cancel` | 取消盘点单 |
| POST | `/api/stocktake/<id>/items/<item_id>/count` | 录入盘点数量 |
| POST | `/api/stocktake/<id>/batch-count` | 批量录入盘点 |
| POST | `/api/stocktake/<id>/adjust` | 执行库存调整 |
| GET | `/api/stocktake/<id>/adjust-logs` | 获取调整记录 |
| GET | `/api/stocktake/types` | 获取盘点类型 |
| GET | `/api/stocktake/statuses` | 获取盘点状态 |
| GET | `/api/stocktake/statistics` | 获取盘点统计 |

### 库存报表 API（新）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/inventory/reports/summary` | 库存汇总报表 |
| GET | `/api/inventory/reports/by-warehouse` | 按仓库库存报表 |
| GET | `/api/inventory/reports/by-category` | 按分类库存报表 |
| GET | `/api/inventory/reports/low-stock` | 低库存预警报表 |
| GET | `/api/inventory/reports/turnover` | 周转率分析报表 |
| GET | `/api/inventory/reports/aging` | 库龄分析报表 |
| GET | `/api/inventory/reports/movement` | 库存变动报表 |
| GET | `/api/inventory/reports/value` | 库存价值报表 |

### 转移单 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/transfer` | 获取转移单列表 |
| GET | `/api/transfer/<id>` | 获取转移单详情（含明细） |
| POST | `/api/transfer` | 创建转移单 |
| PUT | `/api/transfer/<id>` | 更新转移单（仅草稿） |
| DELETE | `/api/transfer/<id>` | 删除转移单（仅草稿/已取消） |
| POST | `/api/transfer/<id>/submit` | 提交转移单 |
| POST | `/api/transfer/<id>/cancel` | 取消转移单 |
| POST | `/api/transfer/<id>/execute` | 执行转移（支持部分转移） |
| POST | `/api/transfer/<id>/complete` | 强制完成转移单 |
| GET | `/api/transfer/<id>/items` | 获取转移单明细 |
| POST | `/api/transfer/<id>/items` | 添加转移明细 |
| PUT | `/api/transfer/<id>/items/<item_id>` | 更新转移明细 |
| DELETE | `/api/transfer/<id>/items/<item_id>` | 删除转移明细 |
| GET | `/api/transfer/<id>/logs` | 获取转移执行日志 |
| POST | `/api/transfer/quick` | 快速转移（创建并立即执行） |
| GET | `/api/transfer/types` | 获取转移类型 |
| GET | `/api/transfer/statuses` | 获取转移状态 |
| GET | `/api/transfer/statistics` | 获取转移统计 |

### 批次管理 API（新）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/batch-serial/batches` | 获取批次列表 |
| GET | `/api/batch-serial/batches/<id>` | 获取批次详情（含交易记录/序列号） |
| POST | `/api/batch-serial/batches` | 创建批次 |
| PUT | `/api/batch-serial/batches/<id>` | 更新批次 |
| POST | `/api/batch-serial/batches/<id>/block` | 冻结批次 |
| POST | `/api/batch-serial/batches/<id>/unblock` | 解冻批次 |
| POST | `/api/batch-serial/batches/<id>/quality-check` | 批次质检 |
| GET | `/api/batch-serial/batches/<id>/trace` | 批次追溯 |
| GET | `/api/batch-serial/batches/expiring` | 即将过期批次 |
| GET | `/api/batch-serial/batches/statistics` | 批次统计 |

### 序列号管理 API（新）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/batch-serial/serials` | 获取序列号列表 |
| GET | `/api/batch-serial/serials/<id>` | 获取序列号详情（含流转记录） |
| POST | `/api/batch-serial/serials` | 创建序列号 |
| POST | `/api/batch-serial/serials/batch-create` | 批量创建序列号 |
| PUT | `/api/batch-serial/serials/<id>` | 更新序列号 |
| POST | `/api/batch-serial/serials/<id>/status` | 更新序列号状态 |
| GET | `/api/batch-serial/serials/<id>/trace` | 序列号追溯 |
| GET | `/api/batch-serial/serials/by-serial-no/<no>` | 按序列号查询 |
| GET | `/api/batch-serial/serials/statistics` | 序列号统计 |
| GET | `/api/batch-serial/enums` | 获取枚举值 |

### 集成 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/integration/inventory` | 供其他系统查询库存 |
| POST | `/api/integration/deduct` | 扣减库存（出货系统调用） |

---

## 数据模型

### MaterialCategory 物料分类

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String(50) | 分类编码 |
| name | String(100) | 分类名称 |
| parent_id | Integer | 父级分类 ID |
| level | Integer | 层级（1-5） |
| path | String(500) | 路径（如 /1/2/3/） |
| description | Text | 描述 |
| default_uom | String(20) | 默认计量单位 |
| is_active | Boolean | 是否启用 |
| sort_order | Integer | 排序 |

### Material 物料主数据

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String(50) | 物料编码（唯一） |
| barcode | String(100) | 条形码 |
| customer_code | String(50) | 客户编码 |
| supplier_code | String(50) | 供应商编码 |
| name | String(200) | 物料名称 |
| short_name | String(50) | 简称 |
| english_name | String(200) | 英文名 |
| description | Text | 描述 |
| category_id | Integer | 分类 ID |
| material_type | Enum | 物料类型（原材料/半成品/成品/消耗品/备件/包装/其他） |
| specification | String(200) | 规格 |
| model | String(100) | 型号 |
| brand | String(100) | 品牌 |
| color | String(50) | 颜色 |
| material | String(100) | 材质 |
| base_uom | String(20) | 基本计量单位 |
| purchase_uom | String(20) | 采购单位 |
| sales_uom | String(20) | 销售单位 |
| purchase_conversion | Decimal | 采购单位换算率 |
| sales_conversion | Decimal | 销售单位换算率 |
| min_stock | Decimal | 最低库存 |
| max_stock | Decimal | 最高库存 |
| safety_stock | Decimal | 安全库存 |
| reorder_point | Decimal | 补货点 |
| reorder_qty | Decimal | 补货量 |
| default_warehouse_id | Integer | 默认仓库 |
| default_bin | String(50) | 默认库位 |
| shelf_life_days | Integer | 保质期（天） |
| is_batch_managed | Boolean | 启用批次管理 |
| is_serial_managed | Boolean | 启用序列号管理 |
| reference_cost | Decimal | 参考成本 |
| reference_price | Decimal | 参考售价 |
| currency | String(10) | 币种 |
| gross_weight | Decimal | 毛重(kg) |
| net_weight | Decimal | 净重(kg) |
| length/width/height | Decimal | 尺寸(mm) |
| volume | Decimal | 体积(m³) |
| image_url | String(500) | 图片 |
| drawing_url | String(500) | 图纸 |
| attachments | JSON | 附件列表 |
| status | Enum | 状态（启用/停用/作废） |
| remark | Text | 备注 |

### Warehouse 仓库

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String(50) | 仓库编码 |
| name | String(100) | 仓库名称 |
| short_name | String(50) | 简称 |
| location_id | String(50) | 位置编码 |
| address | String(200) | 地址 |
| warehouse_type | Enum | 仓库类型（普通/虚拟/寄售） |
| is_active | Boolean | 是否启用 |
| is_allow_negative | Boolean | 允许负库存 |
| manager_id | Integer | 管理员 ID |
| manager_name | String(50) | 管理员姓名 |
| contact_phone | String(20) | 联系电话 |

### StorageBin 库位

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String(50) | 库位编码 |
| name | String(100) | 库位名称 |
| warehouse_id | Integer | 所属仓库 |
| zone | String(50) | 区域 |
| aisle | String(50) | 通道 |
| rack | String(50) | 货架 |
| level | String(50) | 层 |
| position | String(50) | 位 |
| is_active | Boolean | 是否启用 |
| max_weight | Decimal | 最大承重(kg) |
| max_volume | Decimal | 最大容积(m³) |
| bin_type | Enum | 库位类型（正常/拣货/临时/不良品） |
| allowed_material_types | JSON | 允许的物料类型 |

### Inventory 库存汇总

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| material_id | Integer | 物料 ID |
| warehouse_id | Integer | 仓库 ID |
| bin_id | Integer | 库位 ID |
| batch_no | String(50) | 批次号 |
| serial_no | String(100) | 序列号 |
| quantity | Decimal | 数量 |
| reserved_qty | Decimal | 预留数量 |
| available_qty | Decimal | 可用数量 |
| uom | String(20) | 单位 |
| production_date | Date | 生产日期 |
| expiry_date | Date | 过期日期 |
| last_in_date | DateTime | 最近入库 |
| last_out_date | DateTime | 最近出库 |

### InboundOrder 入库单

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_no | String(50) | 入库单号（唯一） |
| inbound_type | Enum | 入库类型（采购/生产/调拨/退货/其他） |
| status | Enum | 状态（草稿/待入库/部分入库/已完成/已取消） |
| source_no | String(100) | 来源单号（PO号等） |
| source_system | String(50) | 来源系统 |
| supplier_id | Integer | 供应商ID |
| supplier_name | String(200) | 供应商名称 |
| warehouse_id | Integer | 目标仓库 |
| warehouse_name | String(100) | 仓库名称 |
| planned_date | Date | 计划入库日期 |
| actual_date | Date | 实际入库日期 |
| total_planned_qty | Decimal | 计划总数量 |
| total_received_qty | Decimal | 实收总数量 |
| is_inspected | Boolean | 是否已质检 |
| inspection_result | String(20) | 质检结果 |
| remark | Text | 备注 |

### InboundOrderItem 入库单明细

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_id | Integer | 入库单ID |
| line_no | Integer | 行号 |
| material_id | Integer | 物料ID |
| material_code | String(50) | 物料编码 |
| material_name | String(200) | 物料名称 |
| planned_qty | Decimal | 计划数量 |
| received_qty | Decimal | 实收数量 |
| rejected_qty | Decimal | 拒收数量 |
| uom | String(20) | 单位 |
| bin_id | Integer | 库位ID |
| bin_code | String(50) | 库位编码 |
| batch_no | String(50) | 批次号 |
| unit_price | Decimal | 单价 |
| amount | Decimal | 金额 |

### StocktakeOrder 盘点单

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_no | String(50) | 盘点单号（唯一） |
| stocktake_type | Enum | 盘点类型（全盘/抽盘/循环盘点/抽查） |
| status | Enum | 状态（草稿/盘点中/待审核/已审核/已调整/已取消） |
| warehouse_id | Integer | 仓库ID |
| warehouse_name | String(100) | 仓库名称 |
| category_id | Integer | 物料分类ID（可选，用于抽盘） |
| category_name | String(100) | 物料分类名称 |
| stocktake_date | Date | 盘点日期 |
| start_time | DateTime | 开始时间 |
| end_time | DateTime | 结束时间 |
| total_items | Integer | 盘点项数 |
| counted_items | Integer | 已盘点项数 |
| diff_items | Integer | 差异项数 |
| total_book_qty | Decimal | 账面总数量 |
| total_actual_qty | Decimal | 实际总数量 |
| total_diff_qty | Decimal | 差异总数量 |
| total_diff_amount | Decimal | 差异总金额 |
| remark | Text | 备注 |
| stocktaker_id | Integer | 盘点员ID |
| stocktaker_name | String(50) | 盘点员姓名 |
| reviewer_id | Integer | 审核人ID |
| reviewer_name | String(50) | 审核人姓名 |
| reviewed_at | DateTime | 审核时间 |
| review_remark | Text | 审核备注 |

### StocktakeOrderItem 盘点单明细

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_id | Integer | 盘点单ID |
| line_no | Integer | 行号 |
| material_id | Integer | 物料ID |
| material_code | String(50) | 物料编码 |
| material_name | String(200) | 物料名称 |
| specification | String(200) | 规格 |
| uom | String(20) | 单位 |
| bin_id | Integer | 库位ID |
| bin_code | String(50) | 库位编码 |
| batch_no | String(50) | 批次号 |
| book_qty | Decimal | 账面数量 |
| actual_qty | Decimal | 实际数量 |
| diff_qty | Decimal | 差异数量（实际-账面） |
| unit_cost | Decimal | 单位成本 |
| book_amount | Decimal | 账面金额 |
| actual_amount | Decimal | 实际金额 |
| diff_amount | Decimal | 差异金额 |
| count_status | String(20) | 盘点状态（pending/counted/adjusted） |
| counted_at | DateTime | 盘点时间 |
| counted_by | Integer | 盘点人ID |
| diff_reason | String(200) | 差异原因 |
| adjust_status | String(20) | 调整状态 |

### StocktakeAdjustLog 盘点调整记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_id | Integer | 盘点单ID |
| item_id | Integer | 盘点明细ID |
| material_code | String(50) | 物料编码 |
| material_name | String(200) | 物料名称 |
| book_qty | Decimal | 账面数量 |
| actual_qty | Decimal | 实际数量 |
| adjust_qty | Decimal | 调整数量 |
| adjust_type | String(20) | 调整类型（increase/decrease） |
| adjusted_by | Integer | 调整人ID |
| adjusted_by_name | String(50) | 调整人姓名 |
| adjusted_at | DateTime | 调整时间 |
| remark | Text | 备注 |
| inventory_tx_id | Integer | 关联的库存流水ID |

### TransferOrder 转移单（新）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_no | String(50) | 转移单号（唯一） |
| transfer_type | Enum | 转移类型（warehouse/bin/cross） |
| status | Enum | 状态（draft/pending/in_progress/completed/cancelled） |
| source_warehouse_id | Integer | 源仓库ID |
| source_warehouse_name | String(100) | 源仓库名称 |
| source_bin_id | Integer | 源库位ID |
| source_bin_code | String(50) | 源库位编码 |
| target_warehouse_id | Integer | 目标仓库ID |
| target_warehouse_name | String(100) | 目标仓库名称 |
| target_bin_id | Integer | 目标库位ID |
| target_bin_code | String(50) | 目标库位编码 |
| planned_date | Date | 计划转移日期 |
| actual_date | Date | 实际转移日期 |
| total_planned_qty | Decimal | 计划总数量 |
| total_transferred_qty | Decimal | 已转移总数量 |
| reason | String(200) | 转移原因 |
| remark | Text | 备注 |
| created_by | Integer | 创建人ID |
| submitted_by | Integer | 提交人ID |
| executed_by | Integer | 执行人ID |
| completed_at | DateTime | 完成时间 |

### TransferOrderItem 转移单明细（新）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_id | Integer | 转移单ID |
| line_no | Integer | 行号 |
| material_id | Integer | 物料ID |
| material_code | String(64) | 物料编码 |
| material_name | String(200) | 物料名称 |
| specification | String(200) | 规格 |
| planned_qty | Decimal | 计划数量 |
| transferred_qty | Decimal | 已转移数量 |
| uom | String(20) | 单位 |
| batch_no | String(64) | 批次号 |
| serial_no | String(64) | 序列号 |
| source_bin_id | Integer | 源库位ID（明细级别） |
| target_bin_id | Integer | 目标库位ID（明细级别） |
| item_status | String(20) | 状态（pending/partial/completed） |
| transferred_at | DateTime | 转移时间 |
| transferred_by | Integer | 转移人ID |

### TransferLog 转移执行日志（新）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_id | Integer | 转移单ID |
| item_id | Integer | 转移明细ID |
| material_code | String(64) | 物料编码 |
| material_name | String(200) | 物料名称 |
| transfer_qty | Decimal | 转移数量 |
| uom | String(20) | 单位 |
| batch_no | String(64) | 批次号 |
| source_warehouse_name | String(100) | 源仓库名称 |
| source_bin_code | String(50) | 源库位编码 |
| target_warehouse_name | String(100) | 目标仓库名称 |
| target_bin_code | String(50) | 目标库位编码 |
| executed_by | Integer | 执行人ID |
| executed_by_name | String(50) | 执行人姓名 |
| executed_at | DateTime | 执行时间 |
| inventory_tx_out_id | Integer | 出库流水ID |
| inventory_tx_in_id | Integer | 入库流水ID |

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

- [x] 基础框架搭建
- [x] 物料分类管理（多层级树形）
- [x] 物料主数据管理
- [x] 仓库管理
- [x] 库位管理（含批量创建）
- [x] 库存总览
- [x] 入库/出库登记
- [x] 交货核销
- [x] 库存流水历史
- [x] 低库存预警
- [x] 基础数据设置
- [x] 系统集成 API
- [x] 入库单管理（含采购入库关联）
- [x] 库存盘点（盘点单管理、差异审核、库存调整）
- [x] 库存转移（仓库/库位转移、快速转移）
- [x] 库存报表（汇总、低库存、周转率、库龄、价值、变动、分类）
- [x] 批次管理（批次创建、质检、冻结/解冻、过期预警、追溯）
- [x] 序列号管理（序列号创建、批量创建、状态管理、追溯、保修跟踪）

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
