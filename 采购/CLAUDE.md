# 采购系统 (Caigou) - Claude Code 项目上下文

## 系统概述

采购系统是 JZC 企业管理系统的采购管理模块，覆盖完整的采购流程：采购申请(PR) → 询价单(RFQ) → 供应商报价 → 采购订单(PO) → 收货 → 发票管理。支持企业微信集成和审批流程。

**部署状态**: 已部署

### 核心功能
- 采购申请 (PR) 管理与审批
- 询价单 (RFQ) 创建与发送
- 供应商管理
- 供应商报价与选标
- 采购订单 (PO) 管理
- 收货管理 (GRN)
- 发票管理
- **采购合同管理**（新）
  - 合同创建与审批
  - 合同执行跟踪
  - 即将到期预警
  - 合同统计分析
- **采购预算管理**（新）
  - 年度/季度/月度预算
  - 预算审批流程
  - 预算使用跟踪（预留/消费/释放/调整）
  - 预警阈值管理
  - 预算统计分析
- **付款管理**（新）
  - 付款申请与审批
  - 付款计划管理
  - 多种付款方式支持
  - 逾期预警
  - 付款统计分析
- 审批流程
- 企业微信消息通知
- AI 物料分类（可选）

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 5001 |
| 前端端口(dev) | 5000 |
| 前端路径 | `/caigou/` |
| API路径 | `/caigou/api/` |
| PM2服务名 | caigou-backend |
| 数据库 | caigou |
| 健康检查 | `curl http://127.0.0.1:5001/health` |

---

## 技术栈

### 前端
- React 18.3.1
- Vite
- Tailwind CSS
- 自定义 Hooks
- Context API

### 后端
- Flask 3.0.0 + Flask-CORS
- Flask-SQLAlchemy 3.0+ + Flask-Migrate
- Flask-Marshmallow (序列化)
- Celery 5.0+ + Redis (异步任务)
- wechatpy (企业微信集成)
- PyMySQL + SQLAlchemy 2.0+

---

## 目录结构

