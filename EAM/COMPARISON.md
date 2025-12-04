# EAM vs PM 系统对比

## 系统定位

### PM系统（生产管理系统）
- **全称**: Production Management
- **定位**: 综合生产管理系统
- **端口**: 前端5173 / 后端8003
- **模块**: 生产计划、设备管理、工艺管理、质量管理等

### EAM系统（设备资产管理系统）
- **全称**: Enterprise Asset Management
- **定位**: 专业设备资产管理系统
- **端口**: 前端7200 / 后端8005
- **模块**: 设备台账、产能配置、维护记录（专注设备管理）

## 功能对比

| 功能模块 | PM系统 | EAM系统 | 说明 |
|---------|--------|---------|------|
| 设备台账 | ✅ | ✅ | EAM从PM复制并优化 |
| 生产计划 | ✅ | ❌ | PM独有 |
| 工艺管理 | ✅ | ❌ | PM独有 |
| 设备维护 | ⚠️ | ✅ | EAM专业化 |
| 产能配置 | ⚠️ | ✅ | EAM专业化 |
| 备件管理 | ❌ | 🔜 | EAM未来扩展 |
| 成本分析 | ❌ | 🔜 | EAM未来扩展 |

## 技术栈对比

### 后端

| 技术 | PM系统 | EAM系统 | 备注 |
|------|--------|---------|------|
| 框架 | Flask 3.1.0 | Flask 3.1.0 | 相同 |
| ORM | SQLAlchemy | SQLAlchemy | 相同 |
| 数据库 | MySQL (cncplan) | MySQL (cncplan) | 共享数据库 |
| 端口 | 8003 | 8005 | 不同端口避免冲突 |

### 前端

| 技术 | PM系统 | EAM系统 | 备注 |
|------|--------|---------|------|
| 框架 | React 19 | React 19 | 相同 |
| UI库 | 自定义UI | Ant Design 5 | EAM使用专业组件库 |
| 构建工具 | Vite | Vite 7 | 相同 |
| 端口 | 5173 | 7200 | 不同端口 |

## 数据表对比

### machines表（共享）

两个系统共享同一张 `machines` 表，字段完全一致：

```sql
CREATE TABLE machines (
  id INT PRIMARY KEY AUTO_INCREMENT,
  machine_code VARCHAR(64) UNIQUE NOT NULL,
  name VARCHAR(128) NOT NULL,
  model VARCHAR(128),
  dept_name VARCHAR(64),
  factory_location VARCHAR(16),
  brand VARCHAR(64),
  serial_no VARCHAR(64),
  manufacture_date DATE,
  purchase_date DATE,
  place VARCHAR(128),
  manufacturer VARCHAR(128),
  capacity INT,
  status VARCHAR(16),
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**注意**: 两个系统操作同一张表，数据完全同步。

## 代码来源

### 从PM复制的文件

#### 后端
- ✅ `backend/app/models/machine.py` - 从 PM 完整复制
- ✅ `backend/app/routes/machines.py` - 从 PM 完整复制

#### 前端
- ✅ 设备管理逻辑 - 从 PM 的 `Machines.jsx` 参考
- 🔄 UI实现 - 重构为 Ant Design 组件

### 新创建的文件

#### 后端
- `backend/main.py` - Flask应用入口（参考SCM）
- `backend/app/__init__.py` - Flask工厂（参考SCM）
- `backend/.env` - 环境配置（端口8005）
- `backend/requirements.txt` - 依赖清单

#### 前端
- `frontend/src/App.jsx` - 主应用（参考SCM，菜单中文化）
- `frontend/src/pages/machines/MachineList.jsx` - 设备列表（Ant Design实现）
- `frontend/src/services/api.js` - API封装
- `frontend/package.json` - 依赖清单
- `frontend/vite.config.js` - Vite配置（端口7200，代理8005）

## 界面对比

### PM系统 - 设备管理界面
- 使用自定义UI组件
- 表单布局：4列网格（form-4col）
- 样式类：ui-card, ui-input, ui-btn
- 简洁的搜索和表格

### EAM系统 - 设备管理界面
- 使用 Ant Design 组件库
- 表单布局：Modal + 响应式Grid（2列）
- 组件：Table, Modal, Form, Button, Card
- 专业的搜索、分页、排序
- 更丰富的交互体验

## API对比

### PM系统
```
GET  /api/machines          - 列表
POST /api/machines          - 创建
GET  /api/machines/{id}     - 详情
PUT  /api/machines/{id}     - 更新
DELETE /api/machines/{id}   - 删除
POST /api/machines/list     - 列表（兼容）
```

### EAM系统
```
GET  /api/machines          - 列表（相同）
POST /api/machines          - 创建（相同）
GET  /api/machines/{id}     - 详情（相同）
PUT  /api/machines/{id}     - 更新（相同）
DELETE /api/machines/{id}   - 删除（相同）
POST /api/machines/list     - 列表（兼容，相同）
```

**API完全兼容**，可以无缝切换。

## 使用场景

### 使用PM系统设备模块的场景
1. 需要结合生产计划使用设备信息
2. 需要从生产角度管理设备
3. 简单的设备信息录入和查询

### 使用EAM系统的场景
1. 专业的设备资产管理
2. 需要详细的设备维护记录
3. 需要设备生命周期管理
4. 需要设备成本分析
5. 需要备件库存管理
6. 独立的设备管理部门使用

## 数据同步

由于两个系统共享同一张 `machines` 表：

### 优点
- ✅ 数据实时同步，无需额外同步机制
- ✅ 在任一系统创建/更新的设备，另一系统立即可见
- ✅ 避免数据冗余和不一致

### 注意事项
- ⚠️ 删除操作会影响两个系统
- ⚠️ 字段更新会同时反映在两个系统
- ⚠️ 建议根据使用场景选择合适的系统操作

## 未来发展

### EAM系统扩展方向
1. **维护管理**
   - 预防性维护计划
   - 维修工单管理
   - 维护历史记录
   - 维护成本统计

2. **备件管理**
   - 备件库存
   - 备件采购
   - 备件消耗统计

3. **设备监控**
   - 设备状态实时监控
   - 故障预警
   - 运行效率分析

4. **资产管理**
   - 资产折旧计算
   - 投资回报分析
   - 设备价值评估

### PM系统保持方向
- 继续专注生产管理
- 设备模块保持轻量级
- 与EAM系统数据互通

## 迁移建议

### 从PM迁移到EAM
如果您主要使用设备管理功能，建议：

1. 数据无需迁移（共享数据库）
2. 用户逐步切换到EAM系统
3. 享受更专业的设备管理功能

### 同时使用两个系统
完全可行：

1. PM系统：用于生产计划相关的设备信息查询
2. EAM系统：用于专业设备管理（维护、备件等）
3. 数据自动同步，无需手动维护

## 总结

| 对比项 | PM系统 | EAM系统 |
|-------|--------|---------|
| 定位 | 生产管理 | 设备资产管理 |
| 功能广度 | 广泛（多模块） | 专注（设备） |
| 功能深度 | 浅（通用） | 深（专业） |
| UI体验 | 简洁实用 | 专业美观 |
| 适用对象 | 生产部门 | 设备部门 |
| 数据源 | 共享数据库 | 共享数据库 |
| 独立性 | 独立系统 | 独立系统 |

**推荐**: 根据使用场景选择合适的系统，或同时使用两个系统发挥各自优势。
