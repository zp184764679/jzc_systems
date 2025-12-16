# SHM 出货管理系统 - Claude Code 项目上下文

## 系统概述

SHM (Shipment Management) 是 JZC 企业管理系统的出货管理模块，负责管理产品出货流程，包括出货单创建、物流跟踪、客户地址管理和交货要求管理。

**部署状态**: 已部署

### 核心功能
- 出货单管理（创建、编辑、状态跟踪）
- 出货明细管理
- 客户收货地址管理
- 交货要求/包装要求管理
- CRM 客户信息集成
- SCM 库存信息集成
- **出货报表**
  - 汇总统计
  - 客户分析
  - 产品分析
  - 趋势分析
  - 交付绩效
- **RMA退货管理**
  - RMA单创建/编辑/删除
  - 从出货单创建RMA
  - 审批流程（审批/拒绝/收货/检验/完成/取消）
  - RMA明细管理
  - 统计分析
- **批量出货操作**（新）
  - 批量发货（自动扣减库存）
  - 批量签收
  - 批量删除（仅待出货单）
  - 操作结果明细反馈

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 8006 |
| 前端端口(dev) | 7500 |
| 前端路径 | `/shm/` |
| API路径 | `/shm/api/` |
| PM2服务名 | shm-backend |
| 数据库 | cncplan |
| 健康检查 | `curl http://127.0.0.1:8006/health` |

---

## 技术栈

### 前端
- React 19.0.0
- Vite
- Ant Design 6.0.0

### 后端
- Flask 3.0.0 + Flask-CORS 4.0.0
- Flask-SQLAlchemy 3.1.1 + Flask-Migrate 4.0.5
- PyMySQL 1.1.0
- PyJWT 2.8.0

---

## 目录结构

```
SHM/
├── backend/
│   ├── main.py                      # Flask 应用入口
│   ├── config.py                    # 配置文件
│   ├── extensions.py                # Flask 扩展
│   ├── requirements.txt             # Python 依赖
│   ├── models/
│   │   ├── __init__.py
│   │   ├── shipment.py              # 出货单/明细/地址/要求模型
│   │   └── base_data.py             # 基础数据模型
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                  # 认证路由
│   │   ├── shipments.py             # 出货单路由（含打印功能）
│   │   ├── addresses.py             # 地址管理路由
│   │   ├── requirements.py          # 交货要求路由
│   │   ├── base_data.py             # 基础数据路由
│   │   ├── integration.py           # 系统集成路由
│   │   ├── logistics.py             # 物流追踪路由
│   │   ├── reports.py               # 出货报表路由
│   │   └── rma.py                   # RMA退货管理路由
│   ├── services/
│   │   ├── __init__.py
│   │   ├── crm_service.py           # CRM 客户服务
│   │   ├── scm_service.py           # SCM 库存服务
│   │   ├── hr_service.py            # HR 员工服务
│   │   └── pdm_service.py           # PDM 产品服务
│   ├── shm.db                       # SQLite 数据库（本地开发）
│   └── venv/
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api.js                   # API 服务
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # 仪表盘
│   │   │   ├── ShipmentList.jsx     # 出货单列表
│   │   │   ├── ShipmentCreate.jsx   # 创建出货单
│   │   │   ├── ShipmentDetail.jsx   # 出货单详情（含打印按钮）
│   │   │   ├── AddressList.jsx      # 地址列表
│   │   │   ├── RequirementList.jsx  # 交货要求列表
│   │   │   ├── Reports.jsx          # 出货报表页面
│   │   │   └── RMAList.jsx          # RMA退货管理页面
│   │   ├── components/
│   │   │   ├── PrintPreview.jsx     # 打印预览组件
│   │   │   └── LogisticsTracking.jsx # 物流追踪组件
│   │   └── utils/
│   │       ├── ssoAuth.js           # SSO 认证
│   │       └── authEvents.js        # 认证事件
│   └── dist/
├── public/
└── package.json
```

---

## API 路由清单

### 出货单 API (/api/shipments)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/shipments` | 获取出货单列表 |
| GET | `/api/shipments/<id>` | 获取出货单详情 |
| POST | `/api/shipments` | 创建出货单 |
| PUT | `/api/shipments/<id>` | 更新出货单 |
| DELETE | `/api/shipments/<id>` | 删除出货单 |
| PUT | `/api/shipments/<id>/status` | 更新状态 |
| POST | `/api/shipments/<id>/ship` | 发货操作 |
| GET | `/api/shipments/stats` | 获取统计数据 |