```
采购/
├── backend/
│   ├── main.py                          # Flask 应用入口
│   ├── requirements.txt                 # Python 依赖
│   ├── extensions.py                    # Flask 扩展初始化
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                      # 用户模型
│   │   ├── pr.py                        # 采购申请
│   │   ├── pr_item.py                   # 采购申请明细
│   │   ├── pr_counter.py                # PR 编号计数器
│   │   ├── rfq.py                       # 询价单
│   │   ├── rfq_item.py                  # 询价单明细
│   │   ├── rfq_notification_task.py     # RFQ 通知任务
│   │   ├── supplier.py                  # 供应商
│   │   ├── supplier_category.py         # 供应商分类
│   │   ├── supplier_quote.py            # 供应商报价
│   │   ├── supplier_nudge.py            # 供应商催促
│   │   ├── purchase_order.py            # 采购订单
│   │   ├── receipt.py                   # 收货记录
│   │   ├── invoice.py                   # 发票
│   │   ├── price_history.py             # 价格历史
│   │   ├── operation_history.py         # 操作历史
│   │   ├── notification.py              # 通知
│   │   └── supplier_evaluation.py       # 供应商评估
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py               # 认证路由
│   │   ├── user_routes.py               # 用户管理
│   │   ├── pr/                          # PR 相关路由
│   │   │   ├── __init__.py
│   │   │   ├── create.py                # 创建 PR
│   │   │   ├── query.py                 # 查询 PR
│   │   │   ├── approval.py              # PR 审批
│   │   │   ├── search.py                # PR 搜索
│   │   │   └── statistics.py            # PR 统计
│   │   ├── rfq/                         # RFQ 相关路由
│   │   │   ├── create_po.py             # 从 RFQ 创建 PO
│   │   ├── rfq_routes.py                # 询价单路由
│   │   ├── supplier_admin/              # 供应商管理
│   │   │   ├── __init__.py
│   │   │   ├── supplier_routes.py       # 供应商 CRUD
│   │   │   ├── invoice_routes.py        # 供应商发票
│   │   │   ├── serializers.py           # 序列化
│   │   │   └── utils.py                 # 工具函数
│   │   ├── supplier_public_routes.py    # 供应商公开接口
│   │   ├── supplier_self_routes.py      # 供应商自服务
│   │   ├── supplier_quote_routes.py     # 供应商报价
│   │   ├── supplier_category_routes.py  # 供应商分类
│   │   ├── purchase_order_routes.py     # 采购订单
│   │   ├── receipt_routes.py            # 收货管理
│   │   ├── grn_routes.py                # GRN 路由
│   │   ├── invoice_routes.py            # 发票管理
│   │   ├── notification_routes.py       # 通知
│   │   ├── history_routes.py            # 历史记录
│   │   ├── integration_routes.py        # 系统集成
│   │   ├── ai_routes.py                 # AI 功能
│   │   ├── wechat_callback_routes.py    # 企业微信回调
│   │   ├── wework_oauth_routes.py       # 企业微信 OAuth
│   │   └── supplier_evaluation_routes.py # 供应商评估
│   ├── services/                        # 业务服务
│   ├── middleware/                      # 中间件
│   ├── constants/                       # 常量定义
│   ├── migrations/                      # 数据库迁移
│   ├── logs/                            # 日志
│   └── .venv/
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/
│   │   │   ├── index.js                 # API 客户端
│   │   │   ├── http.js                  # HTTP 工具
│   │   │   └── endpoints.js             # API 端点
│   │   ├── auth/
│   │   │   └── AuthContext.jsx          # 认证上下文
│   │   ├── components/
│   │   │   ├── NavBar.jsx               # 导航栏
│   │   │   ├── ProtectedRoute.jsx       # 路由保护
│   │   │   ├── MaterialRequestForm.jsx  # 物料申请表单
│   │   │   ├── RFQSendPanel.jsx         # RFQ 发送面板
│   │   │   ├── ManualQuoteModal.jsx     # 手动报价
│   │   │   ├── PrAiAssist.jsx           # PR AI 助手
│   │   │   ├── ApprovalCenter/          # 审批中心组件
│   │   │   ├── admin/                   # 管理员组件
│   │   │   └── ui/                      # 通用 UI 组件
│   │   ├── pages/
│   │   │   ├── Login.jsx                # 登录
│   │   │   ├── RequestDetail.jsx        # 申请详情
│   │   │   ├── FillPricePage.jsx        # 填报价格
│   │   │   ├── ApprovalCenter.jsx       # 审批中心
│   │   │   ├── AdminApprovalCenter.jsx  # 管理员审批
│   │   │   ├── AdminUsers.jsx           # 用户管理
│   │   │   ├── InvoiceManagement.jsx    # 发票管理
│   │   │   └── SupplierEvaluation.jsx   # 供应商评估
│   │   ├── hooks/
│   │   │   ├── useApprovalList.js       # 审批列表 Hook
│   │   │   ├── useSupplierAdmin.js      # 供应商管理 Hook
│   │   │   ├── useSupplierQuotes.js     # 供应商报价 Hook
│   │   │   ├── useSupplierStats.js      # 供应商统计 Hook
│   │   │   ├── useSupplierInvoices.js   # 供应商发票 Hook
│   │   │   └── useQuoteLibrary.js       # 报价库 Hook
│   │   ├── constants/
│   │   │   ├── categories.js            # 物料分类
│   │   │   ├── departments.js           # 部门
│   │   │   └── roles.js                 # 角色
│   │   └── utils/
│   │       └── formatters.js            # 格式化工具
│   └── dist/
└── package.json
```

---

## API 路由清单

