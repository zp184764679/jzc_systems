# 报价系统 (Quotation) - Claude Code 项目上下文

## 系统概述

报价系统是 JZC 企业管理系统的核心业务模块，用于机加工精密零件的智能报价。支持图纸上传、OCR 识别、BOM 管理、工艺路线配置、自动成本计算和报价单生成。

**部署状态**: 已部署

### 核心功能
- 图纸上传与 OCR 识别
- BOM 物料清单管理
- 材料库管理
- 工艺库管理
- 产品库管理
- 工艺路线配置
- 自动报价计算（基于创怡兴公式）
- 报价单 Excel/PDF 导出
- **报价审批流程**（草稿→待审核→已批准→已发送）
- **报价版本管理**
  - 创建新版本
  - 版本历史查看
  - 版本对比
  - 设置当前版本
- **报价有效期管理**（新）
  - 有效期状态显示（已过期/即将过期/正常）
  - 延长有效期（按天数或指定日期）
  - 即将过期报价查询
  - 自动过期检查
  - 有效期统计
- 跨系统集成（CRM客户、HR业务员）

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 8001 |
| 前端端口(dev) | 6001 |
| 前端路径 | `/quotation/` |
| API路径 | `/quotation/api/` |
| PM2服务名 | quotation-backend |
| 数据库 | cncplan |
| 健康检查 | `curl http://127.0.0.1:8001/health` |

---

## 技术栈

### 前端
- React 18.3.1
- Vite 5.4.11
- Ant Design
- Zustand (状态管理)
- React Query / TanStack Query

### 后端
- **FastAPI** 0.109.0 + Uvicorn 0.27.0
- SQLAlchemy 2.0.25 + Alembic
- Pydantic 2.5.3
- Celery 5.3.6 + Redis 5.0.1 (异步任务)

### OCR/Vision
- RapidOCR-ONNXRUNTIME (轻量级 OCR)
- OpenCV 4.8+ (图像预处理)
- PyMuPDF (PDF 处理)
- Pillow (图像处理)

### 文档生成
- openpyxl / pandas (Excel)
- reportlab / WeasyPrint (PDF)

---

## 目录结构

```
报价/
├── backend/
│   ├── main.py                          # FastAPI 应用入口
│   ├── requirements.txt                 # Python 依赖
│   ├── celery_app.py                    # Celery 异步任务配置
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                  # 应用配置
│   │   └── database.py                  # 数据库配置
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py                      # 认证路由
│   │   ├── drawings.py                  # 图纸管理
│   │   ├── materials.py                 # 材料库
│   │   ├── processes.py                 # 工艺库
│   │   ├── products.py                  # 产品管理
│   │   ├── quotes.py                    # 报价管理
│   │   ├── boms.py                      # BOM 管理
│   │   ├── routes.py                    # 工艺路线
│   │   ├── ocr_corrections.py           # OCR 学习
│   │   ├── integration.py               # 跨系统集成
│   │   └── schemas.py                   # Pydantic 模型
│   ├── models/
│   │   ├── __init__.py
│   │   ├── drawing.py                   # 图纸模型
│   │   ├── material.py                  # 材料模型
│   │   ├── process.py                   # 工艺模型
│   │   ├── process_cost.py              # 工艺成本模型
│   │   ├── process_route.py             # 工艺路线模型
│   │   ├── product.py                   # 产品模型
│   │   ├── quote.py                     # 报价模型
│   │   ├── quote_approval.py            # 报价审批模型
│   │   ├── bom.py                       # BOM 模型
│   │   └── ocr_correction.py            # OCR 修正模型
│   ├── services/
│   │   ├── drawing_ocr_service.py       # 图纸 OCR 服务
│   │   ├── quote_calculator.py          # 报价计算服务
│   │   ├── quote_excel_service.py       # Excel 导出服务
│   │   ├── quote_document_generator.py  # 文档生成服务
│   │   ├── crm_service.py               # CRM 集成服务
│   │   ├── hr_service.py                # HR 集成服务
│   │   └── ocr_learning_service.py      # OCR 学习服务
│   ├── utils/
│   │   ├── file_handler.py              # 文件处理
│   │   ├── error_handler.py             # 错误处理
│   │   └── logging_config.py            # 日志配置
│   ├── migrations/                      # 数据库迁移
│   ├── uploads/
│   │   ├── drawings/                    # 图纸文件
│   │   └── quotes/                      # 报价文件
│   ├── templates/                       # 模板文件
│   ├── scripts/                         # 数据导入脚本
│   └── venv/
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/
│   │   │   └── auth.js
│   │   ├── components/
│   │   │   ├── AppHeader.jsx
│   │   │   ├── AppSider.jsx
│   │   │   └── AuthProvider.jsx
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── DrawingUpload.jsx        # 图纸上传
│   │   │   ├── DrawingList.jsx          # 图纸列表
│   │   │   ├── MaterialLibrary.jsx      # 材料库
│   │   │   ├── ProcessLibrary.jsx       # 工艺库
│   │   │   ├── ProcessManage.jsx        # 工艺管理
│   │   │   ├── ProductLibrary.jsx       # 产品库
│   │   │   ├── BOMManage.jsx            # BOM 管理
│   │   │   ├── QuoteCreate.jsx          # 创建报价
│   │   │   ├── QuoteList.jsx            # 报价列表
│   │   │   └── QuoteDetail.jsx          # 报价详情
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── store/                       # Zustand 状态
│   │   └── utils/
│   │       └── ssoAuth.js
│   └── dist/
└── package.json
```

