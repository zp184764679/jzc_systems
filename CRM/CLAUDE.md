# CRM 客户关系管理系统 - Claude Code 项目上下文

## 系统概述

CRM 是 JZC 企业管理系统的客户关系管理模块，负责客户信息管理、订单跟踪，为其他系统提供客户数据支持。

**部署状态**: 未部署

### 核心功能
- 客户基本信息管理
- 客户联系人管理
- 客户结算信息管理
- 客户订单跟踪
- 交货要求管理
- 为其他系统提供客户查询 API

---

## 计划部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 8002 |
| 前端路径 | `/crm/` |
| API路径 | `/crm/api/` |
| PM2服务名 | crm-backend |
| 数据库 | cncplan |

---

## 技术栈

### 前端
- React 19.2.0
- Vite
- Ant Design 5.28.1

### 后端
- Flask 3.0.0 + Flask-CORS 4.0.0
- Flask-SQLAlchemy 3.1.1 + Flask-Migrate 4.0.5
- PyMySQL 1.1.0
- SQLAlchemy >= 2.0.36

---

## 目录结构

```
CRM/
├── backend/
│   ├── main.py                      # Flask 应用入口
│   ├── requirements.txt             # Python 依赖
│   ├── app/
│   │   ├── __init__.py              # Flask 应用工厂
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── customer.py          # 客户模型
│   │   │   ├── core.py              # 核心模型
│   │   │   └── base_data.py         # 基础数据
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # 认证路由
│   │   │   ├── customers.py         # 客户路由
│   │   │   ├── orders.py            # 订单路由
│   │   │   ├── base_data.py         # 基础数据路由
│   │   │   └── integration.py       # 系统集成路由
│   │   └── services/
│   │       ├── __init__.py
│   │       └── hr_service.py        # HR 服务
│   ├── import_customers.py          # 客户导入脚本
│   ├── crm.db                       # SQLite 数据库（开发）
│   └── venv/
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # 仪表盘
│   │   │   ├── CustomerList.jsx     # 客户列表
│   │   │   ├── CustomerDetail.jsx   # 客户详情
│   │   │   └── orders/
│   │   │       ├── OrderList.jsx    # 订单列表
│   │   │       └── OrderNew.jsx     # 新建订单
│   │   ├── services/
│   │   │   └── api.js
│   │   └── utils/
│   │       └── ssoAuth.js
│   └── dist/
└── package.json
```

---

## API 路由清单

### 客户 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/customers` | 获取客户列表（分页搜索） |
| GET | `/api/customers/<id>` | 获取客户详情 |
| POST | `/api/customers` | 创建客户 |
| PUT | `/api/customers/<id>` | 更新客户 |
| DELETE | `/api/customers/<id>` | 删除客户 |
| GET | `/api/customers/search` | 搜索客户 |

### 订单 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/orders` | 获取订单列表 |
| GET | `/api/orders/<id>` | 获取订单详情 |
| POST | `/api/orders` | 创建订单 |
| PUT | `/api/orders/<id>` | 更新订单 |

### 集成 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/integration/customers` | 供其他系统调用的客户查询 |

---

## 数据模型

### Customer 客户

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| seq_no | Integer | 序号 |
| code | String(64) | 客户代码 |
| short_name | String(128) | 客户简称 |
| name | String(255) | 客户全称 |
| currency_default | String(16) | 默认币种 |
| tax_points | Integer | 含税点数 |
| settlement_cycle_days | Integer | 结算周期（天） |
| settlement_method | String(64) | 结算方式 |
| statement_day | Integer | 对账日 |
| address | String(512) | 公司地址 |
| contacts | JSON | 联系人列表 |
| shipping_method | String(64) | 出货方式 |
| need_customs | Boolean | 是否报关 |
| order_method | String(64) | 接单方式 |
| delivery_requirements | String(512) | 送货要求 |
| delivery_address | String(512) | 送货地址 |
| remark | String(1024) | 备注 |

---

## 本地开发

```bash
# 启动后端
cd CRM/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py

# 启动前端
cd CRM/frontend
npm install
npm run dev
```

---

## 已完成功能

- [x] 客户 CRUD
- [x] 客户搜索与分页
- [x] 客户联系人管理
- [x] 结算信息管理
- [x] 交货要求管理
- [ ] 订单管理（开发中）
- [ ] 客户跟进记录
- [ ] 报表统计

---

## 与其他系统的集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| 报价 | API 调用 | 报价系统获取客户信息 |
| 采购 | API 调用 | 采购系统获取供应商信息 |
| SHM | API 调用 | 出货系统获取客户/地址信息 |
| HR | API 调用 | 获取业务员信息 |

---

## 注意事项

1. **未部署**: CRM 系统尚未部署到生产环境
2. **数据库**: 开发使用 SQLite，生产需配置 MySQL
3. **端口**: 计划使用 8002 端口
4. **客户数据**: 已导入历史客户数据
