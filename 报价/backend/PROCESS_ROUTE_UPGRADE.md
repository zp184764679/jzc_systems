# 工艺路线（ProcessRoute）模块升级说明

## 升级概述

本次升级将报价系统的工艺路线模块整合了PM系统的模板化功能，实现了以下核心改进：

1. **独立的模型文件**：将ProcessRoute从quote.py迁移到独立的process_route.py
2. **模板化功能**：支持创建和使用工艺路线模板
3. **多对象关联**：支持关联Product、Drawing、Quote三种对象
4. **独立的工序步骤表**：ProcessRouteStep独立管理，支持详细的工艺参数
5. **完整的API接口**：提供CRUD、模板管理、成本计算等完整功能

---

## 数据库变更

### 新增表：process_routes（升级版）

```sql
-- 主表：工艺路线
CREATE TABLE process_routes (
    id INTEGER PRIMARY KEY,
    route_code VARCHAR(64) UNIQUE NOT NULL,           -- 路线编码
    name VARCHAR(128),                                 -- 路线名称

    -- 关联对象（支持三种方式）
    product_id INTEGER,                                -- 关联产品
    drawing_id INTEGER,                                -- 关联图纸
    quote_id INTEGER,                                  -- 关联报价

    -- 模板功能
    is_template BOOLEAN DEFAULT FALSE,                 -- 是否为模板
    template_name VARCHAR(128),                        -- 模板名称
    template_category VARCHAR(64),                     -- 模板分类

    -- 版本管理
    version VARCHAR(32) DEFAULT '1.0',                 -- 版本号

    -- 成本汇总
    total_cost DECIMAL(12,4) DEFAULT 0,                -- 总成本
    total_time FLOAT DEFAULT 0,                        -- 总工时（分钟）

    -- 其他
    description TEXT,                                  -- 说明
    is_active BOOLEAN DEFAULT TRUE,                    -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    created_by INTEGER,

    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (drawing_id) REFERENCES drawings(id),
    FOREIGN KEY (quote_id) REFERENCES quotes(id)
);

CREATE INDEX idx_route_code ON process_routes(route_code);
CREATE INDEX idx_is_template ON process_routes(is_template);
```

### 新增表：process_route_steps

```sql
-- 子表：工序步骤
CREATE TABLE process_route_steps (
    id INTEGER PRIMARY KEY,
    route_id INTEGER NOT NULL,                         -- 路线ID
    process_id INTEGER NOT NULL,                       -- 工艺ID

    -- 顺序
    sequence INTEGER DEFAULT 0,                        -- 工序顺序

    -- 部门和设备
    department VARCHAR(64),                            -- 部门
    machine VARCHAR(128),                              -- 设备
    machine_model VARCHAR(128),                        -- 设备型号

    -- 工时预估
    estimate_minutes INTEGER,                          -- 预计工时（分钟）
    setup_time FLOAT DEFAULT 0,                        -- 段取时间（小时）

    -- 成本信息
    labor_cost DECIMAL(10,4) DEFAULT 0,                -- 人工成本
    machine_cost DECIMAL(10,4) DEFAULT 0,              -- 机器成本
    tool_cost DECIMAL(10,4) DEFAULT 0,                 -- 刀具成本
    material_cost DECIMAL(10,4) DEFAULT 0,             -- 辅料成本
    other_cost DECIMAL(10,4) DEFAULT 0,                -- 其他成本
    total_cost DECIMAL(10,4) DEFAULT 0,                -- 该工序总成本

    -- 生产参数
    daily_output INTEGER,                              -- 日产量（件/天）
    defect_rate FLOAT DEFAULT 0,                       -- 不良率

    -- 工艺参数
    process_parameters TEXT,                           -- 工艺参数JSON

    -- 其他
    remarks TEXT,                                      -- 备注
    is_active BOOLEAN DEFAULT TRUE,                    -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,

    FOREIGN KEY (route_id) REFERENCES process_routes(id) ON DELETE CASCADE,
    FOREIGN KEY (process_id) REFERENCES processes(id)
);

CREATE INDEX idx_route_id ON process_route_steps(route_id);
```

### 迁移旧数据（如果存在）

如果系统中已有旧的process_routes表数据，需要执行以下迁移：