---

## API 路由清单

### 认证 API (/api/auth)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/verify` | 验证 Token |

### 图纸管理 API (/api/drawings)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/drawings` | 获取图纸列表 |
| GET | `/api/drawings/{id}` | 获取图纸详情 |
| POST | `/api/drawings/upload` | 上传图纸 |
| POST | `/api/drawings/{id}/ocr` | 执行 OCR 识别 |
| PUT | `/api/drawings/{id}` | 更新图纸信息 |
| DELETE | `/api/drawings/{id}` | 删除图纸 |

### 材料库 API (/api/materials)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/materials` | 获取材料列表 |
| GET | `/api/materials/{id}` | 获取材料详情 |
| POST | `/api/materials` | 创建材料 |
| PUT | `/api/materials/{id}` | 更新材料 |
| DELETE | `/api/materials/{id}` | 删除材料 |
| GET | `/api/materials/search` | 搜索材料 |

### 工艺库 API (/api/processes)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/processes` | 获取工艺列表 |
| GET | `/api/processes/{id}` | 获取工艺详情 |
| POST | `/api/processes` | 创建工艺 |
| PUT | `/api/processes/{id}` | 更新工艺 |
| DELETE | `/api/processes/{id}` | 删除工艺 |
| GET | `/api/processes/categories` | 获取工艺分类 |

### 产品管理 API (/api/products)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/products` | 获取产品列表 |
| GET | `/api/products/{id}` | 获取产品详情 |
| POST | `/api/products` | 创建产品 |
| PUT | `/api/products/{id}` | 更新产品 |
| DELETE | `/api/products/{id}` | 删除产品 |

### 报价管理 API (/api/quotes)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/quotes` | 获取报价列表 |
| GET | `/api/quotes/{id}` | 获取报价详情 |
| POST | `/api/quotes` | 创建报价 |
| POST | `/api/quotes/calculate` | 计算报价 |
| PUT | `/api/quotes/{id}` | 更新报价 |
| DELETE | `/api/quotes/{id}` | 删除报价 |
| GET | `/api/quotes/{id}/export/excel` | 导出 Excel |
| GET | `/api/quotes/{id}/export/pdf` | 导出 PDF |
| GET | `/api/quotes/statuses` | 获取状态列表 |
| POST | `/api/quotes/{id}/submit` | 提交审核 |
| POST | `/api/quotes/{id}/approve` | 审批通过 |
| POST | `/api/quotes/{id}/reject` | 审批拒绝 |
| POST | `/api/quotes/{id}/revise` | 退回修改 |
| POST | `/api/quotes/{id}/send` | 发送给客户 |
| POST | `/api/quotes/{id}/withdraw` | 撤回 |
| GET | `/api/quotes/{id}/approvals` | 获取审批历史 |
| GET | `/api/quotes/expiring` | 获取即将过期报价 |
| POST | `/api/quotes/check-expired` | 检查并标记过期报价 |
| PUT | `/api/quotes/{id}/extend-validity` | 延长有效期 |
| GET | `/api/quotes/validity-statistics` | 有效期统计 |

