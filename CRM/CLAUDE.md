# CRM 客户关系管理系统 - Claude Code 项目上下文

## 系统概述

CRM 是 JZC 企业管理系统的客户关系管理模块，负责客户信息管理、订单跟踪，为其他系统提供客户数据支持。

**部署状态**: 未部署

### 核心功能
- 客户基本信息管理
- 客户联系人管理
- 客户结算信息管理
- 订单管理（完整工作流、审批流程）
- 订单报表统计
- 订单导入导出
- 交货要求管理
- 销售机会/商机管理
- 客户跟进记录
- 销售漏斗看板
- 合同管理
- 客户分析报表（概览、等级分布、增长趋势、销售排行、活跃度分析）
- 为其他系统提供客户查询 API

---

## 计划部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 8002 |
| 前端端口(dev) | 6004 |
| 前端路径 | `/crm/` |
| API路径 | `/crm/api/` |
| PM2服务名 | crm-backend |
| 数据库 | cncplan |
| 健康检查 | `curl http://127.0.0.1:8002/health` |

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
│   │   │   ├── base_data.py         # 基础数据
│   │   │   ├── sales.py             # 销售机会/跟进记录模型
│   │   │   └── contract.py          # 合同管理模型 (新)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # 认证路由
│   │   │   ├── customers.py         # 客户路由
│   │   │   ├── orders.py            # 订单主路由
│   │   │   ├── order_workflow.py    # 订单工作流 API
│   │   │   ├── order_reports.py     # 订单报表 API
│   │   │   ├── order_import.py      # 订单导入导出 API
│   │   │   ├── base_data.py         # 基础数据路由
│   │   │   ├── integration.py       # 系统集成路由
│   │   │   ├── opportunities.py     # 销售机会路由
│   │   │   ├── follow_ups.py        # 跟进记录路由
│   │   │   ├── contracts.py         # 合同管理路由
│   │   │   └── customer_reports.py  # 客户分析报表路由
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── hr_service.py        # HR 服务
│   │       └── data_permission.py   # 数据权限控制服务
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
│   │   │   ├── OpportunityList.jsx  # 销售机会列表
│   │   │   ├── SalesPipeline.jsx    # 销售漏斗看板
│   │   │   ├── ContractList.jsx     # 合同管理页面
│   │   │   ├── CustomerReports.jsx  # 客户分析报表
│   │   │   └── orders/
│   │   │       ├── OrderList.jsx    # 订单列表（含工作流、审批、导入）
│   │   │       ├── OrderNew.jsx     # 新建订单
│   │   │       └── OrderReports.jsx # 订单报表统计
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
| DELETE | `/api/orders/<id>` | 删除订单（仅草稿） |
| POST | `/api/orders/query` | 订单高级查询 |

### 订单工作流 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/orders/<id>/submit` | 提交审批 |
| POST | `/api/orders/<id>/approve` | 审批通过 |
| POST | `/api/orders/<id>/reject` | 拒绝 |
| POST | `/api/orders/<id>/return` | 退回修改 |
| POST | `/api/orders/<id>/cancel` | 取消订单 |
| POST | `/api/orders/<id>/start-production` | 开始生产 |
| POST | `/api/orders/<id>/start-delivery` | 开始交货 |
| POST | `/api/orders/<id>/complete` | 完成订单 |
| GET | `/api/orders/<id>/approvals` | 获取审批历史 |
| GET | `/api/orders/<id>/available-actions` | 获取可用操作 |
| GET | `/api/orders/pending-approval` | 待审批列表 |
| GET | `/api/orders/statistics` | 订单统计 |
| GET | `/api/orders/enums` | 状态和操作枚举 |

### 订单报表 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/orders/reports/summary` | 订单汇总统计 |
| GET | `/api/orders/reports/by-customer` | 按客户统计 |
| GET | `/api/orders/reports/by-status` | 按状态分布 |
| GET | `/api/orders/reports/trend` | 订单趋势（支持按日/周/月） |
| GET | `/api/orders/reports/delivery-performance` | 交付绩效 |
| GET | `/api/orders/reports/product-ranking` | 产品销量排行 |