```python
# 迁移脚本示例（需要根据实际情况调整）
from models.process_route import ProcessRoute as NewProcessRoute, ProcessRouteStep
from models.quote import ProcessRoute as OldProcessRoute  # 假设旧模型还在

def migrate_old_routes(db):
    """迁移旧的工艺路线数据"""
    old_routes = db.query(OldProcessRoute).all()

    for old_route in old_routes:
        # 生成新的路线编码
        new_code = f"ROUTE-OLD-{old_route.id}"

        # 创建新的工艺路线（作为步骤）
        # 注意：旧模型是单个工序，新模型是完整路线
        # 这里假设每个旧工序创建一个单步骤的路线
        new_route = NewProcessRoute(
            route_code=new_code,
            name=f"迁移路线-{old_route.id}",
            drawing_id=old_route.drawing_id,
            is_template=False,
            version="1.0"
        )
        db.add(new_route)
        db.flush()

        # 创建步骤
        step = ProcessRouteStep(
            route_id=new_route.id,
            process_id=old_route.process_id,
            sequence=old_route.sequence_number,
            estimate_minutes=int(float(old_route.estimated_time or 0) * 60),
            setup_time=float(old_route.setup_time or 0),
            labor_cost=old_route.labor_cost,
            machine_cost=old_route.machine_cost,
            tool_cost=old_route.tool_cost,
            total_cost=old_route.total_cost,
            remarks=old_route.remark
        )
        db.add(step)

    db.commit()
```

---

## API端点清单

### 基础CRUD

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/routes` | 获取工艺路线列表（支持筛选） |
| POST | `/api/routes` | 创建工艺路线 |
| GET | `/api/routes/{route_id}` | 获取工艺路线详情 |
| PUT | `/api/routes/{route_id}` | 更新工艺路线 |
| DELETE | `/api/routes/{route_id}` | 删除工艺路线 |

### 模板管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/routes/templates/list` | 获取模板列表 |
| POST | `/api/routes/from-template/{template_id}` | 从模板创建路线 |

### 关联对象查询

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/products/{product_id}/routes` | 获取产品的所有路线 |
| GET | `/api/drawings/{drawing_id}/routes` | 获取图纸的所有路线 |
| GET | `/api/quotes/{quote_id}/routes` | 获取报价的所有路线 |

### 成本计算

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/routes/{route_id}/calculate` | 计算路线总成本 |

---

## 前端API方法

### 新增的前端API方法（src/services/api.js）

```javascript
// 获取工艺路线列表
getProcessRouteList(params)

// 获取工艺路线详情
getProcessRoute(routeId)

// 创建工艺路线
createProcessRoute(data)

// 更新工艺路线
updateProcessRoute(routeId, data)

// 删除工艺路线
deleteProcessRoute(routeId)

// 从模板创建工艺路线
createRouteFromTemplate(templateId, params)

// 获取工艺路线模板列表
getProcessRouteTemplates(params)

// 计算工艺路线成本
calculateRouteCost(routeId)

// 获取产品的所有工艺路线
getProductRoutes(productId)

// 获取图纸的所有工艺路线
getDrawingRoutes(drawingId)

// 获取报价的所有工艺路线
getQuoteRoutes(quoteId)
```

---

## 与PM系统的功能对比

| 功能 | PM系统 | 报价系统（升级后） | 说明 |
|------|--------|-------------------|------|
| 工艺路线模板 | ✅ | ✅ | 完全支持，增加了分类功能 |
| 从模板创建 | ✅ | ✅ | 支持克隆模板到实际对象 |
| 多对象关联 | Product + ProjectTask | Product + Drawing + Quote | 报价系统扩展了关联类型 |
| 工序步骤管理 | ✅ | ✅ | 独立的步骤表，支持更多字段 |
| 成本计算 | ✅ | ✅ | 支持分类成本汇总 |
| 版本管理 | ✅ | ✅ | 支持版本号字段 |
| 部门/设备 | ✅ | ✅ | 完全支持 |
| 工艺参数 | ✅ | ✅ | JSON格式存储详细参数 |
| 启用/停用 | ✅ | ✅ | 支持软删除 |

---

## 使用示例

### 1. 创建工艺路线模板