### 批量操作 API (/api/shipments)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/shipments/batch-ship` | 批量发货（扣减库存） |
| POST | `/api/shipments/batch-status` | 批量更新状态 |
| POST | `/api/shipments/batch-delete` | 批量删除（仅待出货） |

### 打印 API (/api/shipments)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/shipments/<id>/print/delivery-note` | 获取送货单打印数据 |
| GET | `/api/shipments/<id>/print/packing-list` | 获取装箱单打印数据 |
| POST | `/api/shipments/batch-print` | 批量打印数据 |

### 物流追踪 API (/api)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/shipments/<id>/traces` | 获取物流轨迹 |
| POST | `/api/shipments/<id>/traces` | 添加物流轨迹 |
| PUT | `/api/traces/<id>` | 更新物流轨迹 |
| DELETE | `/api/traces/<id>` | 删除物流轨迹 |
| GET | `/api/shipments/<id>/receipt` | 获取签收回执 |
| POST | `/api/shipments/<id>/receipt` | 创建签收回执 |
| PUT | `/api/shipments/<id>/receipt` | 更新签收回执 |
| POST | `/api/shipments/<id>/ship` | 发货操作（更新发货信息+添加轨迹） |
| POST | `/api/shipments/<id>/sign` | 快速签收（创建回执+添加轨迹） |
| GET | `/api/logistics/event-types` | 获取物流事件类型枚举 |
| GET | `/api/logistics/receipt-conditions` | 获取收货状况枚举 |

### 出货报表 API (/api/reports)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/reports/summary` | 获取出货汇总统计 |
| GET | `/api/reports/by-customer` | 按客户统计出货数据 |
| GET | `/api/reports/by-product` | 按产品统计出货数据 |
| GET | `/api/reports/trend` | 获取出货趋势数据（按日/周/月） |
| GET | `/api/reports/delivery-performance` | 获取交付绩效数据 |
| GET | `/api/reports/by-warehouse` | 按仓库统计出货数据 |
| GET | `/api/reports/export` | 导出报表数据 |

### 客户地址 API (/api/addresses)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/addresses` | 获取地址列表 |
| GET | `/api/addresses/<id>` | 获取地址详情 |
| POST | `/api/addresses` | 创建地址 |
| PUT | `/api/addresses/<id>` | 更新地址 |
| DELETE | `/api/addresses/<id>` | 删除地址 |
| GET | `/api/addresses/customer/<customer_id>` | 按客户获取地址 |

### 交货要求 API (/api/requirements)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/requirements` | 获取交货要求列表 |
| GET | `/api/requirements/<id>` | 获取交货要求详情 |
| POST | `/api/requirements` | 创建交货要求 |
| PUT | `/api/requirements/<id>` | 更新交货要求 |
| DELETE | `/api/requirements/<id>` | 删除交货要求 |
| GET | `/api/requirements/customer/<customer_id>` | 按客户获取要求 |

### RMA退货管理 API (/api/rma)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/rma` | 获取RMA列表 |
| GET | `/api/rma/<id>` | 获取RMA详情 |
| POST | `/api/rma` | 创建RMA |
| PUT | `/api/rma/<id>` | 更新RMA |
| DELETE | `/api/rma/<id>` | 删除RMA（仅待审核状态） |
| POST | `/api/rma/<id>/approve` | 审批通过 |
| POST | `/api/rma/<id>/reject` | 拒绝 |
| POST | `/api/rma/<id>/receive` | 确认收货 |
| POST | `/api/rma/<id>/inspect` | 质检完成 |
| POST | `/api/rma/<id>/complete` | 完成RMA |
| POST | `/api/rma/<id>/cancel` | 取消RMA |
| GET | `/api/rma/statistics` | 获取RMA统计 |
| GET | `/api/rma/enums` | 获取状态/类型枚举 |
| GET | `/api/rma/from-shipment/<id>` | 获取出货单可退货明细 |

### 集成 API (/api/integration)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/integration/customers` | 获取 CRM 客户列表 |
| GET | `/api/integration/inventory` | 获取 SCM 库存 |
| GET | `/api/integration/products` | 获取产品列表 |

---

## 数据模型