### 订单导入导出 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/orders/export` | 导出订单 Excel |
| GET | `/api/orders/export/template` | 下载导入模板 |
| POST | `/api/orders/import/preview` | 预览导入数据 |
| POST | `/api/orders/import` | 批量导入订单 |

### 销售机会 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/opportunities` | 获取机会列表（分页筛选） |
| GET | `/api/opportunities/<id>` | 获取机会详情（含阶段历史、跟进记录） |
| POST | `/api/opportunities` | 创建机会 |
| PUT | `/api/opportunities/<id>` | 更新机会 |
| PUT | `/api/opportunities/<id>/stage` | 阶段推进 |
| DELETE | `/api/opportunities/<id>` | 删除机会 |
| GET | `/api/opportunities/pipeline` | 销售漏斗数据 |
| GET | `/api/opportunities/statistics` | 销售统计 |
| GET | `/api/opportunities/stages` | 阶段和优先级定义 |

### 跟进记录 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/follow-ups` | 获取跟进记录列表 |
| GET | `/api/follow-ups/<id>` | 获取单条跟进记录 |
| POST | `/api/follow-ups` | 创建跟进记录 |
| PUT | `/api/follow-ups/<id>` | 更新跟进记录 |
| DELETE | `/api/follow-ups/<id>` | 删除跟进记录 |
| GET | `/api/follow-ups/customer/<id>/timeline` | 客户跟进时间线 |
| GET | `/api/follow-ups/pending` | 待跟进列表（逾期/今日/即将） |
| GET | `/api/follow-ups/statistics` | 跟进统计 |
| GET | `/api/follow-ups/types` | 跟进类型定义 |

### 合同管理 API (新)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/contracts` | 获取合同列表（分页筛选） |
| GET | `/api/contracts/<id>` | 获取合同详情（含明细、审批记录） |
| POST | `/api/contracts` | 创建合同 |
| PUT | `/api/contracts/<id>` | 更新合同（仅草稿） |
| DELETE | `/api/contracts/<id>` | 删除合同（仅草稿） |
| POST | `/api/contracts/<id>/submit` | 提交审批 |
| POST | `/api/contracts/<id>/approve` | 审批通过 |
| POST | `/api/contracts/<id>/reject` | 审批拒绝 |
| POST | `/api/contracts/<id>/activate` | 激活合同 |
| POST | `/api/contracts/<id>/terminate` | 终止合同 |
| GET | `/api/contracts/expiring` | 即将到期合同 |
| GET | `/api/contracts/statistics` | 合同统计 |
| GET | `/api/contracts/from-opportunity/<id>` | 从机会创建合同 |
| GET | `/api/contracts/types` | 类型和状态定义 |

### 客户分析报表 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/customers/reports/overview` | 客户概览统计（总数、本月新增、重点客户等） |
| GET | `/api/customers/reports/grade-distribution` | 客户等级分布（VIP/金牌/银牌/普通） |
| GET | `/api/customers/reports/growth-trend` | 客户增长趋势（按日/周/月/年） |
| GET | `/api/customers/reports/sales-ranking` | 客户销售额排行（支持日期筛选） |
| GET | `/api/customers/reports/activity-analysis` | 客户活跃度分析（活跃/沉睡/新增/流失） |
| GET | `/api/customers/reports/transaction-frequency` | 交易频次分布 |
| GET | `/api/customers/reports/settlement-distribution` | 结算方式分布 |
| GET | `/api/customers/reports/currency-distribution` | 币种分布 |
| GET | `/api/customers/reports/opportunity-conversion` | 商机转化分析 |
| GET | `/api/customers/reports/comprehensive` | 综合报表 |

