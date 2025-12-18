# HR 人力资源系统 - Claude Code 项目上下文

## 系统概述

HR 系统是 JZC 企业管理系统的人力资源管理模块，负责员工信息管理、部门/职位/团队基础数据管理，支持多工厂数据管理。

**部署状态**: 已部署

### 核心功能
- 员工信息管理（增删改查）
- 部门管理（支持层级结构）
- 职位管理
- 团队/班组管理
- 工厂/厂区管理
- 员工黑名单管理
- 数据导入导出
- 用户注册审批

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 8003 |
| 前端端口(dev) | 6002 |
| 前端路径 | `/hr/` |
| API路径 | `/hr/api/` |
| PM2服务名 | hr-backend |
| 数据库 | hr_system (独立数据库) |
| 健康检查 | `curl http://127.0.0.1:8003/health` |

---

## 技术栈

### 前端
- React 19.2.0
- Vite 7.2.2
- Ant Design

### 后端
- Flask + Flask-CORS
- Flask-SQLAlchemy + Flask-Migrate
- PyMySQL
- SQLAlchemy >= 2.0.36

---

## 目录结构

```
HR/
├── backend/
│   ├── main.py                          # Flask 应用入口
│   ├── config.py                        # 配置文件
│   ├── requirements.txt                 # Python 依赖
│   ├── app/
│   │   ├── __init__.py                  # Flask 应用工厂
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── employee.py              # 员工模型
│   │   │   └── base_data.py             # 基础数据模型
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py                  # 认证路由
│   │       ├── register.py              # 注册路由
│   │       ├── employees.py             # 员工 CRUD
│   │       └── base_data.py             # 基础数据 CRUD
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── jwt_auth.py                  # JWT 认证中间件
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── test_employees.py
│   ├── migrations/                      # 数据库迁移
│   ├── *.py                             # 数据导入/迁移脚本
│   └── venv/
├── frontend/
│   ├── src/
│   │   ├── main.jsx                     # React 入口
│   │   ├── App.jsx                      # 主应用组件
│   │   ├── pages/
│   │   │   ├── Login.jsx                # 登录页
│   │   │   ├── Register.jsx             # 注册页
│   │   │   ├── EmployeeList.jsx         # 员工列表
│   │   │   ├── BaseDataManagement.jsx   # 基础数据管理
│   │   │   └── RegistrationApproval.jsx # 注册审批
│   │   ├── services/
│   │   │   └── api.js                   # API 服务
│   │   └── utils/
│   │       ├── axios.js                 # Axios 配置
│   │       └── ssoAuth.js               # SSO 认证工具
│   └── dist/
└── package.json
```

---

## API 路由清单

### 员工 API (/api)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/employees` | 获取员工列表（分页+搜索） | 需要 |
| GET | `/api/employees/<id>` | 获取单个员工详情 | 需要 |
| POST | `/api/employees` | 创建员工 | 需要 |
| PUT | `/api/employees/<id>` | 更新员工 | 需要 |
| DELETE | `/api/employees/<id>` | 删除员工 | 需要 |
| POST | `/api/employees/list` | 获取员工列表（POST方式） | 需要 |
| GET | `/api/employees/stats` | 获取员工统计数据 | 需要 |

**员工列表查询参数**:
- `page`: 页码 (默认 1)
- `per_page`: 每页数量 (默认 10000)
- `search`: 搜索关键词
- `department`: 部门筛选
- `employment_status`: 状态筛选
- `factory_id`: 工厂筛选

### 基础数据 API (/api/base-data)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/base-data/departments` | 获取所有部门 |
| POST | `/api/base-data/departments` | 创建部门 |
| PUT | `/api/base-data/departments/<id>` | 更新部门 |
| DELETE | `/api/base-data/departments/<id>` | 删除部门 |
| GET | `/api/base-data/positions` | 获取所有职位 |
| POST | `/api/base-data/positions` | 创建职位 |
| PUT | `/api/base-data/positions/<id>` | 更新职位 |
| DELETE | `/api/base-data/positions/<id>` | 删除职位 |
| GET | `/api/base-data/teams` | 获取所有团队 |
| POST | `/api/base-data/teams` | 创建团队 |
| PUT | `/api/base-data/teams/<id>` | 更新团队 |
| DELETE | `/api/base-data/teams/<id>` | 删除团队 |
| GET | `/api/base-data/factories` | 获取所有工厂 |
| POST | `/api/base-data/factories` | 创建工厂 |
| PUT | `/api/base-data/factories/<id>` | 更新工厂 |
| DELETE | `/api/base-data/factories/<id>` | 删除工厂 |

### 认证 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/verify` | 验证 Token |
| POST | `/api/register` | 用户注册 |
| GET | `/api/register/pending` | 获取待审批注册 |
| POST | `/api/register/approve/<id>` | 审批注册 |

---

## 数据模型

