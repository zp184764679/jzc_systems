# JZC 企业管理系统 - 开发规范

> **目的**: 统一各子系统的开发模式，杜绝因标准化缺失导致的系统性问题。
>
> **适用范围**: 所有12个子系统 + shared模块

---

## 目录

1. [后端开发规范](#后端开发规范)
   - [认证模式](#1-认证模式)
   - [ORM模型定义](#2-orm模型定义)
   - [API路由设计](#3-api路由设计)
   - [错误处理](#4-错误处理)
2. [前端开发规范](#前端开发规范)
   - [组件设计原则](#1-组件设计原则)
   - [状态管理](#2-状态管理)
   - [API调用](#3-api调用)
3. [数据库规范](#数据库规范)
4. [常见错误速查](#常见错误速查)
5. [后端进阶规范](#后端进阶规范)
   - [SQLAlchemy Enum 映射](#5-sqlalchemy-enum-映射重要)
   - [MySQL 兼容性](#6-mysql-兼容性)
   - [FastAPI 路由顺序](#7-fastapi-路由顺序报价系统)
   - [共享模块依赖管理](#8-共享模块依赖管理)
   - [SSO 认证路径规范](#9-sso-认证路径规范)
6. [前端进阶规范](#前端进阶规范)
   - [代码质量检查](#4-代码质量检查)
7. [Nginx 路由规范](#nginx-路由规范)
8. [数据库迁移规范](#数据库迁移规范)
9. [代码审查清单（更新版）](#代码审查清单更新版)

---

## 后端开发规范

### 1. 认证模式

#### 1.1 统一使用函数模式（非装饰器）

**所有子系统必须使用 `get_current_user()` 函数模式**，不要使用装饰器模式。

```python
# ✅ 正确写法
from shared.auth import get_current_user

@bp.route('/api/resource', methods=['POST'])
def create_resource():
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '未授权'}), 401

    # current_user 是字典，包含以下字段：
    user_id = current_user.get('user_id')      # int
    username = current_user.get('username')    # str
    full_name = current_user.get('full_name')  # str
    role = current_user.get('role')            # str

    # 业务逻辑...
    return jsonify({'success': True})
```

```python
# ❌ 错误写法 - 不要使用装饰器模式
@token_required  # 这个装饰器在Portal中不存在！
def create_resource():
    user = g.current_user  # 这种方式不适用于Portal
```

#### 1.2 公开API vs 受保护API

```python
# 公开API（无需认证）
@bp.route('/api/public/list', methods=['GET'])
def public_list():
    # 不需要调用 get_current_user()
    return jsonify({'data': []})

# 受保护API（需要认证）
@bp.route('/api/protected/create', methods=['POST'])
def protected_create():
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '未授权'}), 401
    # 业务逻辑...

# 可选认证API（登录用户有额外功能）
@bp.route('/api/items', methods=['GET'])
def list_items():
    current_user = get_current_user()  # 可能为 None
    if current_user:
        # 返回用户相关数据
        return jsonify({'data': get_user_items(current_user['user_id'])})
    else:
        # 返回公开数据
        return jsonify({'data': get_public_items()})
```

#### 1.3 认证相关导入

```python
# ✅ 正确的导入方式
from shared.auth import get_current_user
from shared.auth.models import User

# ❌ 错误的导入 - db 对象不存在于 shared.auth.models
from shared.auth.models import db  # 这会导致 ImportError！
```

---

### 2. ORM模型定义

#### 2.1 Portal系统模型基类

Portal 使用**纯 SQLAlchemy**，不是 Flask-SQLAlchemy：

```python
# ✅ 正确写法 - Portal模型
from models import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from datetime import datetime

class NewModel(Base):
    __tablename__ = 'new_models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 外键关系
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', backref=backref('new_models', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
```

```python
# ❌ 错误写法 - 这是 Flask-SQLAlchemy 模式，Portal 不使用
from shared.auth.models import db

class NewModel(db.Model):  # 错误！db.Model 不存在
    id = db.Column(db.Integer, primary_key=True)
    user = relationship('User', backref=db.backref('items'))  # db.backref 不存在
```

#### 2.2 其他子系统模型基类

HR、CRM、采购等使用 Flask-SQLAlchemy 的系统：

```python
# 适用于: HR, CRM, Account, 采购, SHM 等
from extensions import db

class NewModel(db.Model):
    __tablename__ = 'new_models'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
```

#### 2.3 模型基类速查表

| 系统 | 基类 | 导入方式 |
|------|------|----------|
| Portal | `Base` | `from models import Base` |
| HR | `db.Model` | `from extensions import db` |
| Account | `db.Model` | `from extensions import db` |
| CRM | `db.Model` | `from extensions import db` |
| 报价 | `Base` | `from database import Base` |
| 采购 | `db.Model` | `from extensions import db` |
| SHM | `db.Model` | `from extensions import db` |

---

### 3. API路由设计

#### 3.1 路由前缀规范

```python
# Portal - 直接使用 /api 前缀
bp = Blueprint('resource', __name__, url_prefix='/api/resource')

# 其他子系统 - 各有不同，参见主 CLAUDE.md
```

#### 3.2 RESTful 设计

```python
# 资源命名使用复数
/api/projects      # 项目列表
/api/projects/1    # 单个项目
/api/tasks         # 任务列表
/api/tasks/1       # 单个任务

# 嵌套资源
/api/projects/1/tasks      # 项目下的任务
/api/tasks/1/comments      # 任务下的评论
/api/tasks/1/checklist     # 任务的检查项
```

#### 3.3 响应格式统一

```python
# 成功响应
return jsonify({
    'success': True,
    'data': {...},
    'message': '操作成功'
}), 200

# 列表响应（带分页）- ⚠️ 必须使用 items 作为键名
return jsonify({
    'data': {
        'items': [...],   # ✅ 正确：统一用 items
        'total': 100,
        'page': 1,
        'page_size': 20
    }
}), 200

# ❌ 错误示例 - 使用特定名称会导致前端解析错误
return jsonify({
    'projects': [...],    # ❌ 错误：用了 projects
    'employees': [...],   # ❌ 错误：用了 employees
    'users': [...]        # ❌ 错误：用了 users
}), 200

# 错误响应
return jsonify({
    'error': '错误描述',
    'code': 'ERROR_CODE'  # 可选
}), 400/401/404/500
```

#### 3.4 分页 API 模板（必须使用）

```python
# 后端统一分页响应工具
def paginated_response(items: list, total: int, page: int, page_size: int):
    """所有分页 API 必须使用此函数返回"""
    return jsonify({
        'success': True,
        'data': {
            'items': items,  # ⚠️ 固定键名 items
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    })

# 使用示例
@bp.route('/api/projects')
def get_projects():
    pagination = Project.query.paginate(page=page, per_page=per_page)
    return paginated_response(
        items=[p.to_dict() for p in pagination.items],
        total=pagination.total,
        page=page,
        page_size=per_page
    )
```

```javascript
// 前端防御性解析工具
export const getItems = (response) => {
  const data = response.data
  return data?.data?.items    // 标准格式
      || data?.items          // 简化格式
      || data?.projects       // 兼容旧 API
      || data?.employees
      || data?.users
      || []
}
```

---

### 4. Force/Override 参数处理顺序（重要！）

当函数有 `force`、`override`、`skip_check` 等覆盖参数时，**必须先处理覆盖逻辑，再执行常规检查**。

```python
# ❌ 错误顺序 - 状态检查在 force 逻辑之前
def translate_email(email_id, force=False):
    email = get_email(email_id)

    # ❌ 错误：先检查状态，force 永远执行不到
    if email.translation_status == "translating":
        raise HTTPException(409, "正在翻译中")  # force=True 时也会报 409！

    # force 逻辑在后面，被上面的检查拦截了
    if force:
        email.translation_status = None
        db.commit()

    # 开始翻译...

# ✅ 正确顺序 - force 逻辑在状态检查之前
def translate_email(email_id, force=False):
    email = get_email(email_id)

    # ✅ 正确：先处理 force 覆盖
    if force:
        email.translation_status = None  # 清除卡住的状态
        db.commit()
        db.refresh(email)  # 重新加载以确保状态已更新

    # ✅ 正确：然后再检查状态
    if email.translation_status == "translating":
        raise HTTPException(409, "正在翻译中")

    # 开始翻译...
```

**必须遵守此规范的场景：**

| 参数名 | 常见场景 | 说明 |
|-------|---------|------|
| `force=True` | 重新翻译、重新计算 | 强制执行，忽略状态检查 |
| `override=True` | 覆盖现有数据 | 跳过"已存在"检查 |
| `skip_validation=True` | 批量导入 | 跳过格式验证 |
| `ignore_lock=True` | 管理员操作 | 忽略锁定状态 |

**代码审查检查项：**
- [ ] force/override 参数是否在所有检查逻辑之前处理？
- [ ] 清除状态后是否调用了 `db.refresh()` 重新加载？
- [ ] 是否有对应的单元测试覆盖 force=True 场景？

---

### 5. 错误处理

#### 4.1 统一异常处理

```python
from functools import wraps

def handle_exceptions(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except PermissionError as e:
            return jsonify({'error': str(e)}), 403
        except Exception as e:
            # 生产环境不暴露详细错误
            import traceback
            traceback.print_exc()
            return jsonify({'error': '服务器内部错误'}), 500
    return decorated

# 使用
@bp.route('/api/resource', methods=['POST'])
@handle_exceptions
def create_resource():
    # 业务逻辑...
```

---

## 前端开发规范

### 1. 组件设计原则

#### 1.1 受控组件 vs 非受控组件

**关键原则**: 组件要么完全受控（由父组件管理状态），要么完全非受控（自己管理状态），**不要混用**。

```jsx
// ✅ 正确：完全受控组件
function FilterPanel({ statusFilter, onStatusChange, searchText, onSearchChange }) {
  return (
    <div>
      <Select value={statusFilter} onChange={onStatusChange}>
        <Option value="all">全部</Option>
        <Option value="pending">待处理</Option>
      </Select>
      <Input value={searchText} onChange={e => onSearchChange(e.target.value)} />
    </div>
  );
}

// ✅ 正确：完全非受控组件（内部管理状态）
function FilterPanel({ onFilter }) {
  const [status, setStatus] = useState('all');
  const [search, setSearch] = useState('');

  const handleApply = () => {
    onFilter({ status, search });
  };

  return (
    <div>
      <Select value={status} onChange={setStatus}>...</Select>
      <Input value={search} onChange={e => setSearch(e.target.value)} />
      <Button onClick={handleApply}>应用筛选</Button>
    </div>
  );
}
```

```jsx
// ❌ 错误：混合模式 - 接收外部值但试图内部修改
function FilterPanel({ statusFilter, searchKeyword }) {
  // 错误！statusFilter 来自 props，但 setStatusFilter 不存在
  return (
    <Select
      value={statusFilter}
      onChange={setStatusFilter}  // ❌ setStatusFilter 未定义！
    />
  );
}
```

#### 1.2 外部筛选参数的正确处理

当组件接收外部筛选参数时，内部UI应该：

```jsx
// ✅ 方案1：禁用内部筛选控件（推荐）
function Timeline({ statusFilter, searchKeyword }) {
  return (
    <div>
      {/* 只读显示当前筛选状态 */}
      <Select value={statusFilter} disabled />
      <Input value={searchKeyword} disabled />

      {/* 或者完全不显示筛选控件，由父组件处理 */}
    </div>
  );
}

// ✅ 方案2：通过回调通知父组件
function Timeline({ statusFilter, onStatusChange, searchKeyword, onSearchChange }) {
  return (
    <div>
      <Select value={statusFilter} onChange={onStatusChange} />
      <Input value={searchKeyword} onChange={e => onSearchChange(e.target.value)} />
    </div>
  );
}
```

#### 1.3 组件Props设计清单

设计新组件时，必须回答以下问题：

| 问题 | 决策 |
|------|------|
| 这个状态由谁管理？ | 父组件 / 自己 |
| 如果是父组件管理，有onChange回调吗？ | 必须有 |
| 如果是自己管理，需要暴露给父组件吗？ | 通过ref或回调 |

---

### 2. 状态管理

#### 2.1 状态提升原则

```jsx
// ✅ 正确：筛选状态在父组件，子组件只负责显示和回调
function ProjectDetailPage() {
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchText, setSearchText] = useState('');

  return (
    <div>
      <FilterBar
        status={statusFilter}
        onStatusChange={setStatusFilter}
        search={searchText}
        onSearchChange={setSearchText}
      />
      <Timeline
        statusFilter={statusFilter}
        searchKeyword={searchText}
      />
      <Kanban
        statusFilter={statusFilter}
        searchKeyword={searchText}
      />
    </div>
  );
}
```

#### 2.2 避免Props钻透

当props需要传递超过3层时，考虑使用Context：

```jsx
// 创建筛选Context
const FilterContext = createContext();

function ProjectDetailPage() {
  const [filters, setFilters] = useState({ status: 'all', search: '' });

  return (
    <FilterContext.Provider value={{ filters, setFilters }}>
      <FilterBar />
      <Timeline />
      <Kanban />
    </FilterContext.Provider>
  );
}

// 子组件直接使用
function Timeline() {
  const { filters } = useContext(FilterContext);
  // 使用 filters.status, filters.search
}
```

---

### 3. API调用

#### 3.1 禁止使用原生 fetch（重要！）

**所有 API 调用必须使用统一的 axios 实例**，禁止使用原生 `fetch()`。

```javascript
// ❌ 错误写法 - 使用原生 fetch
const response = await fetch("/hr/api/register/requests", {
  credentials: "include"
});
// 问题：没有自动注入 Authorization header，导致 401 错误

// ✅ 正确写法 - 使用统一的 api 实例
import api from '../services/api';
const response = await api.get('/register/requests');
// 好处：自动注入 token，统一错误处理
```

**为什么禁止原生 fetch？**
1. 不会自动注入 JWT token（导致 401 错误）
2. 没有统一的错误处理
3. 没有请求超时控制
4. 响应格式不统一

#### 3.2 API 响应处理规范（重要！）

**响应拦截器行为决定了调用方式。** 必须了解系统的拦截器配置：

| 拦截器返回值 | 调用方访问方式 | 系统示例 |
|-------------|---------------|---------|
| `response` (原始) | `res.data.success` | Portal |
| `response.data` (解包) | `res.success` | SHM, 采购 |

```javascript
// 场景1：拦截器返回原始 response（如 Portal）
api.interceptors.response.use(response => response);  // 不解包

// 调用方式：
const res = await api.get('/customers');
if (res.data.success) {           // ✅ 需要 .data
  setData(res.data.data);
}

// 场景2：拦截器返回 response.data（如 SHM、采购）
api.interceptors.response.use(response => response.data);  // 已解包

// 调用方式：
const res = await api.get('/customers');
if (res.success) {                // ✅ 不需要 .data（已经是 data）
  setData(res.data);
}

// ❌ 常见错误：不了解拦截器行为，导致访问错误
const res = await requirementApi.getByCustomer(id);
if (res.data.success) {  // ❌ 如果拦截器已解包，res.data 是 undefined
  // 报错：Cannot read properties of undefined (reading 'success')
}
```

**防止此类错误的检查清单：**
1. 查看 `api.js` 中的响应拦截器配置
2. 确认返回的是 `response` 还是 `response.data`
3. 调用时使用正确的访问方式

#### 3.3 统一API服务层

```javascript
// services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
});

// 请求拦截器 - 添加Token（所有系统必须配置）
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 - 统一错误处理
// ⚠️ 注意：返回 response 还是 response.data 会影响调用方式！
api.interceptors.response.use(
  response => response,  // 或 response.data（取决于系统设计）
  error => {
    if (error.response?.status === 401) {
      // Token过期，跳转登录
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 导出API方法
export const projectAPI = {
  list: () => api.get('/projects'),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
};

export const taskAPI = {
  list: (projectId) => api.get(`/tasks/project/${projectId}`),
  create: (data) => api.post('/tasks', data),
  update: (id, data) => api.put(`/tasks/${id}`, data),
  // ...
};
```

#### 3.4 错误处理

```jsx
// ✅ 正确：统一错误处理
const handleSubmit = async () => {
  try {
    setLoading(true);
    await taskAPI.create(formData);
    message.success('创建成功');
    onSuccess?.();
  } catch (error) {
    const errorMsg = error.response?.data?.error || '操作失败';
    message.error(errorMsg);
  } finally {
    setLoading(false);
  }
};
```

---

## 数据库规范

### 1. 表命名

```sql
-- 使用小写下划线命名
CREATE TABLE project_files (...);    -- ✅ 正确
CREATE TABLE ProjectFiles (...);     -- ❌ 错误
CREATE TABLE projectfiles (...);     -- ❌ 错误

-- 关联表命名：两个表名按字母顺序 + _mapping
CREATE TABLE project_user_mapping (...);
CREATE TABLE task_tag_mapping (...);
```

### 2. 字段命名

```sql
-- 主键
id INT PRIMARY KEY AUTO_INCREMENT

-- 外键：表名单数 + _id
user_id INT
project_id INT
task_id INT

-- 时间字段
created_at DATETIME DEFAULT CURRENT_TIMESTAMP
updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
deleted_at DATETIME  -- 软删除

-- 布尔字段：is_ 或 has_ 前缀
is_active TINYINT(1) DEFAULT 1
is_deleted TINYINT(1) DEFAULT 0
has_attachment TINYINT(1) DEFAULT 0
```

### 3. 软删除规范

```sql
-- 所有支持软删除的表必须有这两个字段
deleted_at DATETIME DEFAULT NULL COMMENT '删除时间'
deleted_by_id INT DEFAULT NULL COMMENT '删除人ID'

-- 查询时过滤已删除记录
SELECT * FROM projects WHERE deleted_at IS NULL;
```

---

## 代码审查清单

### 后端PR检查项

- [ ] 认证API是否使用 `get_current_user()` 函数模式？
- [ ] 模型是否使用正确的基类（Portal用Base，其他用db.Model）？
- [ ] 是否有未导入就使用的模块？
- [ ] API响应格式是否统一？
- [ ] 是否有适当的错误处理？
- [ ] 数据库操作是否有事务保护？

### 前端PR检查项

- [ ] 组件是完全受控还是完全非受控？（不能混用）
- [ ] 从props接收的值是否有对应的onChange回调？
- [ ] 是否所有使用的变量都已定义？
- [ ] API调用是否有loading状态和错误处理？
- [ ] 是否有内存泄漏风险（useEffect清理）？
- [ ] **是否使用了原生 fetch？（必须改用 axios api 实例）**
- [ ] **API 响应访问方式是否匹配拦截器配置？（res.data.xxx vs res.xxx）**

### 通用检查项

- [ ] 是否更新了相关文档（CLAUDE.md）？
- [ ] 是否有硬编码的配置值？
- [ ] 是否有console.log需要移除？
- [ ] 是否有中文路径/文件名问题？

---

## 常见错误速查

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `NameError: name 'token_required' is not defined` | 使用了不存在的装饰器 | 改用 `get_current_user()` |
| `ImportError: cannot import name 'db' from 'shared.auth.models'` | 错误的ORM导入 | Portal用 `from models import Base` |
| `ReferenceError: xxx is not defined` | 前端使用了未定义的变量 | 检查是否缺少props或state定义 |
| `Cannot read property 'xxx' of undefined` | 访问了null/undefined对象的属性 | 添加可选链 `obj?.xxx` |
| **401 Unauthorized（使用 fetch）** | 原生 fetch 没有自动注入 token | 改用 axios api 实例 |
| **Cannot read properties of undefined (reading 'success')** | API 响应拦截器已解包，但代码访问 `res.data.success` | 检查拦截器配置，改为 `res.success` |
| **ModuleNotFoundError: No module named 'bcrypt'** | shared 模块依赖未同步到子系统 | 更新 requirements.txt，添加 bcrypt>=4.1.2 |
| **SQLAlchemy Enum 值不匹配** | Enum 默认用成员名映射，数据库存的是值 | 添加 `values_callable=lambda x: [e.value for e in x]` |
| **MySQL 不支持 NULLS LAST** | MySQL 语法不兼容 | 使用 CASE 表达式模拟 |
| **FastAPI 422 Unprocessable Entity** | 路由顺序错误，固定路径被参数路由匹配 | 固定路径放在参数路径之前 |
| **SyntaxError: Invalid or unexpected token** | 中文引号 `""` 混入代码 | 使用英文引号 `""` |
| **TypeError: L.map is not a function** | API 返回 `{projects:[]}` 但代码期望 `{items:[]}` | 后端统一用 `items`，前端防御性解析 |
| **409 Conflict（force=true 无效）** | force 逻辑在状态检查之后执行 | force 逻辑必须在检查之前 |

---

## 后端进阶规范

### 5. SQLAlchemy Enum 映射（重要！）

**问题**: SQLAlchemy Enum 默认使用成员名称（如 `ACTIVE`），但数据库通常存储值（如 `active`）。

```python
# ❌ 错误：默认映射，数据库存 'active' 但 Python 期望 'ACTIVE'
class ProjectStatus(Enum):
    ACTIVE = 'active'
    COMPLETED = 'completed'

class Project(Base):
    status = Column(Enum(ProjectStatus))  # 映射失败！

# ✅ 正确：使用 values_callable 让 Enum 按值映射
from sqlalchemy import Enum as SQLEnum

class Project(Base):
    status = Column(
        SQLEnum(ProjectStatus, values_callable=lambda x: [e.value for e in x]),
        default=ProjectStatus.ACTIVE.value
    )
```

**规则**: 所有 Enum 列必须添加 `values_callable` 参数。

---

### 6. MySQL 兼容性

#### 6.1 不支持 NULLS LAST

```python
# ❌ 错误：MySQL 不支持 NULLS LAST
query.order_by(Task.due_date.asc().nulls_last())

# ✅ 正确：使用 CASE 表达式模拟
from sqlalchemy import case

query.order_by(
    case((Task.due_date.is_(None), 1), else_=0),  # NULL 排最后
    Task.due_date.asc()
)
```

#### 6.2 不支持 LIMIT 在子查询

```python
# ❌ 错误：MySQL 不支持子查询中的 LIMIT
subquery = session.query(Task.id).limit(10).subquery()

# ✅ 正确：使用 CTE 或分两步查询
ids = session.query(Task.id).limit(10).all()
tasks = session.query(Task).filter(Task.id.in_([i[0] for i in ids])).all()
```

---

### 7. FastAPI 路由顺序（报价系统）

**问题**: FastAPI 按定义顺序匹配路由，参数路由 `/{id}` 会匹配所有路径。

```python
# ❌ 错误：/expiring 被 /{quote_id} 匹配，导致 422 错误
@router.get("/{quote_id}")
async def get_quote(quote_id: int):
    pass

@router.get("/expiring")  # 永远不会被匹配到！
async def get_expiring():
    pass

# ✅ 正确：固定路径放在参数路径之前
@router.get("/expiring")
async def get_expiring():
    pass

@router.get("/statuses")
async def get_statuses():
    pass

@router.get("/{quote_id}")  # 参数路径放最后
async def get_quote(quote_id: int):
    pass
```

**规则**: 固定路径（如 `/list`, `/stats`, `/export`）必须定义在参数路径（如 `/{id}`）之前。

---

### 8. 共享模块依赖管理

**问题**: `shared/auth` 模块新增依赖时，子系统的 `requirements.txt` 未同步更新。

**必需依赖**: 所有引用 `shared/auth` 的子系统必须包含：

```
bcrypt>=4.1.2        # password_utils.py 使用
PyJWT>=2.8.0         # jwt_utils.py 使用
SQLAlchemy>=2.0.0    # models.py 使用
```

**检查命令**:
```bash
for dir in Portal HR account CRM SHM 报价 采购; do
  echo "=== $dir ==="
  grep -E "bcrypt|PyJWT" "$dir/backend/requirements.txt" || echo "缺失!"
done
```

**规则**: 修改 shared 模块添加新依赖时，必须同步更新所有 7 个子系统的 `requirements.txt`。

---

### 9. SSO 认证路径规范

**问题**: 子系统验证 Token 时使用错误的 Portal API 路径。

```python
# ❌ 错误：/api 被子系统自己的路由拦截
response = requests.get('https://jzchardware.cn/api/auth/verify')

# ✅ 正确：使用 /portal-api 前缀访问 Portal
response = requests.get('https://jzchardware.cn/portal-api/auth/verify')
```

**Nginx 配置**:
```nginx
# Portal API 验证路由（供其他子系统调用）
location /portal-api/ {
    rewrite ^/portal-api/(.*)$ /api/$1 break;
    proxy_pass http://portal-backend;
}
```

---

## 前端进阶规范

### 4. 代码质量检查

#### 4.1 禁止中文标点符号

**问题**: 中文引号 `""` `''` 混入代码导致语法错误。

```javascript
// ❌ 错误：中文引号
const message = "操作成功";  // 编译报错

// ✅ 正确：英文引号
const message = "操作成功";
```

**检查命令**:
```bash
grep -rn "[""'']" src/ --include="*.js" --include="*.jsx"
```

#### 4.2 React 19 兼容性

**问题**: 部分第三方库不兼容 React 19。

| 库 | 问题 | 解决方案 |
|---|------|---------|
| `react-quill` | 不兼容 React 19 | 使用 `react-quill-new` |
| `react-beautiful-dnd` | 废弃 | 使用 `@dnd-kit/core` |
| 旧版 Ant Design | 兼容性警告 | 升级到 v5.x |

**规则**: 新项目使用 React 19 前，检查所有依赖的兼容性。

---

## Nginx 路由规范

### 各系统路由前缀

| 系统 | 前端路径 | API 路径 | 后端 url_prefix | nginx rewrite |
|------|----------|----------|-----------------|---------------|
| Portal | `/` | `/api/` | `/api/xxx` | 不 rewrite |
| HR | `/hr/` | `/hr/api/` | `/api` | `/api/$1` |
| Account | `/account/` | `/account/api/` | 无前缀 | `/$1` |
| SHM | `/shm/` | `/shm/api/` | `/api/xxx` | `/api/$1` |
| CRM | `/crm/` | `/crm/api/` | `/api/xxx` | `/api/$1` |
| 报价 | `/quotation/` | `/quotation/api/` | `/api/xxx` | `/api/$1` |
| 采购 | `/caigou/` | `/caigou/api/` | `/api/v1/xxx` | `/api/$1` |

**Portal API 验证**（供子系统调用）:
```nginx
location /portal-api/ {
    rewrite ^/portal-api/(.*)$ /api/$1 break;
    proxy_pass http://portal-backend;
}
```

---

## 数据库迁移规范

### 1. 新增字段必须同步

**问题**: 代码新增字段，但数据库未执行迁移脚本。

**流程**:
1. 编写迁移脚本放入 `shared/migrations/`
2. 本地测试迁移
3. 部署时执行: `mysql -u root -p database < migration.sql`
4. 更新 CLAUDE.md 文档

### 2. 软删除字段标准

```sql
-- 所有支持软删除的表必须有这两个字段
ALTER TABLE table_name
ADD COLUMN deleted_at DATETIME DEFAULT NULL COMMENT '删除时间',
ADD COLUMN deleted_by_id INT DEFAULT NULL COMMENT '删除人ID';
```

---

## 代码审查清单（更新版）

### 后端PR检查项

- [ ] 认证API是否使用 `get_current_user()` 函数模式？
- [ ] 模型是否使用正确的基类（Portal用Base，其他用db.Model）？
- [ ] Enum 列是否添加了 `values_callable` 参数？
- [ ] SQL 查询是否兼容 MySQL（无 NULLS LAST）？
- [ ] FastAPI 路由顺序是否正确（固定路径在前）？
- [ ] 是否有未导入就使用的模块？
- [ ] API响应格式是否统一？
- [ ] 是否有适当的错误处理？
- [ ] 数据库操作是否有事务保护？
- [ ] **shared 模块新增依赖是否同步到各子系统？**
- [ ] **分页 API 是否统一使用 `items` 作为列表键名？**
- [ ] **force/override 参数是否在状态检查之前处理？**

### 前端PR检查项

- [ ] 组件是完全受控还是完全非受控？（不能混用）
- [ ] 从props接收的值是否有对应的onChange回调？
- [ ] 是否所有使用的变量都已定义？
- [ ] API调用是否有loading状态和错误处理？
- [ ] 是否有内存泄漏风险（useEffect清理）？
- [ ] **是否使用了原生 fetch？（必须改用 axios api 实例）**
- [ ] **API 响应访问方式是否匹配拦截器配置？（res.data.xxx vs res.xxx）**
- [ ] **是否有中文引号混入代码？**
- [ ] **第三方库是否兼容当前 React 版本？**

### 部署前检查项

- [ ] 是否有数据库迁移脚本需要执行？
- [ ] Nginx 路由配置是否正确？
- [ ] 环境变量是否配置完整？
- [ ] 所有系统的 JWT_SECRET_KEY 是否一致？
- [ ] **requirements.txt 依赖是否完整？**

---

## 安全规范

### 10.1 敏感信息管理

**禁止在代码中硬编码任何敏感信息：**

```python
# ❌ 严禁：硬编码密码/密钥
JWT_SECRET_KEY = 'jzc-dev-shared-secret-key-2025'
DB_PASSWORD = 'exak472008'
ROOT_PASSWORDS = ['root', 'admin123']

# ✅ 正确：从环境变量读取
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY 环境变量必须设置")
```

**规则：**
- 所有密码、密钥、Token 必须从环境变量或密钥管理系统读取
- `.env` 文件必须添加到 `.gitignore`
- 生产环境必须使用强随机密钥（至少 32 字符）

---

### 10.2 CORS 配置

```python
# ❌ 错误：允许所有来源
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')

# ❌ 错误：默认值为 *
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

# ✅ 正确：无默认值，强制配置
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')
if not CORS_ORIGINS or CORS_ORIGINS == ['']:
    raise ValueError("CORS_ORIGINS 环境变量必须设置")
```

**规则：** 生产环境 CORS 必须显式配置允许的域名列表，禁止使用 `*`。

---

### 10.3 登录速率限制

所有登录接口必须添加速率限制，防止暴力破解：

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # 每分钟最多 5 次
def login():
    # 登录逻辑
```

**规则：** 登录接口限制为每分钟 5 次，连续失败 5 次锁定账户 30 分钟。

---

### 10.4 安全HTTP头

所有系统必须设置以下安全响应头：

```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'  # 防止点击劫持
    response.headers['X-Content-Type-Options'] = 'nosniff'  # 防止 MIME 嗅探
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'  # 强制 HTTPS
    response.headers['X-XSS-Protection'] = '1; mode=block'  # XSS 保护
    return response
```

---

### 10.5 文件上传验证

文件上传必须验证以下内容：

```python
import magic
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/png', 'image/jpeg'
}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def validate_upload(file):
    # 1. 检查扩展名
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return False, '文件类型不允许'

    # 2. 检查文件大小
    file.seek(0, 2)  # 移到文件末尾
    size = file.tell()
    file.seek(0)  # 重置位置
    if size > MAX_FILE_SIZE:
        return False, '文件过大（最大 100MB）'

    # 3. 检查 MIME 类型
    mime_type = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)
    if mime_type not in ALLOWED_MIME_TYPES:
        return False, 'MIME 类型不允许'

    # 4. 清理文件名
    safe_filename = secure_filename(file.filename)

    return True, safe_filename
```

---

## 性能规范

### 11.1 禁止 N+1 查询

```python
# ❌ 错误：循环内查询数据库
projects = Project.query.all()
for project in projects:
    tasks = Task.query.filter_by(project_id=project.id).all()  # N 次查询！

# ✅ 正确：使用预加载
from sqlalchemy.orm import joinedload, selectinload

# joinedload: 使用 JOIN 一次查询
projects = session.query(Project).options(joinedload(Project.tasks)).all()

# selectinload: 使用 IN 子查询（推荐用于一对多）
projects = session.query(Project).options(selectinload(Project.tasks)).all()
```

**规则：** 所有关联数据必须使用 `joinedload` 或 `selectinload` 预加载。

---

### 11.2 禁止一次加载全部数据

```python
# ❌ 错误：加载全部数据到内存
all_customers = Customer.query.all()
customer_ids = [c.id for c in all_customers]

# ✅ 正确：只查询需要的字段
customer_ids = [row[0] for row in db.session.query(Customer.id).all()]

# ✅ 正确：分页查询
page = request.args.get('page', 1, type=int)
per_page = request.args.get('per_page', 20, type=int)
customers = Customer.query.paginate(page=page, per_page=per_page)

# ✅ 正确：流式处理大数据
def export_customers():
    for customer in Customer.query.yield_per(100):  # 每次处理 100 条
        yield customer.to_csv_row()
```

**规则：**
- 禁止 `.all()` 加载超过 1000 条记录
- 列表查询必须分页
- 导出功能必须使用流式处理

---

### 11.3 必须添加数据库索引

经常用于查询的字段必须有索引：

```sql
-- 外键字段（必须）
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);

-- 状态字段（必须）
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_orders_status ON orders(status);

-- 复合索引（推荐）
CREATE INDEX idx_tasks_project_status ON tasks(project_id, status);
CREATE INDEX idx_orders_customer_date ON orders(customer_id, created_at);

-- 搜索字段
CREATE INDEX idx_customers_name ON customers(name);
CREATE INDEX idx_products_code ON products(product_code);
```

**规则：** 新增模型时，必须为外键、状态、时间、搜索字段添加索引。

---

## 异常处理规范

### 12.1 禁止静默忽略异常

```python
# ❌ 严禁：完全忽略异常
try:
    setattr(obj, name, value)
except Exception:
    pass  # 危险！错误被隐藏

# ❌ 禁止：捕获过于宽泛且返回原始错误
except Exception as e:
    return {'error': str(e)}, 500  # 可能暴露敏感信息

# ✅ 正确：区分异常类型，记录日志
import logging
logger = logging.getLogger(__name__)

try:
    process_order(data)
except ValidationError as e:
    logger.warning(f"验证失败: {e}")
    return {'error': str(e)}, 400
except PermissionError as e:
    logger.warning(f"权限不足: {e}")
    return {'error': str(e)}, 403
except Exception as e:
    logger.error(f"处理订单失败: {e}", exc_info=True)  # 记录完整堆栈
    return {'error': '服务器内部错误'}, 500  # 不暴露详细信息
```

**规则：**
- 禁止 `except: pass` 或 `except Exception: pass`
- 所有异常必须记录日志
- 生产环境不向用户暴露详细错误信息

---

### 12.2 HTTP 状态码规范

| 场景 | 状态码 | 说明 |
|------|--------|------|
| 请求成功 | 200 | OK |
| 创建成功 | 201 | Created |
| 请求参数错误 | 400 | Bad Request |
| 未认证 | 401 | Unauthorized |
| 无权限 | 403 | Forbidden |
| 资源不存在 | 404 | Not Found |
| 资源冲突 | 409 | Conflict |
| 服务器错误 | 500 | Internal Server Error |

---

## 事务处理规范

### 13.1 多表操作必须使用事务

```python
# ❌ 错误：无事务保护，可能部分成功
order.status = 'confirmed'
db.session.flush()  # 这不是 commit！
db.session.query(OrderLine).filter(...).delete()
db.session.add(new_order_line)
db.session.commit()  # 如果这里失败，delete 已执行但未回滚

# ✅ 正确：完整事务保护
try:
    order.status = 'confirmed'
    db.session.query(OrderLine).filter(OrderLine.order_id == order.id).delete()
    db.session.add(new_order_line)
    db.session.commit()
except Exception as e:
    db.session.rollback()
    logger.error(f"订单更新失败: {e}", exc_info=True)
    raise

# ✅ 推荐：使用上下文管理器
from contextlib import contextmanager

@contextmanager
def transaction_scope(session):
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise

with transaction_scope(db.session) as session:
    order.status = 'confirmed'
    session.query(OrderLine).filter(...).delete()
    session.add(new_order_line)
```

---

### 13.2 级联删除必须配置

```python
# ❌ 错误：无级联配置，删除父记录后子记录孤立
class Project(Base):
    tasks = relationship('Task')  # 删除项目后，任务仍存在但 project_id 无效

# ✅ 正确：配置级联删除
class Project(Base):
    tasks = relationship('Task', cascade='all, delete-orphan', back_populates='project')
    files = relationship('ProjectFile', cascade='all, delete-orphan')
    members = relationship('ProjectMember', cascade='all, delete-orphan')
```

**级联选项：**
- `delete-orphan`: 父记录删除时，删除所有子记录
- `all`: 包含 save-update, merge, refresh-expire, expunge, delete
- `delete`: 仅删除操作级联

---

## 数据验证规范

### 14.1 API 输入必须验证

```python
# ❌ 错误：无验证直接使用
@bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    order = Order(
        order_no=data.get('order_no'),  # 可能为 None
        qty=int(data.get('qty', 0)),  # 类型转换可能失败
    )

# ✅ 正确：使用 Pydantic 验证（推荐）
from pydantic import BaseModel, Field, validator

class CreateOrderRequest(BaseModel):
    order_no: str = Field(..., min_length=1, max_length=50)
    qty: int = Field(..., gt=0)
    customer_id: int

    @validator('order_no')
    def order_no_format(cls, v):
        if not v.startswith('ORD-'):
            raise ValueError('订单号必须以 ORD- 开头')
        return v

@bp.route('/orders', methods=['POST'])
def create_order():
    try:
        req = CreateOrderRequest(**request.get_json())
    except ValidationError as e:
        return {'error': '参数验证失败', 'details': e.errors()}, 400

    order = Order(order_no=req.order_no, qty=req.qty)
```

---

### 14.2 数据库约束必须定义

```python
# ❌ 错误：无约束
class Employee(Base):
    department_id = Column(Integer)  # 可以是任意值，包括不存在的部门

# ✅ 正确：定义外键约束
class Employee(Base):
    department_id = Column(
        Integer,
        ForeignKey('departments.id', ondelete='RESTRICT'),  # 禁止删除有员工的部门
        nullable=False
    )

    # 其他约束
    emp_no = Column(String(50), unique=True, nullable=False)  # 唯一且非空
    salary = Column(Numeric(12, 2), CheckConstraint('salary >= 0'))  # 检查约束
```

**常用约束：**
- `nullable=False`: 非空
- `unique=True`: 唯一
- `ForeignKey(..., ondelete='RESTRICT')`: 外键约束，阻止删除被引用的记录
- `ForeignKey(..., ondelete='CASCADE')`: 级联删除
- `ForeignKey(..., ondelete='SET NULL')`: 删除时设为 NULL
- `CheckConstraint('column >= 0')`: 检查约束

---

## 代码审查清单（更新版）

### 后端PR检查项

- [ ] 认证API是否使用 `get_current_user()` 函数模式？
- [ ] 模型是否使用正确的基类（Portal用Base，其他用db.Model）？
- [ ] Enum 列是否添加了 `values_callable` 参数？
- [ ] SQL 查询是否兼容 MySQL（无 NULLS LAST）？
- [ ] FastAPI 路由顺序是否正确（固定路径在前）？
- [ ] 是否有未导入就使用的模块？
- [ ] API响应格式是否统一？
- [ ] 是否有适当的错误处理？
- [ ] 数据库操作是否有事务保护？
- [ ] **shared 模块新增依赖是否同步到各子系统？**
- [ ] **分页 API 是否统一使用 `items` 作为列表键名？**
- [ ] **force/override 参数是否在状态检查之前处理？**

### 安全检查项（新增）

- [ ] **是否有硬编码的密码/密钥/Token？**
- [ ] **CORS 是否配置为 `*`？**
- [ ] **登录接口是否有速率限制？**
- [ ] **是否设置了安全HTTP头？**
- [ ] **文件上传是否验证了 MIME 类型和大小？**
- [ ] **敏感操作是否记录了审计日志？**

### 性能检查项（新增）

- [ ] **是否有循环内的数据库查询（N+1）？**
- [ ] **是否有 `.all()` 一次加载全部数据（>1000条）？**
- [ ] **经常查询的字段是否有索引？**
- [ ] **关联查询是否使用了 joinedload/selectinload？**

### 代码质量检查项（新增）

- [ ] **是否有 `except: pass` 静默忽略异常？**
- [ ] **异常是否记录了日志？**
- [ ] **多表操作是否在事务中？**
- [ ] **API输入是否有验证？**
- [ ] **外键是否定义了约束？**
- [ ] **级联删除是否正确配置？**

### 前端PR检查项

- [ ] 组件是完全受控还是完全非受控？（不能混用）
- [ ] 从props接收的值是否有对应的onChange回调？
- [ ] 是否所有使用的变量都已定义？
- [ ] API调用是否有loading状态和错误处理？
- [ ] 是否有内存泄漏风险（useEffect清理）？
- [ ] **是否使用了原生 fetch？（必须改用 axios api 实例）**
- [ ] **API 响应访问方式是否匹配拦截器配置？（res.data.xxx vs res.xxx）**
- [ ] **是否有中文引号混入代码？**
- [ ] **第三方库是否兼容当前 React 版本？**

### 部署前检查项

- [ ] 是否有数据库迁移脚本需要执行？
- [ ] Nginx 路由配置是否正确？
- [ ] 环境变量是否配置完整？
- [ ] 所有系统的 JWT_SECRET_KEY 是否一致？
- [ ] **requirements.txt 依赖是否完整？**

---

## API 响应格式规范

### 15.1 统一使用 shared/api_response.py

所有子系统必须使用统一的 API 响应格式模块：

```python
# Flask 系统
from shared.api_response import APIResponse, ErrorCodes, handle_exceptions

@bp.route('/api/users/<int:id>')
@handle_exceptions  # 自动捕获异常并返回标准格式
def get_user(id):
    user = User.query.get(id)
    if not user:
        return APIResponse.not_found('用户不存在')
    return APIResponse.success(data=user.to_dict())

# 分页响应
@bp.route('/api/users')
def list_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = User.query.paginate(page=page, per_page=per_page)
    return APIResponse.paginated(
        items=[u.to_dict() for u in pagination.items],
        total=pagination.total,
        page=page,
        per_page=per_page
    )
```

```python
# FastAPI 系统（报价）
from shared.api_response import FastAPIResponse

@app.get('/api/quotes/{id}')
async def get_quote(id: int):
    quote = await get_quote_by_id(id)
    if not quote:
        raise FastAPIResponse.not_found('报价不存在')
    return FastAPIResponse.success(data=quote.dict())
```

### 15.2 标准响应格式

```json
// 成功响应
{
    "success": true,
    "message": "操作成功",
    "data": {...},
    "meta": {
        "pagination": {
            "total": 100,
            "page": 1,
            "per_page": 20,
            "total_pages": 5
        }
    }
}

// 错误响应
{
    "success": false,
    "error": "用户不存在",
    "code": "NOT_FOUND",
    "details": {...}
}
```

### 15.3 标准错误代码

使用 `ErrorCodes` 类中定义的标准代码：

| 代码 | HTTP状态码 | 说明 |
|------|-----------|------|
| TOKEN_MISSING | 401 | Token 缺失 |
| TOKEN_INVALID | 401 | Token 无效 |
| TOKEN_EXPIRED | 401 | Token 过期 |
| PERMISSION_DENIED | 403 | 权限不足 |
| RESOURCE_NOT_FOUND | 404 | 资源不存在 |
| VALIDATION_FAILED | 422 | 验证失败 |
| DATABASE_ERROR | 500 | 数据库错误 |

---

## 关系和约束规范

### 16.1 级联删除配置

父子关系必须配置级联删除，确保数据完整性：

```python
# ✅ 正确：配置级联删除
class Project(Base):
    tasks = relationship('Task', back_populates='project',
                        cascade='all, delete-orphan',
                        passive_deletes=True)

class Task(Base):
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'))
    project = relationship('Project', back_populates='tasks')
```

```python
# ❌ 错误：无级联配置
class Project(Base):
    tasks = relationship('Task')  # 删除项目不会删除任务

class Task(Base):
    project_id = Column(Integer, ForeignKey('projects.id'))  # 无 ondelete
```

### 16.2 外键约束类型

| 约束类型 | 使用场景 | 示例 |
|---------|---------|------|
| CASCADE | 删除父记录时自动删除子记录 | 项目→任务 |
| RESTRICT | 禁止删除有子记录的父记录 | 部门→员工 |
| SET NULL | 删除父记录时将子记录外键设为NULL | 分类→商品 |

```python
# 禁止删除有员工的部门
department_id = Column(Integer, ForeignKey('departments.id', ondelete='RESTRICT'))

# 删除项目时自动删除任务
project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'))

# 删除分类时商品的分类ID设为NULL
category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'))
```

### 16.3 关系定义检查清单

- [ ] 是否定义了 `back_populates` 双向关系？
- [ ] 是否配置了 `cascade='all, delete-orphan'`（父表）？
- [ ] 是否配置了 `ondelete='CASCADE/RESTRICT'`（子表 ForeignKey）？
- [ ] 是否有对应的数据库迁移脚本？

---

## Bug 修复记录

### 2025-12-26 修复

| # | 系统 | 问题 | 根因 | 修复方案 | Commit |
|---|------|------|------|---------|--------|
| 1 | Portal | 邮件导入点击按钮后页面崩溃跳转首页 | API 响应格式不一致：`projects` API 返回 `{projects:[]}` 而非 `{items:[]}` | 前端防御性解析 `res.data?.projects \|\| res.data?.items \|\| []` | `b352d2c` |
| 2 | 邮件系统 | 强制翻译返回 409 Conflict | `force=true` 时先检查状态再清除，逻辑顺序错误 | 将 force 清除逻辑移到状态检查之前 | `07e4819` |

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2025-12-22 | 初始版本，包含认证、ORM、组件设计规范 |
| 1.1 | 2025-12-24 | 新增 API 调用规范：禁止原生 fetch、响应拦截器行为说明 |
| 1.2 | 2025-12-25 | 大版本更新，新增：SQLAlchemy Enum 映射、MySQL 兼容性、FastAPI 路由顺序、共享模块依赖管理、SSO 认证路径、中文标点检查、React 19 兼容性、Nginx 路由规范、数据库迁移规范、更新代码审查清单 |
| 2.0 | 2025-12-25 | **深度审计更新**：新增安全规范（敏感信息/CORS/速率限制/HTTP头/文件上传）、性能规范（N+1/分页/索引）、异常处理规范、事务处理规范、数据验证规范，更新代码审查清单（新增安全/性能/代码质量检查项） |
| 2.1 | 2025-12-25 | 新增 API 响应格式规范（shared/api_response.py 使用指南）、关系和约束规范（级联删除/外键约束配置） |
| 2.2 | 2025-12-26 | **新增**：API 分页列表键名规范（必须用 `items`）、Force/Override 参数处理顺序规范、Bug 修复记录表 |

---

> **维护说明**: 发现新的标准化问题时，请及时更新此文档并通知团队。