### 数据权限 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/customers/my` | 获取我负责的客户列表 |
| GET | `/api/customers/department/<id>` | 获取指定部门的客户列表 |
| POST | `/api/customers/assign` | 批量分配客户给指定负责人（仅管理员） |
| GET | `/api/customers/permission-info` | 获取当前用户的数据权限信息 |

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

### SalesOpportunity 销售机会 (新)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| opportunity_no | String(32) | 机会编号（自动生成 OPP-YYYYMMDD-XXXX） |
| name | String(200) | 机会名称 |
| customer_id | Integer | 客户ID |
| customer_name | String(200) | 客户名称（冗余） |
| stage | String(32) | 阶段 (lead/qualified/proposal/negotiation/closed_won/closed_lost) |
| expected_amount | Decimal(14,2) | 预计金额 |
| currency | String(8) | 币种 |
| probability | Integer | 成交概率 (0-100) |
| weighted_amount | Decimal(14,2) | 加权金额 |
| expected_close_date | Date | 预计成交日期 |
| actual_close_date | Date | 实际成交日期 |
| owner_id | Integer | 负责人ID |
| owner_name | String(64) | 负责人姓名 |
| priority | String(16) | 优先级 (low/medium/high/urgent) |
| source | String(64) | 机会来源 |
| product_interest | Text | 意向产品 |
| competitors | Text | 竞争对手 |
| description | Text | 详细描述 |
| win_reason | Text | 赢单原因 |
| loss_reason | Text | 丢单原因 |
| next_follow_up_date | Date | 下次跟进日期 |
| next_follow_up_note | String(500) | 下次跟进内容 |

### FollowUpRecord 跟进记录 (新)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| customer_id | Integer | 客户ID |
| customer_name | String(200) | 客户名称（冗余） |
| opportunity_id | Integer | 关联机会ID（可选） |
| follow_up_type | String(32) | 跟进方式 (phone/visit/email/wechat/meeting/quotation/sample/other) |
| follow_up_date | DateTime | 跟进时间 |
| subject | String(200) | 主题 |
| content | Text | 跟进内容 |
| result | Text | 跟进结果 |
| contact_name | String(64) | 联系人 |
| contact_phone | String(32) | 联系电话 |
| contact_role | String(64) | 联系人职位 |
| next_follow_up_date | Date | 下次跟进日期 |
| next_follow_up_note | String(500) | 下次跟进内容 |
| owner_id | Integer | 跟进人ID |
| owner_name | String(64) | 跟进人姓名 |
| attachments | JSON | 附件列表 |

### Contract 合同 (新)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| contract_no | String(32) | 合同编号（自动生成 CON-YYYYMMDD-XXXX） |
| name | String(200) | 合同名称 |
| contract_type | String(32) | 合同类型 (sales/framework/service/nda/other) |
| status | String(32) | 状态 (draft/pending/approved/active/expired/terminated) |
| customer_id | Integer | 客户ID |
| customer_name | String(200) | 客户名称（冗余） |
| opportunity_id | Integer | 关联机会ID（可选） |
| total_amount | Decimal(14,2) | 合同总金额 |
| currency | String(8) | 币种 |
| tax_rate | Decimal(5,2) | 税率 (%) |
| start_date | Date | 生效日期 |
| end_date | Date | 到期日期 |
| sign_date | Date | 签订日期 |
| our_signatory | String(64) | 我方签约人 |
| customer_signatory | String(64) | 客户签约人 |
| payment_terms | Text | 付款条款 |
| delivery_terms | Text | 交货条款 |
| special_terms | Text | 特殊条款 |
| attachments | JSON | 附件列表 |
| owner_id | Integer | 负责人ID |
| owner_name | String(64) | 负责人姓名 |
| remark | Text | 备注 |

### ContractItem 合同明细 (新)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| contract_id | Integer | 合同ID |
| product_name | String(200) | 产品/服务名称 |
| specification | String(500) | 规格型号 |
| quantity | Decimal(12,2) | 数量 |
| unit | String(32) | 单位 |
| unit_price | Decimal(14,4) | 单价 |
| amount | Decimal(14,2) | 金额 |
| delivery_date | Date | 交货日期 |
| remark | String(500) | 备注 |