### 采购申请 (PR) API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/pr` | 获取 PR 列表 |
| GET | `/api/pr/<id>` | 获取 PR 详情 |
| POST | `/api/pr` | 创建 PR |
| PUT | `/api/pr/<id>` | 更新 PR |
| DELETE | `/api/pr/<id>` | 删除 PR |
| POST | `/api/pr/<id>/submit` | 提交审批 |
| POST | `/api/pr/<id>/approve` | 审批通过 |
| POST | `/api/pr/<id>/reject` | 审批拒绝 |
| GET | `/api/pr/statistics` | PR 统计数据 |
| GET | `/api/pr/search` | 搜索 PR |

### 询价单 (RFQ) API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/rfq` | 获取 RFQ 列表 |
| GET | `/api/rfq/<id>` | 获取 RFQ 详情 |
| POST | `/api/rfq` | 创建 RFQ |
| POST | `/api/rfq/<id>/send` | 发送给供应商 |
| POST | `/api/rfq/<id>/create-po` | 从 RFQ 创建 PO |

### 供应商 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/suppliers` | 获取供应商列表 |
| GET | `/api/suppliers/<id>` | 获取供应商详情 |
| POST | `/api/suppliers` | 创建供应商 |
| PUT | `/api/suppliers/<id>` | 更新供应商 |
| DELETE | `/api/suppliers/<id>` | 删除供应商 |
| GET | `/api/supplier-categories` | 获取供应商分类 |

### 供应商报价 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/supplier-quotes` | 获取报价列表 |
| POST | `/api/supplier-quotes` | 提交报价 |
| PUT | `/api/supplier-quotes/<id>` | 更新报价 |
| POST | `/api/supplier-quotes/<id>/select` | 选定报价 |

### 采购订单 (PO) API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/purchase-orders` | 获取 PO 列表 |
| GET | `/api/purchase-orders/<id>` | 获取 PO 详情 |
| POST | `/api/purchase-orders` | 创建 PO |
| PUT | `/api/purchase-orders/<id>` | 更新 PO |
| POST | `/api/purchase-orders/<id>/confirm` | 确认 PO |

### 收货 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/receipts` | 获取收货列表 |
| POST | `/api/receipts` | 创建收货记录 |
| GET | `/api/grn` | 获取 GRN 列表 |

### 发票 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/invoices` | 获取发票列表 |
| POST | `/api/invoices` | 创建发票 |
| PUT | `/api/invoices/<id>` | 更新发票 |
| POST | `/api/invoices/<id>/verify` | 验证发票 |

### 企业微信 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/wework/oauth` | 企业微信 OAuth |
| POST | `/api/wework/callback` | 企业微信回调 |

### 供应商评估 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/evaluation-templates` | 获取评估模板列表 |
| GET | `/api/v1/evaluation-templates/<id>` | 获取模板详情 |
| POST | `/api/v1/evaluation-templates` | 创建评估模板 |
| PUT | `/api/v1/evaluation-templates/<id>` | 更新评估模板 |
| DELETE | `/api/v1/evaluation-templates/<id>` | 删除评估模板 |
| GET | `/api/v1/evaluation-templates/options` | 获取模板选项 |
| POST | `/api/v1/evaluation-templates/init-default` | 初始化默认模板 |
| GET | `/api/v1/supplier-evaluations` | 获取评估列表 |
| GET | `/api/v1/supplier-evaluations/<id>` | 获取评估详情 |
| POST | `/api/v1/supplier-evaluations` | 创建评估 |
| PUT | `/api/v1/supplier-evaluations/<id>` | 更新评估 |
| DELETE | `/api/v1/supplier-evaluations/<id>` | 删除评估 |
| POST | `/api/v1/supplier-evaluations/<id>/start` | 开始评估 |
| POST | `/api/v1/supplier-evaluations/<id>/complete` | 完成评估 |
| POST | `/api/v1/supplier-evaluations/<id>/cancel` | 取消评估 |
| GET | `/api/v1/supplier-evaluations/statistics/summary` | 统计概览 |
| GET | `/api/v1/supplier-evaluations/statistics/supplier-ranking` | 供应商排名 |
| GET | `/api/v1/supplier-evaluations/enums` | 获取枚举值 |