### BOM 管理 API (/api)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/boms` | 获取 BOM 列表 |
| GET | `/api/boms/{id}` | 获取 BOM 详情 |
| POST | `/api/boms` | 创建 BOM |
| PUT | `/api/boms/{id}` | 更新 BOM |
| DELETE | `/api/boms/{id}` | 删除 BOM |

### 工艺路线 API (/api)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/process-routes` | 获取工艺路线列表 |
| POST | `/api/process-routes` | 创建工艺路线 |
| PUT | `/api/process-routes/{id}` | 更新工艺路线 |
| DELETE | `/api/process-routes/{id}` | 删除工艺路线 |

### 跨系统集成 API (/api/integration)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/integration/customers` | 获取 CRM 客户列表 |
| GET | `/api/integration/salesmen` | 获取 HR 业务员列表 |

---

## 数据模型

### Quote 报价单

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| quote_number | String | 报价单号（唯一） |
| drawing_id | Integer | 关联图纸 ID |
| product_id | Integer | 关联产品 ID |
| customer_name | String | 客户名称 |
| product_name | String | 产品名称 |
| lot_size | Integer | 批量 |
| material_cost | Decimal | B.材料费 |
| process_cost | Decimal | C.加工费 |
| management_cost | Decimal | D.管理费 |
| other_cost | Decimal | F.其他费用 |
| subtotal_cost | Decimal | A.小计单价 |
| profit_rate | Float | 利润率 |
| profit_amount | Decimal | M.利润 |
| unit_price | Decimal | N.零件单价 |
| total_amount | Decimal | 总价 |
| status | String | 状态（draft/pending_review/approved/rejected/sent/expired） |
| valid_until | Date | 有效期截止日期 |
| calculation_details | JSON | 计算详情 |
| submitted_at | DateTime | 提交审核时间 |
| submitted_by | Integer | 提交人ID |
| submitted_by_name | String | 提交人姓名 |
| approved_at | DateTime | 审批时间 |
| approved_by | Integer | 审批人ID |
| approved_by_name | String | 审批人姓名 |
| rejected_at | DateTime | 拒绝时间 |
| rejected_by | Integer | 拒绝人ID |
| reject_reason | Text | 拒绝原因 |
| sent_at | DateTime | 发送时间 |
| sent_by | Integer | 发送人ID |

### QuoteApproval 审批记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| quote_id | Integer | 报价单ID（外键） |
| action | String | 审批动作（submit/approve/reject/revise/send/withdraw） |
| from_status | String | 原状态 |
| to_status | String | 新状态 |
| approver_id | Integer | 审批人ID |
| approver_name | String | 审批人姓名 |
| approver_role | String | 审批人角色 |
| comment | Text | 审批意见 |
| created_at | DateTime | 操作时间 |

### Drawing 图纸

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| drawing_number | String | 图纸编号 |
| file_path | String | 文件路径 |
| ocr_result | JSON | OCR 识别结果 |
| material_name | String | 材料名称 |
| outer_diameter | Float | 外径 |
| product_length | Float | 产品长度 |

### Material 材料

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String | 材料代码 |
| name | String | 材料名称 |
| category | String | 分类 |
| density | Float | 比重 |
| price_per_kg | Float | 单价（元/kg） |

### Process 工艺

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String | 工艺代码 |
| name | String | 工艺名称 |
| category | String | 分类 |
| defect_rate | Float | 不良率 |
| daily_production | Float | 日产量 |
| cost_per_day | Float | 工事费/日 |

