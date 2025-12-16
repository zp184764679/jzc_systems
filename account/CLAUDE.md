# Account 账户管理系统 - Claude Code 项目上下文

## 系统概述

Account 系统是 JZC 企业管理系统的账户管理模块，负责用户账户的统一管理，包括用户注册审批、权限分配、密码管理，以及与 HR 系统的数据同步。

**部署状态**: 已部署

### 核心功能
- 用户管理（CRUD + 激活/停用）
- 用户注册审批流程
- 权限分配管理
- 密码重置
- HR 员工数据同步
- 组织架构选项获取

---

## 部署信息

| 配置项 | 值 |
|--------|-----|
| 后端端口 | 8004 |
| 前端端口(dev) | 6003 |
| 前端路径 | `/account/` |
| API路径 | `/account/api/` |
| PM2服务名 | account-backend |
| 数据库 | account (独立) |
| 健康检查 | `curl http://127.0.0.1:8004/health` |

---

## 技术栈

### 前端
- React 19.2.0
- Vite
- Ant Design 5.28.1
- Axios

### 后端
- Flask 3.0.0 + Flask-CORS 4.0.0
- Flask-SQLAlchemy + Flask-Migrate
- SQLAlchemy 2.0.23
- PyMySQL

---

## 目录结构

```
account/
├── backend/
│   ├── main.py                      # Flask 应用入口
│   ├── requirements.txt             # Python 依赖
│   ├── db_upgrade.py                # 数据库升级脚本
│   ├── check_user.py                # 用户检查脚本
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── registration.py      # 注册申请模型
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py              # 认证路由
│   │       ├── register.py          # 注册路由
│   │       ├── users.py             # 用户管理路由
│   │       └── hr_sync.py           # HR 数据同步路由
│   └── venv/
├── frontend/
│   ├── src/
│   │   ├── main.jsx                 # React 入口
│   │   ├── App.jsx                  # 主应用组件
│   │   ├── pages/
│   │   │   ├── Login.jsx            # 登录页
│   │   │   ├── Register.jsx         # 注册页
│   │   │   ├── UserManagement.jsx   # 用户管理
│   │   │   ├── AdminPanel.jsx       # 管理面板
│   │   │   ├── RegistrationApproval.jsx # 注册审批
│   │   │   └── HRSync.jsx           # HR 数据同步
│   │   ├── services/
│   │   │   └── api.js               # API 服务
│   │   └── utils/
│   │       └── ssoAuth.js           # SSO 认证工具
│   └── dist/
└── package.json
```

---

## API 路由清单

### 用户管理 API (/users)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/users` | 获取所有用户 | 管理员 |
| GET | `/users/<id>` | 获取单个用户 | 管理员 |
| PUT | `/users/<id>` | 更新用户信息 | 管理员 |
| DELETE | `/users/<id>` | 删除用户 | 管理员 |
| POST | `/users/<id>/toggle-active` | 切换用户激活状态 | 管理员 |
| POST | `/users/<id>/reset-password` | 重置用户密码 | 管理员 |

### 批量操作 API (/users/batch)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/users/batch/toggle-active` | 批量启用/停用用户 | 管理员 |
| POST | `/users/batch/assign-role` | 批量分配角色 | 管理员 |
| POST | `/users/batch/assign-permissions` | 批量分配权限 | 管理员 |
| POST | `/users/batch/delete` | 批量删除用户 | 管理员 |
| POST | `/users/batch/reset-password` | 批量重置密码 | 管理员 |
| POST | `/users/batch/update-org` | 批量更新组织信息 | 管理员 |

### HR 同步 API (/hr-sync)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/hr-sync/org-options` | 获取组织选项（工厂/部门/岗位/团队） | 公开 |
| GET | `/hr-sync/employees` | 获取 HR 在职员工列表 | 管理员 |
| GET | `/hr-sync/preview` | 预览同步结果 | 管理员 |
| POST | `/hr-sync/execute` | 执行同步更新 | 管理员 |
| POST | `/hr-sync/batch-create` | 批量创建用户 | 管理员 |

### 注册 API (/register)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/register` | 提交注册申请 |
| GET | `/register/pending` | 获取待审批列表 |
| POST | `/register/approve/<id>` | 审批注册申请 |
| POST | `/register/reject/<id>` | 拒绝注册申请 |