### 采购合同 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/contracts` | 获取合同列表 |
| GET | `/api/v1/contracts/<id>` | 获取合同详情 |
| POST | `/api/v1/contracts` | 创建合同 |
| PUT | `/api/v1/contracts/<id>` | 更新合同 |
| DELETE | `/api/v1/contracts/<id>` | 删除合同 |
| POST | `/api/v1/contracts/<id>/submit` | 提交审批 |
| POST | `/api/v1/contracts/<id>/approve` | 审批通过 |
| POST | `/api/v1/contracts/<id>/reject` | 拒绝/退回 |
| POST | `/api/v1/contracts/<id>/activate` | 激活合同 |
| POST | `/api/v1/contracts/<id>/complete` | 完成合同 |
| POST | `/api/v1/contracts/<id>/cancel` | 取消合同 |
| POST | `/api/v1/contracts/<id>/execute` | 登记执行 |
| POST | `/api/v1/contracts/<id>/attachment` | 上传附件 |
| GET | `/api/v1/contracts/statistics` | 合同统计 |
| GET | `/api/v1/contracts/expiring` | 即将到期合同 |
| GET | `/api/v1/contracts/by-supplier/<supplier_id>` | 供应商合同 |
| GET | `/api/v1/contracts/enums` | 获取枚举值 |

### 采购预算 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/budgets` | 获取预算列表 |
| GET | `/api/v1/budgets/<id>` | 获取预算详情 |
| POST | `/api/v1/budgets` | 创建预算 |
| PUT | `/api/v1/budgets/<id>` | 更新预算 |
| DELETE | `/api/v1/budgets/<id>` | 删除预算 |
| POST | `/api/v1/budgets/<id>/submit` | 提交审批 |
| POST | `/api/v1/budgets/<id>/approve` | 审批通过 |
| POST | `/api/v1/budgets/<id>/reject` | 拒绝/退回 |
| POST | `/api/v1/budgets/<id>/activate` | 激活预算 |
| POST | `/api/v1/budgets/<id>/close` | 关闭预算 |
| POST | `/api/v1/budgets/<id>/reserve` | 预留预算 |
| POST | `/api/v1/budgets/<id>/consume` | 消耗预算 |
| POST | `/api/v1/budgets/<id>/release` | 释放预算 |
| POST | `/api/v1/budgets/<id>/adjust` | 调整预算 |
| GET | `/api/v1/budgets/<id>/usage` | 获取使用记录 |
| GET | `/api/v1/budgets/statistics` | 预算统计 |
| GET | `/api/v1/budgets/warnings` | 预警预算列表 |
| GET | `/api/v1/budgets/by-department` | 按部门查询 |
| POST | `/api/v1/budgets/check-availability` | 检查预算可用性 |
| GET | `/api/v1/budgets/years` | 获取年份列表 |
| GET | `/api/v1/budgets/departments` | 获取部门列表 |
| GET | `/api/v1/budgets/enums` | 获取枚举值 |

### 付款管理 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/payments` | 获取付款列表 |
| GET | `/api/v1/payments/<id>` | 获取付款详情 |
| POST | `/api/v1/payments` | 创建付款 |
| PUT | `/api/v1/payments/<id>` | 更新付款 |
| DELETE | `/api/v1/payments/<id>` | 删除付款 |
| POST | `/api/v1/payments/<id>/submit` | 提交审批 |
| POST | `/api/v1/payments/<id>/approve` | 审批通过 |
| POST | `/api/v1/payments/<id>/reject` | 拒绝/退回 |
| POST | `/api/v1/payments/<id>/confirm` | 确认付款 |
| POST | `/api/v1/payments/<id>/cancel` | 取消付款 |
| GET | `/api/v1/payments/statistics` | 付款统计 |
| GET | `/api/v1/payments/overdue` | 逾期付款列表 |
| GET | `/api/v1/payments/due-soon` | 即将到期付款 |
| GET | `/api/v1/payments/by-supplier/<supplier_id>` | 供应商付款 |
| GET | `/api/v1/payments/enums` | 获取枚举值 |
| GET | `/api/v1/payment-plans` | 获取付款计划列表 |
| GET | `/api/v1/payment-plans/<id>` | 获取付款计划详情 |
| POST | `/api/v1/payment-plans` | 创建付款计划 |
| PUT | `/api/v1/payment-plans/<id>` | 更新付款计划 |
| DELETE | `/api/v1/payment-plans/<id>` | 删除付款计划 |