### Employee 员工表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| empNo | String(50) | 员工编号（唯一） |
| name | String(100) | 姓名 |
| gender | String(10) | 性别 |
| birth_date | Date | 出生日期 |
| id_card | String(50) | 身份证号 |
| phone | String(20) | 电话 |
| email | String(100) | 邮箱 |
| nationality | String(50) | 民族 |
| education | String(50) | 学历 |
| native_place | String(100) | 籍贯 |
| bank_card | String(50) | 银行卡 |
| has_card | String(10) | 是否制卡 |
| salary_type | String(20) | 薪资制（计时/计件） |
| accommodation | String(20) | 住宿（内宿/外宿） |
| department_id | Integer | 部门ID（外键） |
| position_id | Integer | 职位ID（外键） |
| team_id | Integer | 团队ID（外键） |
| factory_id | Integer | 工厂ID（外键） |
| department | String(100) | 部门名称（兼容字段） |
| title | String(100) | 职位名称（兼容字段） |
| team | String(100) | 团队名称（兼容字段） |
| hire_date | Date | 入职日期 |
| employment_status | String(20) | 状态（Active/Resigned/...） |
| resignation_date | Date | 离职日期 |
| contract_type | String(50) | 合同类型 |
| contract_start_date | Date | 合同开始日期 |
| contract_end_date | Date | 合同结束日期 |
| base_salary | Float | 基本工资 |
| performance_salary | Float | 绩效工资 |
| total_salary | Float | 总工资 |
| home_address | Text | 家庭地址 |
| emergency_contact | String(100) | 紧急联系人 |
| emergency_phone | String(20) | 紧急联系电话 |
| is_blacklisted | Boolean | 是否黑名单 |
| blacklist_reason | Text | 黑名单原因 |
| blacklist_date | Date | 加入黑名单日期 |
| remark | Text | 备注 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### Department 部门表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String(50) | 部门编码（唯一） |
| name | String(100) | 部门名称 |
| parent_id | Integer | 上级部门ID |
| manager_id | Integer | 部门负责人ID |
| description | Text | 描述 |
| is_active | Boolean | 是否启用 |
| sort_order | Integer | 排序 |

### Position 职位表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String(50) | 职位编码（唯一） |
| name | String(100) | 职位名称 |
| level | Integer | 职级(1-10) |
| category | String(50) | 职位类别 |
| description | Text | 描述 |
| is_active | Boolean | 是否启用 |

### Team 团队表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String(50) | 团队编码（唯一） |
| name | String(100) | 团队名称 |
| department_id | Integer | 所属部门ID |
| leader_id | Integer | 团队负责人ID |
| description | Text | 描述 |
| is_active | Boolean | 是否启用 |

### Factory 工厂表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String(50) | 工厂编码（唯一） |
| name | String(100) | 工厂名称 |
| city | String(100) | 所在城市 |
| address | String(255) | 详细地址 |
| description | Text | 描述 |
| is_active | Boolean | 是否启用 |

---

## 前端页面/组件

### EmployeeList.jsx - 员工列表
- 员工表格展示
- 分页、搜索、筛选
- 新增/编辑/删除员工
- 支持工厂筛选

### BaseDataManagement.jsx - 基础数据管理
- 部门管理（树形结构）
- 职位管理
- 团队管理
- 工厂管理

### Login.jsx - 登录页
- 本地登录
- SSO Token 验证

### Register.jsx - 注册页
- 新用户注册表单

### RegistrationApproval.jsx - 注册审批
- 待审批列表
- 审批通过/拒绝

---

## 配置文件

### 后端环境变量 (.env)
```bash
# 数据库
USE_SQLITE=false
DB_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=hr_system

# 或直接指定连接字符串
SQLALCHEMY_DATABASE_URI=mysql+pymysql://user:pass@host/hr_system

# 端口
PORT=8003

# CORS
CORS_ORIGINS=https://jzchardware.cn
```

### 前端环境变量 (.env)
```bash
VITE_API_BASE_URL=/hr/api
```

---

## 本地开发

```bash
# 启动后端
cd HR/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py

# 启动前端
cd HR/frontend
npm install
npm run dev

# 构建前端
npm run build
```

---

## 数据导入脚本

backend 目录下包含多个数据导入脚本：

| 脚本 | 说明 |
|------|------|
| import_employees.py | 导入员工数据 |
| import_dongguan_employees.py | 导入东莞工厂员工 |
| import_base_data.py | 导入基础数据 |
| import_team_info.py | 导入团队信息 |
| fix_employee_data.py | 修复员工数据 |
| fix_phone_numbers.py | 修复电话号码 |
| migrate_add_factory.py | 添加工厂字段迁移 |
| migrate_add_blacklist.py | 添加黑名单字段迁移 |

---

## 已完成功能

- [x] 员工信息 CRUD
- [x] 部门/职位/团队/工厂管理
- [x] 多工厂支持（中山、东莞）
- [x] 员工黑名单管理
- [x] 分页、搜索、筛选
- [x] SSO 认证集成
- [x] 用户注册审批流程
- [x] 数据导入导出
- [x] 考勤管理（考勤规则、班次、排班、打卡记录）
- [x] 假期管理（假期类型、余额、请假申请、审批）
- [x] 薪资管理（薪资结构、工资项、工资单、调整）
- [x] 绩效管理（KPI模板、绩效目标、评估、反馈）
- [x] 招聘管理（职位发布、应聘申请、面试安排、评价、人才库）

---

## 与其他系统的集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| Portal | JWT Token | 使用 Portal 签发的 Token 进行认证 |
| Account | API 调用 | Account 系统同步 HR 员工数据 |
| shared/auth | symlink | 共享认证模块 |

---

## 注意事项

1. **独立数据库**: HR 使用独立的 `hr_system` 数据库，而非共享的 `cncplan`
2. **外键关系**: 员工表通过外键关联部门/职位/团队/工厂，同时保留兼容的文本字段
3. **SQLite 支持**: 开发环境可设置 `USE_SQLITE=true` 使用 SQLite
4. **数据迁移**: 使用 Flask-Migrate 管理数据库迁移
5. **多工厂**: 支持多工厂数据管理（如中山、东莞）