### Shipment 出货单

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| shipment_no | String(50) | 出货单号（唯一） |
| order_no | String(50) | 订单号 |
| customer_id | String(50) | 客户 ID |
| customer_name | String(200) | 客户名称 |
| delivery_date | Date | 出货日期 |
| expected_arrival | Date | 预计到达日期 |
| shipping_method | String(50) | 运输方式 |
| carrier | String(100) | 承运商 |
| tracking_no | String(100) | 物流单号 |
| status | String(20) | 状态（待出货/已发货/已签收/已取消） |
| warehouse_id | String(50) | 发货仓库 |
| receiver_contact | String(100) | 收货联系人 |
| receiver_phone | String(50) | 收货电话 |
| receiver_address | String(500) | 收货地址 |
| items | Relationship | 出货明细 |

### ShipmentItem 出货明细

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| shipment_id | Integer | 出货单 ID |
| product_code | String(100) | 产品编码 |
| product_name | String(200) | 产品名称 |
| qty | Decimal | 数量 |
| unit | String(20) | 单位 |
| bin_code | String(50) | 仓位 |
| batch_no | String(50) | 批次号 |

### CustomerAddress 客户地址

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| customer_id | String(50) | 客户 ID |
| customer_name | String(200) | 客户名称 |
| contact_person | String(100) | 联系人 |
| contact_phone | String(50) | 联系电话 |
| province | String(50) | 省份 |
| city | String(50) | 城市 |
| district | String(50) | 区县 |
| address | String(500) | 详细地址 |
| is_default | Boolean | 是否默认 |

### DeliveryRequirement 交货要求

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| customer_id | String(50) | 客户 ID |
| packaging_type | String(50) | 包装类型 |
| packaging_material | String(50) | 包装材料 |
| labeling_requirement | String(200) | 标签要求 |
| delivery_time_window | String(100) | 送货时间窗口 |
| special_instructions | Text | 特殊说明 |
| quality_cert_required | Boolean | 是否需要质检报告 |

### LogisticsTrace 物流轨迹

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| shipment_id | Integer | 出货单 ID (FK) |
| event_type | String(50) | 事件类型（枚举） |
| event_time | DateTime | 事件时间 |
| location | String(200) | 地点 |
| description | String(500) | 描述 |
| operator | String(100) | 操作人 |
| operator_phone | String(50) | 操作人电话 |
| remark | Text | 备注 |

**LogisticsEventType 事件类型枚举**:
- `created` - 已创建
- `picked_up` - 已揽收
- `in_transit` - 运输中
- `arrived` - 已到达
- `out_for_delivery` - 派送中
- `delivered` - 已签收
- `exception` - 异常
- `returned` - 已退回

### DeliveryReceipt 签收回执

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| shipment_id | Integer | 出货单 ID (FK, 唯一) |
| receiver_name | String(100) | 签收人姓名 |
| receiver_phone | String(50) | 签收人电话 |
| receiver_id_card | String(50) | 签收人身份证 |
| sign_time | DateTime | 签收时间 |
| sign_location | String(200) | 签收地点 |
| sign_photo | String(500) | 签收照片路径 |
| signature_image | String(500) | 签名图片路径 |
| receipt_condition | String(50) | 收货状况（完好/部分损坏/严重损坏） |
| damage_description | Text | 损坏描述 |
| damage_photos | Text | 损坏照片路径（JSON数组） |
| actual_qty | Decimal | 实际收货数量 |
| qty_difference | Decimal | 数量差异 |
| difference_reason | Text | 差异原因 |
| feedback | Text | 客户反馈 |

### RMAOrder RMA退货单

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| rma_no | String(50) | RMA单号（唯一） |
| shipment_id | Integer | 原出货单 ID (FK) |
| shipment_no | String(50) | 原出货单号 |
| customer_id | String(50) | 客户 ID |
| customer_name | String(200) | 客户名称 |
| rma_type | String(20) | 退货类型（枚举） |
| status | String(20) | 状态（枚举） |
| handle_method | String(20) | 处理方式（枚举） |
| reason | Text | 退货原因 |
| apply_date | Date | 申请日期 |
| return_contact | String(100) | 退货联系人 |
| return_phone | String(50) | 退货电话 |
| return_address | String(500) | 退货地址 |
| return_carrier | String(100) | 退货承运商 |
| return_tracking_no | String(100) | 退货物流单号 |
| approved_at | DateTime | 审批时间 |
| approved_by | Integer | 审批人ID |
| approved_by_name | String(100) | 审批人姓名 |
| reject_reason | Text | 拒绝原因 |
| refund_amount | Decimal | 退款金额 |
| credit_amount | Decimal | 抵扣金额 |
| inspection_result | String(50) | 质检结果 |
| inspection_note | Text | 质检备注 |