---

## 数据模型

### PR 采购申请

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| pr_number | String | PR 编号（唯一） |
| requester_id | Integer | 申请人 ID |
| department | String | 部门 |
| status | String | 状态（draft/pending/approved/rejected） |
| total_amount | Decimal | 总金额 |
| approval_date | DateTime | 审批日期 |
| items | Relationship | PR 明细 |

### RFQ 询价单

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| rfq_number | String | RFQ 编号 |
| pr_id | Integer | 关联 PR |
| status | String | 状态 |
| deadline | DateTime | 截止日期 |
| suppliers | Relationship | 发送的供应商 |

### Supplier 供应商

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String | 供应商编码 |
| name | String | 供应商名称 |
| contact | String | 联系人 |
| phone | String | 电话 |
| email | String | 邮箱 |
| category_id | Integer | 分类 ID |
| is_active | Boolean | 是否启用 |

### PurchaseOrder 采购订单

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| po_number | String | PO 编号 |
| supplier_id | Integer | 供应商 ID |
| rfq_id | Integer | 关联 RFQ |
| status | String | 状态 |
| total_amount | Decimal | 总金额 |

### SupplierQuote 供应商报价

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| rfq_id | Integer | RFQ ID |
| supplier_id | Integer | 供应商 ID |
| unit_price | Decimal | 单价 |
| quantity | Integer | 数量 |
| lead_time | Integer | 交期（天） |
| is_selected | Boolean | 是否选定 |

### EvaluationTemplate 评估模板

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| code | String(50) | 模板编码（唯一） |
| name | String(100) | 模板名称 |
| description | Text | 模板描述 |
| is_default | Boolean | 是否默认模板 |
| is_active | Boolean | 是否启用 |
| criteria | Relationship | 评估指标 |

### EvaluationCriteria 评估指标

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| template_id | BigInteger | 模板 ID |
| name | String(100) | 指标名称 |
| weight | Decimal | 权重（百分比） |
| description | Text | 指标描述 |
| sort_order | Integer | 排序 |
| max_score | Integer | 满分（默认100） |

### SupplierEvaluation 供应商评估

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| evaluation_no | String(50) | 评估编号（唯一） |
| supplier_id | BigInteger | 供应商 ID |
| supplier_name | String(200) | 供应商名称 |
| template_id | BigInteger | 模板 ID |
| period_type | Enum | 评估周期（月度/季度/年度/临时） |
| period_year | Integer | 评估年度 |
| period_value | Integer | 周期值 |
| status | Enum | 状态（待评估/评估中/已完成/已取消） |
| total_score | Decimal | 总分 |
| grade | Enum | 等级（A/B/C/D/E） |
| evaluator_id | BigInteger | 评估人 ID |
| evaluator_name | String(100) | 评估人姓名 |
| comment | Text | 评估意见 |
| scores | Relationship | 各指标得分 |

### EvaluationScore 评估得分

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| evaluation_id | BigInteger | 评估 ID |
| criteria_id | BigInteger | 指标 ID |
| criteria_name | String(100) | 指标名称 |
| criteria_weight | Decimal | 指标权重 |
| score | Decimal | 得分 |
| comment | Text | 评分说明 |

**评估等级标准**:
- A级 (优秀): 90-100分
- B级 (良好): 80-89分
- C级 (合格): 70-79分
- D级 (待改进): 60-69分
- E级 (不合格): <60分

