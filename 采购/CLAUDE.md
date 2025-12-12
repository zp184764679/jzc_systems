# 采购系统 (Caigou) - Claude Code 项目上下文

## 系统概述

采购系统是 JZC 企业管理系统的采购管理模块，覆盖完整的采购流程：采购申请(PR) → 询价单(RFQ) → 供应商报价 → 采购订单(PO) → 收货 → 发票管理。支持企业微信集成和审批流程。

### 核心功能
- 采购申请 (PR) 管理与审批
- 询价单 (RFQ) 创建与发送
- 供应商管理
- 供应商报价与选标
- 采购订单 (PO) 管理
- 收货管理 (GRN)
- 发票管理
- 审批流程
- 企业微信消息通知
- AI 物料分类（可选）

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 5001 |
| 前端路径 | `/caigou/` |
| API路径 | `/caigou/api/` |
| PM2服务名 | caigou-backend |
| 数据库 | caigou |
| 健康检查 | `curl http://127.0.0.1:5001/api/health` |

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
│   ├── app.py                           # Flask 应用入口
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
│   │   └── notification.py              # 通知
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
│   │   └── wework_oauth_routes.py       # 企业微信 OAuth
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
│   │   │   └── InvoiceManagement.jsx    # 发票管理
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
python app.py

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
