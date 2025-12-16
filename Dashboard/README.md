# Dashboard - 精密加工可视化追踪系统

为精密加工行业打造的订单追踪和生产流程可视化系统，支持时间轴展示、仪表盘、待办事项管理和客户门户。

## 功能特点

### 核心功能
- **时间轴视图** - 多维度切换（按客户/订单/工序/部门）
- **仪表盘** - KPI指标、订单状态分布、交付趋势分析
- **待办事项** - 任务管理、截止日期提醒、优先级标记
- **客户门户** - 客户可通过临时链接查看订单进度

### 技术栈
- **前端**: React 18 + Vite + Ant Design + ECharts + react-calendar-timeline
- **后端**: Flask 3.0 + SQLAlchemy 2.0
- **数据库**: MySQL 8.0 (cncplan)

## 快速开始

### 1. 安装后端依赖

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置数据库

编辑 `backend/.env` 文件：
```bash
SQLALCHEMY_DATABASE_URI=mysql+pymysql://app:app@localhost/cncplan?charset=utf8mb4
```

### 3. 创建数据库表

```bash
# 方法1: 使用SQL脚本
mysql -u app -p cncplan < migrations/create_tables.sql

# 方法2: 使用Flask命令
cd backend
flask init-db
flask seed-demo  # 可选：填充示例数据
```

### 4. 启动后端

```bash
cd backend
python main.py
# 后端运行在 http://localhost:8100
```

### 5. 安装前端依赖

```bash
cd frontend
npm install
```

### 6. 启动前端

```bash
npm run dev
# 前端运行在 http://localhost:6100
```

## 目录结构

```
Dashboard/
├── backend/
│   ├── app/
│   │   ├── models/           # 数据模型
│   │   │   ├── production_plan.py
│   │   │   ├── task.py
│   │   │   └── customer_token.py
│   │   ├── routes/           # API路由
│   │   │   ├── timeline.py
│   │   │   ├── dashboard.py
│   │   │   ├── tasks.py
│   │   │   └── customer_portal.py
│   │   └── services/         # 业务服务
│   │       └── data_aggregator.py
│   ├── migrations/           # 数据库迁移
│   ├── main.py               # 入口文件
│   ├── requirements.txt
│   └── .env
│
└── frontend/
    ├── src/
    │   ├── components/       # 组件
    │   │   └── Layout/
    │   ├── pages/            # 页面
    │   │   ├── Dashboard/
    │   │   ├── Timeline/
    │   │   ├── Tasks/
    │   │   └── CustomerPortal/
    │   └── services/         # API服务
    │       └── api.js
    ├── package.json
    └── vite.config.js
```

## API 接口

### 时间轴
- `GET /api/timeline/data` - 获取时间轴数据
- `GET /api/timeline/item/:type/:id` - 获取项目详情
- `GET /api/timeline/stats` - 获取统计数据

### 仪表盘
- `GET /api/dashboard/kpi/summary` - KPI汇总
- `GET /api/dashboard/charts/order-status` - 订单状态分布
- `GET /api/dashboard/charts/delivery-trend` - 交付趋势

### 待办事项
- `GET /api/tasks` - 获取任务列表
- `POST /api/tasks` - 创建任务
- `PUT /api/tasks/:id` - 更新任务
- `DELETE /api/tasks/:id` - 删除任务

### 客户门户
- `POST /api/customer-portal/generate-link` - 生成访问链接
- `GET /api/customer-portal/orders` - 获取客户订单
- `GET /api/customer-portal/orders/:id` - 获取订单详情

## 部署

### PM2 配置

在 `jzc_systems/ecosystem.config.js` 中添加：

```javascript
{
  name: 'dashboard-backend',
  script: 'python',
  args: 'main.py',
  cwd: '/www/jzc_systems/Dashboard/backend',
  interpreter: 'none',
  env: {
    FLASK_DEBUG: 'false'
  }
}
```

### Nginx 配置

```nginx
# Dashboard 前端
location /dashboard/ {
    alias /www/jzc_systems/Dashboard/frontend/dist/;
    try_files $uri $uri/ /dashboard/index.html;
}

# Dashboard API
location /dashboard/api/ {
    proxy_pass http://127.0.0.1:8100/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## 许可证

内部项目 - 晨龙精密企业管理系统
