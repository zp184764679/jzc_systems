# SHM 出货管理系统 - Claude Code 项目上下文

## 系统概述

SHM (Shipment Management) 是 JZC 企业管理系统的出货管理模块，负责管理产品出货流程，包括出货单创建、物流跟踪、客户地址管理和交货要求管理。

### 核心功能
- 出货单管理（创建、编辑、状态跟踪）
- 出货明细管理
- 客户收货地址管理
- 交货要求/包装要求管理
- CRM 客户信息集成
- SCM 库存信息集成

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 8006 |
| 前端路径 | `/shm/` |
| API路径 | `/shm/api/` |
| PM2服务名 | shm-backend |
| 数据库 | cncplan |
| 健康检查 | `curl http://127.0.0.1:8006/api/health` |

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
│   ├── app.py                       # Flask 应用入口
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
│   │   ├── shipments.py             # 出货单路由
│   │   ├── addresses.py             # 地址管理路由
│   │   ├── requirements.py          # 交货要求路由
│   │   ├── base_data.py             # 基础数据路由
│   │   └── integration.py           # 系统集成路由
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
│   │   │   ├── ShipmentDetail.jsx   # 出货单详情
│   │   │   ├── AddressList.jsx      # 地址列表
│   │   │   └── RequirementList.jsx  # 交货要求列表
│   │   └── utils/
│   │       └── ssoAuth.js           # SSO 认证
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

---

## 本地开发

```bash
# 启动后端
cd SHM/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py

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