### Contract 采购合同

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| contract_number | String(50) | 合同编号（唯一） |
| title | String(200) | 合同名称 |
| contract_type | String(20) | 类型（framework/single/long_term/annual） |
| supplier_id | BigInteger | 供应商 ID |
| supplier_name | String(200) | 供应商名称 |
| total_amount | Decimal | 合同总金额 |
| executed_amount | Decimal | 已执行金额 |
| currency | String(10) | 货币（默认CNY） |
| start_date | Date | 开始日期 |
| end_date | Date | 结束日期 |
| po_id | BigInteger | 关联 PO ID（可选） |
| payment_terms | Text | 付款条款 |
| delivery_terms | Text | 交付条款 |
| warranty_terms | Text | 质保条款 |
| status | String(30) | 状态 |
| attachment_path | String(500) | 附件路径 |

**合同状态**:
- draft: 草稿
- pending_approval: 待审批
- approved: 已批准
- active: 执行中
- completed: 已完成
- cancelled: 已取消
- expired: 已过期

### ContractItem 合同明细

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| contract_id | BigInteger | 合同 ID |
| material_code | String(50) | 物料编码 |
| material_name | String(200) | 物料名称 |
| specification | String(200) | 规格 |
| unit | String(20) | 单位 |
| quantity | Decimal | 数量 |
| unit_price | Decimal | 单价 |
| amount | Decimal | 金额 |
| executed_quantity | Decimal | 已执行数量 |

### Budget 采购预算

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| budget_code | String(50) | 预算编码（唯一） |
| name | String(200) | 预算名称 |
| description | Text | 描述 |
| period_type | String(20) | 周期类型（monthly/quarterly/annual） |
| year | Integer | 年度 |
| period_value | Integer | 周期值（月份1-12/季度1-4） |
| department | String(100) | 部门（空表示全公司） |
| total_amount | Decimal | 预算总额 |
| used_amount | Decimal | 已使用金额 |
| reserved_amount | Decimal | 预留金额 |
| currency | String(10) | 货币（默认CNY） |
| warning_threshold | Integer | 预警阈值（%） |
| critical_threshold | Integer | 严重阈值（%） |
| status | String(30) | 状态 |

**预算状态**:
- draft: 草稿
- pending_approval: 待审批
- approved: 已批准
- active: 执行中
- closed: 已关闭
- exceeded: 已超支

### BudgetCategory 预算分类

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| budget_id | BigInteger | 预算 ID |
| category_name | String(100) | 分类名称 |
| category_code | String(50) | 分类编码 |
| allocated_amount | Decimal | 分配金额 |
| used_amount | Decimal | 已使用金额 |

### BudgetUsage 预算使用记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| budget_id | BigInteger | 预算 ID |
| pr_id | BigInteger | 关联 PR ID |
| pr_number | String(50) | PR 编号 |
| usage_type | String(20) | 类型（reserve/consume/release/adjust） |
| amount | Decimal | 金额 |
| balance_after | Decimal | 操作后余额 |
| remarks | Text | 备注 |
| operated_by | BigInteger | 操作人 ID |
| operated_by_name | String(100) | 操作人姓名 |

**使用类型**:
- reserve: 预留（PR提交时）
- consume: 消耗（PO确认时）
- release: 释放（PR取消时）
- adjust: 调整（追加/减少）

### Payment 付款

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| payment_number | String(50) | 付款编号（唯一） |
| supplier_id | BigInteger | 供应商 ID |
| supplier_name | String(200) | 供应商名称 |
| po_id | BigInteger | 关联 PO ID（可选） |
| po_number | String(50) | PO 编号 |
| invoice_id | BigInteger | 关联发票 ID（可选） |
| invoice_number | String(50) | 发票号码 |
| contract_id | BigInteger | 关联合同 ID（可选） |
| contract_number | String(50) | 合同编号 |
| payment_type | String(20) | 付款类型 |
| payment_method | String(20) | 付款方式 |
| amount | Decimal | 付款金额 |
| tax_amount | Decimal | 税额 |
| total_amount | Decimal | 总金额（含税） |
| currency | String(10) | 货币（默认CNY） |
| due_date | Date | 应付日期 |
| payment_date | Date | 实际付款日期 |
| bank_name | String(100) | 收款银行 |
| bank_account | String(50) | 收款账号 |
| bank_account_name | String(100) | 收款户名 |
| status | String(30) | 状态 |
| remarks | Text | 备注 |