### 认证 API (/auth)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/verify` | 验证 Token |

---

## 数据模型

Account 系统主要使用 `shared/auth` 共享模块的 User 模型，并有自己的注册申请模型。

### User 模型 (shared/auth)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| username | String | 用户名（唯一） |
| email | String | 邮箱 |
| hashed_password | String | 密码哈希 |
| full_name | String | 全名 |
| emp_no | String | 员工编号 |
| user_type | String | 用户类型（employee/supplier） |
| role | String | 角色（user/supervisor/admin/super_admin） |
| permissions | JSON | 权限列表 |
| department_id | Integer | 部门ID |
| department_name | String | 部门名称 |
| position_id | Integer | 岗位ID |
| position_name | String | 岗位名称 |
| team_id | Integer | 团队ID |
| team_name | String | 团队名称 |
| is_active | Boolean | 是否激活 |
| is_admin | Boolean | 是否管理员 |

### Registration 注册申请模型

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| username | String | 申请的用户名 |
| email | String | 邮箱 |
| full_name | String | 全名 |
| emp_no | String | 员工编号 |
| department_id | Integer | 部门ID |
| position_id | Integer | 岗位ID |
| status | String | 状态（pending/approved/rejected） |
| created_at | DateTime | 创建时间 |

---

## 前端页面/组件

### UserManagement.jsx - 用户管理
- 用户列表表格
- 编辑用户信息
- 激活/停用用户
- 重置密码
- 删除用户

### AdminPanel.jsx - 管理面板
- 注册审批 Tab
- 用户管理 Tab
- 权限管理 Tab
- 批量操作 Tab

### BatchOperations.jsx - 批量操作
- 批量启用/停用用户
- 批量分配角色
- 批量分配权限
- 批量重置密码
- 批量更新组织信息
- 批量删除用户

### Register.jsx - 注册页
- 注册表单
- 组织架构下拉选择
- 从 HR 系统获取选项

### RegistrationApproval.jsx - 注册审批
- 待审批列表
- 审批/拒绝操作

### HRSync.jsx - HR 数据同步
- 预览同步差异
- 执行同步更新
- 批量创建用户

---

## 配置文件

### 后端环境变量 (.env)
```bash
# 数据库
MYSQL_USER=app
MYSQL_PASSWORD=app
DB_HOST=localhost
MYSQL_DATABASE=account

# HR 系统
HR_BACKEND_URL=http://localhost:8003
HR_DB_USER=app
HR_DB_PASSWORD=app
HR_DB_HOST=localhost
HR_DB_NAME=hr_system

# 安全
SECRET_KEY=your-secret-key
```

### 前端环境变量 (.env)
```bash
VITE_API_BASE_URL=/account/api
```

---

## 本地开发

```bash
# 启动后端
cd account/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py

# 启动前端
cd account/frontend
npm install
npm run dev

# 构建前端
npm run build
```

---

## 已完成功能

- [x] 用户列表管理
- [x] 用户编辑（角色、权限、组织信息）
- [x] 用户激活/停用
- [x] 密码重置
- [x] 用户删除
- [x] 注册申请与审批
- [x] HR 员工数据同步
- [x] 批量创建用户
- [x] 组织选项获取（从 HR 数据库）
- [x] SSO Token 验证
- [x] 细粒度权限管理 (RBAC)
- [x] 批量操作（启用/停用、分配角色、分配权限、重置密码、更新组织、删除）

---

## 与其他系统的集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| Portal | JWT Token | 使用 Portal 签发的 Token 进行认证 |
| HR | API + 数据库 | 调用 HR API 获取员工数据，直接连接 HR 数据库获取组织选项 |
| shared/auth | symlink | 共享认证模块，User 模型和密码哈希函数 |

---

## 注意事项

1. **端口**: Account 使用端口 8004，不是 8001（8001 是报价系统）
2. **双数据库连接**: 同时连接 account 数据库和 hr_system 数据库
3. **管理员权限**: 用户管理和 HR 同步功能需要管理员权限（role 为 admin 或 super_admin）
4. **批量创建**: 批量创建用户时默认密码为 `jzc123456`
5. **组织数据**: `/hr-sync/org-options` 是公开接口，供注册页面使用