```python
# 创建模板
template_data = {
    "route_code": "TPL-CNC-001",
    "name": "CNC加工标准路线",
    "is_template": True,
    "template_name": "CNC加工标准路线",
    "template_category": "CNC加工",
    "version": "1.0",
    "description": "适用于标准CNC加工零件",
    "steps": [
        {
            "process_id": 1,  # 粗车
            "sequence": 1,
            "department": "车间1",
            "machine": "CNC车床",
            "estimate_minutes": 30,
            "setup_time": 0.5,
            "labor_cost": 50,
            "machine_cost": 80,
            "total_cost": 130
        },
        {
            "process_id": 2,  # 精车
            "sequence": 2,
            "department": "车间1",
            "machine": "CNC车床",
            "estimate_minutes": 45,
            "setup_time": 0.3,
            "labor_cost": 70,
            "machine_cost": 100,
            "total_cost": 170
        }
    ]
}

# 调用API
response = createProcessRoute(template_data)
```

### 2. 从模板创建实际工艺路线

```python
# 从模板创建
template_id = 1
params = {
    "product_id": 100,
    "quote_id": 200
}

# 调用API
route = createRouteFromTemplate(template_id, params)
# 自动生成新的route_code，复制所有步骤
```

### 3. 获取产品的工艺路线

```python
# 获取产品的所有工艺路线
product_id = 100
routes = getProductRoutes(product_id)

# 显示路线列表
for route in routes:
    print(f"{route.route_code}: {route.name}")
    print(f"  总成本: {route.total_cost}")
    print(f"  总工时: {route.total_time}分钟")
    print(f"  工序数: {route.steps_count}")
```

### 4. 计算工艺路线成本

```python
# 重新计算成本
route_id = 1
result = calculateRouteCost(route_id)

# 结果包含：
# - total_cost: 总成本
# - total_time_minutes: 总工时
# - total_labor_cost: 人工成本合计
# - total_machine_cost: 机器成本合计
# - total_tool_cost: 刀具成本合计
# - steps_count: 工序数量
```

---

## 注意事项

### 1. 旧模型已移除

- 原 `models/quote.py` 中的 `ProcessRoute` 类已移除
- 新模型位于 `models/process_route.py`
- 如果有代码引用旧模型，需要更新导入语句

### 2. 表名冲突处理

- 新旧模型都使用 `process_routes` 表名
- 建议在升级前备份数据库
- 首次运行会自动创建新表结构（如果使用SQLite的create_all）

### 3. 关联关系

- Product模型会自动获得 `process_routes` 关系（通过backref）
- Drawing模型会自动获得 `process_routes` 关系
- Quote模型会自动获得 `process_routes` 关系

### 4. 级联删除

- 删除工艺路线会自动删除所有关联的步骤（CASCADE）
- 但不会删除关联的Product/Drawing/Quote
- 如果路线已被引用，API会阻止删除（可设置为不启用）

---

## 升级检查清单

- [x] 创建新的模型文件 `models/process_route.py`
- [x] 移除旧的ProcessRoute模型（quote.py）
- [x] 创建API路由文件 `api/routes.py`
- [x] 在 `main.py` 注册新路由
- [x] 在 `database.py` 导入新模型
- [x] 前端添加API方法（api.js）
- [ ] 执行数据库迁移（如需要）
- [ ] 测试API端点
- [ ] 创建前端管理页面（可选）

---

## 文件变更摘要

### 新增文件
- `backend/models/process_route.py` - 新的工艺路线模型
- `backend/api/routes.py` - 工艺路线管理API
- `backend/PROCESS_ROUTE_UPGRADE.md` - 本升级说明文档

### 修改文件
- `backend/models/quote.py` - 移除旧的ProcessRoute模型
- `backend/main.py` - 注册新的API路由
- `backend/config/database.py` - 导入新模型
- `frontend/src/services/api.js` - 添加前端API方法

---

## 后续开发建议

### 1. 前端管理页面
创建专门的工艺路线管理页面：
- 路线列表（支持筛选：模板/实际、关联对象等）
- 路线创建/编辑（拖拽排序工序）
- 模板库管理
- 从模板创建向导
- 成本预览和对比

### 2. 与报价单集成
- 在报价单创建时自动推荐工艺路线模板
- 支持从工艺路线导入工序到报价单
- 工艺路线成本与报价单成本对比

### 3. 工艺路线优化
- 工艺路线复制（创建变体）
- 工艺路线对比（对比不同版本或方案）
- 工艺路线审批流程
- 历史版本管理

### 4. 数据分析
- 工艺路线成本统计
- 常用模板排行
- 工序耗时分析
- 成本优化建议

---

## 技术支持

如有问题，请参考：
- FastAPI文档：https://fastapi.tiangolo.com/
- SQLAlchemy文档：https://docs.sqlalchemy.org/
- 项目README：../README.md