**付款状态**:
- draft: 草稿
- pending_approval: 待审批
- approved: 已批准
- paid: 已付款
- cancelled: 已取消
- rejected: 已拒绝

**付款类型**:
- advance: 预付款
- progress: 进度款
- final: 尾款
- deposit: 定金
- other: 其他

**付款方式**:
- bank_transfer: 银行转账
- check: 支票
- cash: 现金
- letter_of_credit: 信用证
- other: 其他

### PaymentPlan 付款计划

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| po_id | BigInteger | 关联 PO ID |
| po_number | String(50) | PO 编号 |
| contract_id | BigInteger | 关联合同 ID |
| contract_number | String(50) | 合同编号 |
| supplier_id | BigInteger | 供应商 ID |
| supplier_name | String(200) | 供应商名称 |
| plan_name | String(200) | 计划名称 |
| payment_type | String(20) | 付款类型 |
| percentage | Decimal | 付款比例（%） |
| amount | Decimal | 计划金额 |
| due_date | Date | 计划付款日期 |
| condition | String(200) | 付款条件 |
| payment_id | BigInteger | 关联付款 ID |
| actual_amount | Decimal | 实际付款金额 |
| status | String(20) | 状态 |

**计划状态**:
- pending: 待付
- partial: 部分付款
- paid: 已付

---

## 采购流程

```
1. 创建 PR (采购申请)
       ↓
2. 提交审批 → 审批通过/拒绝
       ↓
3. 创建 RFQ (询价单)
       ↓
4. 发送给供应商 → 供应商报价
       ↓
5. 比价选标
       ↓
6. 创建 PO (采购订单)
       ↓
7. 供应商确认
       ↓
8. 收货 (GRN)
       ↓
9. 发票管理
```

---

## 本地开发

```bash
# 启动后端
cd 采购/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py

# 启动 Celery Worker
celery -A app.celery worker --loglevel=info

# 启动前端
cd 采购/frontend
npm install
npm run dev

# 构建前端
npm run build
```

---

## 已完成功能

- [x] 采购申请 (PR) 全流程
- [x] 询价单 (RFQ) 管理
- [x] 供应商管理
- [x] 供应商报价与选标
- [x] 采购订单 (PO)
- [x] 收货管理
- [x] 发票管理
- [x] 审批流程
- [x] 企业微信消息通知
- [x] AI 物料分类（可选）
- [x] 操作历史记录
- [x] 价格历史查询
- [x] 供应商评估（评估模板、评估记录、排名统计）
- [x] **采购合同管理**（合同CRUD、审批、执行跟踪、到期预警）
- [x] **采购预算管理**（预算CRUD、审批、使用跟踪、预警阈值、统计分析）
- [x] **付款管理**（付款CRUD、审批、付款计划、逾期预警、统计分析）

---

## 与其他系统的集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| Portal | JWT Token | 使用 Portal 签发的 Token |
| CRM | API 调用 | 供应商信息同步 |
| shared/auth | symlink | 共享认证模块 |
| 企业微信 | wechatpy | 消息推送、OAuth 登录 |

---

## 注意事项

1. **中文目录**: 命令行操作时使用引号包裹 `"采购/backend"`
2. **端口**: 使用 5001 端口
3. **Celery**: 异步任务需要 Redis 和 Celery Worker
4. **企业微信**: 需要配置企业微信 AppID、Secret 等
5. **数据库**: 使用独立的 `caigou` 数据库
6. **Tailwind CSS**: 前端使用 Tailwind 而非 Ant Design
