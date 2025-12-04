# EAM设备管理系统

EAM (Enterprise Asset Management) 设备管理系统，从PM系统的设备模块独立出来的专业设备管理系统。

## 系统架构

```
EAM/
├── backend/                    # 后端服务（Flask + MySQL）
│   ├── app/
│   │   ├── __init__.py        # Flask应用工厂
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── machine.py     # 设备模型
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── machines.py    # 设备API路由
│   ├── main.py                # 入口文件
│   ├── requirements.txt       # Python依赖
│   └── .env                   # 环境配置
│
└── frontend/                  # 前端应用（React + Ant Design）
    ├── src/
    │   ├── pages/
    │   │   └── machines/
    │   │       └── MachineList.jsx  # 设备列表页面
    │   ├── services/
    │   │   └── api.js         # API封装
    │   ├── App.jsx            # 主应用
    │   ├── App.css
    │   └── main.jsx
    ├── index.html
    ├── package.json           # Node依赖
    └── vite.config.js         # Vite配置
```

## 技术栈

### 后端
- **Flask 3.1.0** - Web框架
- **SQLAlchemy 2.0.36** - ORM
- **Flask-CORS 5.0.0** - 跨域支持
- **PyMySQL 1.1.1** - MySQL驱动
- **Flask-Migrate 4.0.7** - 数据库迁移

### 前端
- **React 19.2.0** - UI框架
- **Vite 7.2.2** - 构建工具
- **Ant Design 5.28.1** - UI组件库
- **React Router 7.9.6** - 路由管理
- **Axios 1.13.2** - HTTP客户端
- **React Query 5.90.9** - 数据管理

## 端口配置

- **前端端口**: 7200
- **后端端口**: 8005
- **数据库**: localhost:3306/cncplan

## 功能模块

### 1. 设备台账
- 设备基础信息管理
- 设备分类和查询
- 设备增删改查

### 2. 设备产能配置（规划中）
- 设备产能设置
- 产能监控

### 3. 维护记录（规划中）
- 维护计划
- 维护历史

## 数据库表结构

### machines 表

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | INT | 主键 |
| machine_code | VARCHAR(64) | 设备编码（唯一） |
| name | VARCHAR(128) | 设备名称 |
| model | VARCHAR(128) | 型号 |
| group | VARCHAR(64) | 设备分组 |
| dept_name | VARCHAR(64) | 部门 |
| sub_dept_name | VARCHAR(64) | 子部门 |
| factory_location | VARCHAR(16) | 工厂位置（深圳/东莞） |
| brand | VARCHAR(64) | 品牌 |
| serial_no | VARCHAR(64) | 出厂编号 |
| manufacture_date | DATE | 出厂日期 |
| purchase_date | DATE | 购入日期 |
| place | VARCHAR(128) | 放置场所 |
| manufacturer | VARCHAR(128) | 生产厂商 |
| capacity | INT | 产能（件/天） |
| status | VARCHAR(16) | 状态（在用/停用/维修/报废） |
| is_active | BOOLEAN | 是否启用 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## API接口

### 设备管理

#### 获取设备列表
```
GET /api/machines?page=1&page_size=10&q=keyword
```

#### 获取设备详情
```
GET /api/machines/{id}
```

#### 创建设备
```
POST /api/machines
{
  "code": "MC-001",
  "name": "立式加工中心",
  "brand": "Mazak",
  "model": "VCN-430A",
  "dept_name": "数控车间",
  "factory_location": "深圳",
  "status": "在用"
}
```

#### 更新设备
```
PUT /api/machines/{id}
{
  "name": "立式加工中心",
  "status": "维修"
}
```

#### 删除设备
```
DELETE /api/machines/{id}
```

## 安装说明

### 后端安装

1. 进入后端目录
```bash
cd C:\Users\Admin\Desktop\EAM\backend
```

2. 创建虚拟环境（可选）
```bash
python -m venv venv
venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
编辑 `.env` 文件，确保数据库配置正确

5. 初始化数据库（如果需要）
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. 启动后端服务
```bash
python main.py
```

后端将运行在 http://localhost:8005

### 前端安装

1. 进入前端目录
```bash
cd C:\Users\Admin\Desktop\EAM\frontend
```

2. 安装依赖
```bash
npm install
```

3. 启动开发服务器
```bash
npm run dev
```

前端将运行在 http://localhost:7200

## 开发说明

### CORS配置
- 后端已配置允许 http://localhost:7200 访问
- 前端使用 Vite proxy 代理 /api 请求到后端 8005 端口

### 数据库
- 使用共享数据库 `cncplan`
- 表名为 `machines`（与PM系统共享）
- 不使用Docker，直接连接本地MySQL

### 界面语言
- 完全中文化界面
- 使用Ant Design中文语言包

## 未来扩展

1. **设备维护管理**
   - 维护计划
   - 维护记录
   - 维护提醒

2. **设备产能分析**
   - 产能统计
   - 效率分析
   - 报表导出

3. **设备生命周期管理**
   - 设备档案
   - 维修历史
   - 成本分析

4. **权限管理**
   - 用户角色
   - 操作权限
   - 数据权限

## 注意事项

1. 确保MySQL服务已启动
2. 确保数据库 `cncplan` 已创建
3. 确保端口 7200 和 8005 未被占用
4. 首次运行前需要初始化数据库表结构
