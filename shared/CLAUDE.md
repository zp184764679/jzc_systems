# Shared 共享模块 - Claude Code 项目上下文

## 模块概述

shared 目录包含跨所有子系统共享的认证、配置和工具模块。各子系统通过 symlink 或路径引用的方式使用这些模块。

---

## 目录结构

```
shared/
├── auth/                      # 认证核心模块
│   ├── __init__.py           # 导出所有认证相关功能
│   ├── jwt_utils.py          # JWT Token 创建和验证
│   ├── models.py             # User 和 RegistrationRequest 模型
│   ├── password_utils.py     # 密码哈希和验证
│   ├── permissions.py        # 权限检查工具
│   ├── migrate_to_role.py    # 角色迁移脚本
│   └── fix_admin_password.py # 管理员密码修复脚本
├── frontend/                  # 前端共享模块
│   ├── authEvents.js         # 认证事件总线
│   ├── ssoAuth.js            # SSO 认证工具
│   └── api.js                # API 客户端模板
├── auth_middleware.py        # Flask 认证中间件
├── api-config.js             # 前端 API 配置
├── cache_config.py           # Redis 缓存配置
├── logging_config.py         # 日志配置
├── file_storage.py           # 文件存储服务
├── operation_history.py      # 操作历史记录
└── validators.py             # 数据验证工具
```

---

## 核心模块说明

### auth/jwt_utils.py - JWT 工具

| 函数 | 说明 |
|------|------|
| `create_access_token(data, expires_delta)` | 创建 JWT Token |
| `create_token_from_user(user_dict)` | 从用户字典创建 Token |
| `verify_token(token)` | 验证并解码 Token |

**配置**:
- `JWT_SECRET_KEY` 环境变量（必须在生产环境设置）
- Token 有效期：8 小时

### auth/password_utils.py - 密码工具

| 函数 | 说明 |
|------|------|
| `hash_password(password)` | 使用 bcrypt 哈希密码 |
| `verify_password(plain, hashed)` | 验证密码是否匹配 |

### auth/models.py - 数据模型

**User 模型字段**:
- `id`, `username`, `email`, `hashed_password`
- `full_name`, `emp_no`, `user_type`
- `role`: user/supervisor/admin/super_admin
- `permissions`: JSON 数组，可访问系统列表
- `supplier_id`: 供应商 ID（供应商用户专用）
- `department_id/name`, `position_id/name`, `team_id/name`

**RegistrationRequest 模型**:
- 用户注册申请表，需管理员审批

### auth/permissions.py - 权限检查

**Roles 常量**:
```python
class Roles:
    USER = 'user'
    SUPERVISOR = 'supervisor'
    ADMIN = 'admin'
    SUPER_ADMIN = 'super_admin'
```

| 函数 | 说明 |
|------|------|
| `is_admin(role)` | 检查是否为管理员 (admin 或 super_admin) |
| `is_super_admin(role)` | 检查是否为超级管理员 |
| `has_system_permission(perms, system)` | 检查系统访问权限 |
| `can_manage_user(manager, target)` | 检查用户管理权限 |

### auth_middleware.py - Flask 中间件

提供 `@require_auth` 装饰器用于保护 API 路由。

---

## 前端共享模块

### frontend/authEvents.js - 认证事件

```javascript
import { authEvents, AUTH_EVENTS } from '../utils/authEvents';

// 监听 401 事件
authEvents.on(AUTH_EVENTS.UNAUTHORIZED, () => {
  // 处理认证失败
});

// 发送事件
authEvents.emit(AUTH_EVENTS.UNAUTHORIZED, { url, status });
```

### frontend/ssoAuth.js - SSO 工具

提供 SSO 登录跳转、Token 验证等功能。

---

## 使用方式

### 后端使用

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.auth import (
    User,
    init_auth_db,
    create_access_token,
    verify_token,
    verify_password,
    hash_password,
    has_system_permission,
    is_admin,
    Roles
)
from shared.auth_middleware import require_auth
```

### 前端使用

```javascript
// 复制或 symlink frontend/authEvents.js 到各子系统的 src/utils/ 目录
import { authEvents, AUTH_EVENTS } from '../utils/authEvents';
```

---

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `JWT_SECRET_KEY` | JWT 签名密钥 | 开发环境有默认值 |
| `AUTH_DB_USER` | 认证数据库用户 | 开发环境: app |
| `AUTH_DB_PASSWORD` | 认证数据库密码 | 开发环境: app |
| `AUTH_DB_HOST` | 数据库主机 | localhost |
| `AUTH_DB_NAME` | 数据库名称 | account |

---

## 注意事项

1. **Symlink**: 各子系统通过 symlink 或路径引用此目录，修改会影响所有系统
2. **生产环境**: 必须设置 `JWT_SECRET_KEY` 和数据库凭证环境变量
3. **数据库**: 使用 `account` 数据库存储用户信息
4. **角色系统**: 支持 user/supervisor/admin/super_admin 四级角色
5. **权限系统**: 支持基于系统名称的访问控制（如 hr, quotation, 采购）