**RMAStatus 状态枚举**:
- `pending` - 待审核
- `approved` - 已批准
- `rejected` - 已拒绝
- `receiving` - 待收货
- `received` - 已收货
- `inspecting` - 质检中
- `completed` - 已完成
- `cancelled` - 已取消

**RMAType 类型枚举**:
- `quality` - 质量问题
- `wrong_item` - 发错货
- `damaged` - 运输损坏
- `excess` - 多发
- `other` - 其他

**RMAHandleMethod 处理方式枚举**:
- `refund` - 退款
- `exchange` - 换货
- `repair` - 维修
- `credit` - 抵扣

### RMAItem RMA明细

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| rma_id | Integer | RMA单 ID (FK) |
| shipment_item_id | Integer | 原出货明细 ID |
| product_code | String(100) | 产品编码 |
| product_name | String(200) | 产品名称 |
| original_qty | Decimal | 原出货数量 |
| return_qty | Decimal | 退货数量 |
| unit | String(20) | 单位 |
| qualified_qty | Decimal | 合格数量 |
| unqualified_qty | Decimal | 不合格数量 |
| restocked_qty | Decimal | 入库数量 |
| defect_description | Text | 缺陷描述 |

---

## 前端页面

### Dashboard.jsx - 仪表盘
- 出货统计概览
- 待处理出货单
- 最近出货记录

### ShipmentList.jsx - 出货单列表
- 出货单表格
- 状态筛选
- 搜索功能

### ShipmentCreate.jsx - 创建出货单
- 基本信息表单
- 出货明细添加
- 客户地址选择

### ShipmentDetail.jsx - 出货单详情
- 详细信息展示
- 状态更新
- 物流跟踪

### AddressList.jsx - 地址管理
- 客户地址列表
- 新增/编辑地址

### RequirementList.jsx - 交货要求
- 客户交货要求列表
- 包装/标签要求配置

### Reports.jsx - 出货报表
- 汇总统计（出货单数、数量、状态分布、环比增长）
- 客户分析（按客户出货量、签收率统计）
- 产品分析（按产品出货量、客户数统计）
- 趋势分析（按日/周/月查看出货趋势）
- 交付绩效（准时率、完好率、承运商绩效）

### RMAList.jsx - RMA退货管理
- 统计卡片（待审核/待收货/处理中/本月完成）
- 搜索筛选（单号/客户/状态/类型/日期范围）
- RMA列表表格（单号/出货单/客户/类型/状态/处理方式/日期/数量）
- 新建/编辑弹窗（选择出货单、退货类型、处理方式、退货明细）
- 详情弹窗（完整信息+明细表格）
- 操作弹窗（审批/拒绝/收货/完成）
- 状态流转操作（审批/拒绝/收货/检验/完成/取消）

---

## 本地开发

```bash
# 启动后端
cd SHM/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py

# 启动前端
cd SHM/frontend
npm install
npm run dev

# 构建前端
npm run build
```

---

## 已完成功能

- [x] 出货单 CRUD
- [x] 出货明细管理
- [x] 客户地址管理
- [x] 交货要求管理
- [x] 出货状态跟踪
- [x] CRM 客户集成
- [x] SCM 库存集成
- [x] SSO 认证集成
- [x] 打印功能（送货单、装箱单）
- [x] 物流追踪（轨迹记录、事件时间线）
- [x] 签收回执（签收确认、状况记录）
- [x] 快速发货/签收操作
- [x] 出货报表（汇总统计、客户分析、产品分析、趋势分析、交付绩效）
- [x] RMA退货管理（CRUD、审批流程、质检、入库）
- [x] 批量出货操作（批量发货扣库存、批量签收、批量删除）

---

## 与其他系统的集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| Portal | JWT Token | 使用 Portal 签发的 Token |
| CRM | API 调用 | 获取客户信息 |
| SCM | API 调用 | 获取库存信息、扣减库存 |
| PDM | API 调用 | 获取产品信息 |
| shared/auth | symlink | 共享认证模块 |

---

## 注意事项

1. **数据库**: 生产环境使用 MySQL，开发环境可使用 SQLite (shm.db)
2. **端口**: 使用 8006 端口
3. **表前缀**: 所有表使用 `shm_` 前缀
4. **React 版本**: 使用 React 19 + Ant Design 6