---

## 报价计算公式（创怡兴）

### B. 材料费
```
材料费 = (材料单价 × 零件重量 / 1000) × 材管率 × (1 + 总不良率)
```

### C. 加工费
```
每道工序：加工小费 = ((加工日数 + 段取时间) × 工事费/日) / LOT
加工费 = Σ 所有工序的加工小费
```

### D. 管理费
```
管理费 = (B + C + H) × 管理费率
```

### N. 零件单价
```
小计 = B + C + D + F
利润 = 小计 × 利润率
单价 = 小计 + 利润
```

---

## 本地开发

```bash
# 启动后端
cd 报价/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py  # 或 uvicorn main:app --reload --port 8001

# 启动 Celery Worker（可选）
celery -A celery_app worker --loglevel=info

# 启动前端
cd 报价/frontend
npm install
npm run dev

# 构建前端
npm run build
```

---

## 已完成功能

- [x] 图纸上传与管理
- [x] OCR 图纸识别（RapidOCR）
- [x] 材料库管理
- [x] 工艺库管理
- [x] 产品库管理
- [x] BOM 物料清单
- [x] 工艺路线配置
- [x] 自动报价计算
- [x] 报价单 Excel/PDF 导出
- [x] **报价审批流程**（提交/审批/拒绝/退回/发送/撤回）
- [x] 审批历史记录
- [x] **报价有效期管理**（有效期显示/延期/过期检查/统计）
- [x] CRM 客户集成
- [x] HR 业务员集成
- [x] SSO Token 认证

---

## 报价审批流程

### 状态流转

```
┌─────────┐   提交审核   ┌──────────────┐
│  草稿   │ ──────────► │   待审核     │
│ (draft) │ ◄────────── │(pending_review)│
└─────────┘    撤回/退回  └──────┬───────┘
                                │
                    ┌───────────┼───────────┐
                    │ 审批通过  │ 审批拒绝  │
                    ▼           │           ▼
              ┌───────────┐     │     ┌───────────┐
              │  已批准   │     │     │  已拒绝   │
              │(approved) │     │     │(rejected) │
              └─────┬─────┘     │     └─────┬─────┘
                    │           │           │
                    │ 发送客户  │           │ 退回修改
                    ▼           │           │
              ┌───────────┐     │           │
              │  已发送   │◄────┴───────────┘
              │  (sent)   │
              └───────────┘
```

### 状态说明

| 状态 | 代码 | 说明 |
|------|------|------|
| 草稿 | draft | 新创建或被退回的报价单 |
| 待审核 | pending_review | 已提交等待审批 |
| 已批准 | approved | 审批通过，可发送给客户 |
| 已拒绝 | rejected | 审批未通过 |
| 已发送 | sent | 已发送给客户（终态） |
| 已过期 | expired | 报价单已过有效期（终态） |

### 审批动作

| 动作 | 代码 | 源状态 | 目标状态 |
|------|------|--------|----------|
| 提交审核 | submit | draft | pending_review |
| 审批通过 | approve | pending_review | approved |
| 拒绝 | reject | pending_review | rejected |
| 退回修改 | revise | pending_review/approved/rejected | draft |
| 发送客户 | send | approved | sent |
| 撤回 | withdraw | pending_review | draft |

---

## 与其他系统的集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| Portal | JWT Token | 使用 Portal 签发的 Token |
| CRM | API 调用 | 获取客户信息 |
| HR | API 调用 | 获取业务员信息 |
| shared/auth | symlink | 共享认证模块 |

---

## 注意事项

1. **FastAPI 框架**: 报价系统使用 FastAPI 而非 Flask
2. **端口**: 使用 8001 端口
3. **中文目录**: 命令行操作时使用引号包裹路径 `"报价/backend"`
4. **OCR 服务**: 支持多种 OCR 方案（RapidOCR、WSL 调用等）
5. **异步任务**: Celery + Redis 处理耗时任务
6. **API 文档**: FastAPI 自动生成 `/docs` Swagger 文档