### ContractApproval 合同审批

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| contract_id | Integer | 合同ID |
| approver_id | Integer | 审批人ID |
| approver_name | String(64) | 审批人姓名 |
| status | String(32) | 审批状态 (pending/approved/rejected) |
| comment | Text | 审批意见 |
| approved_at | DateTime | 审批时间 |

### Order 订单（扩展）

| 字段 | 类型 | 说明 |
|------|------|------|
| status | String(32) | 状态 (draft/pending/confirmed/in_production/in_delivery/completed/cancelled) |
| submitted_at | DateTime | 提交时间 |
| confirmed_at | DateTime | 确认时间 |
| completed_at | DateTime | 完成时间 |
| submitted_by | Integer | 提交人ID |
| confirmed_by | Integer | 确认人ID |

**状态流转规则**:
```
[草稿] --提交--> [待审批] --审批通过--> [已确认]
   ↑                |                      |
   |              拒绝/退回               开始生产
   |                ↓                      ↓
   +----------<-[草稿]              [生产中]
                                          |
                                       开始交货
                                          ↓
                                     [交货中]
                                          |
                                        完成
                                          ↓
                                     [已完成]

任意状态 --取消--> [已取消]（仅限草稿/待审批/已确认）
```

### OrderApproval 订单审批

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_id | Integer | 订单ID |
| action | String(32) | 操作类型 (submit/approve/reject/return/cancel/start_production/start_delivery/complete) |
| from_status | String(32) | 原状态 |
| to_status | String(32) | 新状态 |
| operator_id | Integer | 操作人ID |
| operator_name | String(64) | 操作人姓名 |
| comment | Text | 审批意见/备注 |
| created_at | DateTime | 操作时间 |

---

## 前端页面/组件

### 页面列表

| 页面 | 路径 | 说明 |
|------|------|------|
| Dashboard | `/crm/` | 仪表盘 - CRM 概览统计 |
| CustomerList | `/crm/customers` | 客户列表 - 客户管理主页 |
| CustomerDetail | `/crm/customers/:id` | 客户详情 - 联系人、结算、交货信息 |
| OpportunityList | `/crm/opportunities` | 销售机会列表 |
| SalesPipeline | `/crm/pipeline` | 销售漏斗看板 |
| ContractList | `/crm/contracts` | 合同管理列表 |
| CustomerReports | `/crm/reports` | 客户分析报表 |
| OrderList | `/crm/orders` | 订单列表（含工作流、审批） |
| OrderNew | `/crm/orders/new` | 新建订单 |
| OrderReports | `/crm/orders/reports` | 订单报表统计 |

### 核心组件

| 组件 | 说明 |
|------|------|
| CustomerForm | 客户新建/编辑表单 |
| ContactEditor | 联系人管理组件 |
| SettlementEditor | 结算信息编辑组件 |
| OpportunityCard | 销售机会卡片（拖拽看板） |
| FollowUpTimeline | 跟进记录时间线 |
| ContractApproval | 合同审批流程组件 |
| OrderWorkflow | 订单状态流转组件 |
| ReportChart | 报表图表组件 |

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
- [x] 销售机会管理
- [x] 客户跟进记录
- [x] 销售漏斗看板
- [x] 阶段推进与历史
- [x] 销售统计
- [x] 合同管理
- [x] 合同审批流程
- [x] 合同到期提醒
- [x] 订单管理（完整工作流）
- [x] 订单审批流程
- [x] 订单状态统计
- [x] 订单报表（汇总、客户分析、趋势、交付绩效、产品排行）
- [x] 订单 Excel 导入导出
- [x] 客户分析报表（概览、等级分布、增长趋势、销售排行、活跃度、商机转化）
- [x] 数据权限控制（基于角色的客户数据访问控制、客户分配、我的客户）

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
