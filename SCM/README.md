# SCM供应链管理系统

## 系统概述

SCM（Supply Chain Management）供应链管理系统，从PM系统的库存模块独立出来，专注于库存管理功能。

- **前端端口**: 7000
- **后端端口**: 8004
- **数据库**: cncplan (共享数据库)
- **数据表**: inventory_tx

## 系统架构

### 后端 (Backend)
- **技术栈**: Flask 3.1 + SQLAlchemy 2.0 + PyMySQL
- **端口**: 8004
- **数据库**: MySQL (localhost:3306/cncplan)

### 前端 (Frontend)
- **技术栈**: React 19 + Vite 7 + Ant Design 5 + React Router 7
- **端口**: 7000
- **代理**: /api -> http://localhost:8004

## 目录结构

```
C:\Users\Admin\Desktop\SCM\
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask应用工厂
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── inventory.py     # InventoryTx模型
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── inventory.py     # 库存API路由
│   ├── main.py                  # 应用入口
│   ├── requirements.txt         # Python依赖
│   └── .env                     # 环境变量配置
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   └── inventory/
    │   │       ├── Stock.jsx           # 库存总览
    │   │       ├── In.jsx              # 入库登记
    │   │       ├── Out.jsx             # 出库登记
    │   │       └── DeliveryCheck.jsx   # 交货核销
    │   ├── services/
    │   │   └── api.js           # API封装
    │   ├── App.jsx              # 主应用组件
    │   ├── main.jsx             # 入口文件
    │   └── index.css            # 全局样式
    ├── index.html
    ├── package.json             # 前端依赖
    └── vite.config.js           # Vite配置
```

## 功能模块

### 1. 库存总览
- 路径: `/stock`
- 功能:
  - 按内部图号聚合显示库存
  - 支持关键字搜索
  - 查看库存流水详情
  - 导出CSV

### 2. 入库登记
- 路径: `/in`
- 功能:
  - 记录入库操作
  - 必填: 内部图号、数量、仓位
  - 可选: 地点、订单号、单位、备注

### 3. 出库登记
- 路径: `/out`
- 功能:
  - 记录出库操作
  - 库存不足校验
  - 必填: 内部图号、数量、出库仓位
  - 可选: 地点、订单号、单位、备注

### 4. 交货核销
- 路径: `/delivery`
- 功能:
  - 记录交货核销
  - 扣减库存
  - 必填: 内部图号、交货数量
  - 可选: 订单号、仓位、地点、单位、备注

## API端点

### 基础接口
- `GET /ping` - 健康检查
- `GET /api/health` - 数据库连接检查

### 库存管理
- `GET /api/inventory/stock` - 库存总览（聚合查询）
- `GET /api/inventory/transactions` - 库存流水查询
- `POST /api/inventory/in` - 入库登记
- `POST /api/inventory/out` - 出库登记
- `POST /api/inventory/delivery` - 交货核销
- `POST /api/inventory/adjust` - 库存调整

## 数据库模型

### InventoryTx (库存流水表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| product_text | String(128) | 内部图号 (必填) |
| qty_delta | Float | 数量变化 (+入库 / -出库) |
| tx_type | String(32) | 类型 (IN/OUT/DELIVERY/ADJUST) |
| order_no | String(64) | 订单编号 |
| bin_code | String(64) | 仓位 |
| location | String(16) | 地点 (深圳/东莞) |
| uom | String(16) | 单位 (默认pcs) |
| ref | String(128) | 参考号 |
| remark | String(255) | 备注 |
| occurred_at | DateTime | 业务发生时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 安装与运行

### 后端启动

```bash
# 1. 进入后端目录
cd C:\Users\Admin\Desktop\SCM\backend

# 2. 创建虚拟环境 (可选)
python -m venv venv
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库 (如果表不存在)
python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all()"

# 5. 启动服务
python main.py
```

后端将运行在: http://localhost:8004

### 前端启动

```bash
# 1. 进入前端目录
cd C:\Users\Admin\Desktop\SCM\frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

前端将运行在: http://localhost:7000

## 环境配置

### 后端 (.env)
```
DB_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=cncplan
PORT=8004
SECRET_KEY=scm-secret-key-2025
```

### CORS配置
- 允许来源: http://localhost:7000
- 允许方法: GET, POST, PUT, PATCH, DELETE, OPTIONS
- 允许头: Content-Type, Authorization

## 导航菜单

1. **首页** - 系统欢迎页
2. **库存总览** - 查看当前库存状态
3. **入库登记** - 记录入库操作
4. **出库登记** - 记录出库操作
5. **交货核销** - 记录交货核销

## 技术特点

1. **完全中文化界面**
2. **Apple风格UI设计**
3. **Flask工厂模式**
4. **RESTful API规范**
5. **React函数式组件**
6. **Ant Design组件库**
7. **React Router 7路由管理**
8. **Axios HTTP客户端**
9. **共享MySQL数据库**

## 注意事项

1. **不要启动服务** - 仅创建文件，不运行
2. **数据库共享** - 使用PM系统的cncplan数据库
3. **表名固定** - inventory_tx (与PM系统共享)
4. **端口固定** - 前端7000，后端8004
5. **本地数据库** - DB_HOST=localhost (不使用Docker)

## 开发团队

- 系统设计: Claude Code
- 创建日期: 2025年
- 版本: 1.0.0
