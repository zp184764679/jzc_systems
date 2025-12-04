# Product（产品）模块实现文档

## 概述

本次更新为报价系统添加了完整的产品管理模块，这是将报价系统升级为工程数据系统的第一步。产品模块作为核心主数据，连接图纸、材料、工艺和报价等各个业务环节。

## 实现内容

### 1. 后端实现

#### 1.1 数据模型

**文件**: `C:\Users\Admin\Desktop\报价\backend\models\product.py`

**Product模型字段**:
- **基础信息**: id, code（产品编码）, name（产品名称）, customer_part_number（客户料号）
- **材质信息**: material, material_spec, density（密度 g/cm³）
- **尺寸信息**: outer_diameter（外径mm）, length（长度mm）, width_or_od, weight_kg
- **结构信息**: subpart_count（子部数量）
- **技术要求**: tolerance（公差等级）, surface_roughness（表面粗糙度）, heat_treatment（热处理）, surface_treatment（表面处理）
- **图纸关联**: customer_drawing_no, drawing_id, version
- **其他**: description, is_active（启用状态）, created_at, updated_at

**关系定义**:
- Product → Drawing: 多对一关系（一个产品可关联一个图纸）
- Product → Quote: 一对多关系（一个产品可有多个报价）

#### 1.2 API路由

**文件**: `C:\Users\Admin\Desktop\报价\backend\api\products.py`

**API端点清单**:

| 方法 | 路径 | 功能 | 说明 |
|------|------|------|------|
| GET | `/api/products` | 获取产品列表 | 支持分页、搜索、状态过滤、材质过滤 |
| POST | `/api/products` | 创建新产品 | 产品编码必须唯一 |
| GET | `/api/products/{product_id}` | 获取产品详情 | 根据ID获取 |
| GET | `/api/products/code/{product_code}` | 根据编码获取产品 | 根据产品编码获取 |
| PUT | `/api/products/{product_id}` | 更新产品信息 | 支持部分更新 |
| DELETE | `/api/products/{product_id}` | 删除产品 | 如已关联报价则禁止删除 |
| PATCH | `/api/products/{product_id}/toggle` | 切换启用/停用状态 | 软删除设计 |
| POST | `/api/products/from-drawing/{drawing_id}` | 从图纸创建产品 | 自动提取图纸信息 |
| GET | `/api/products/stats/summary` | 获取产品统计摘要 | 总数、启用数、材质分布 |

**Pydantic Schemas**:
- `ProductBase`: 基础字段定义
- `ProductCreate`: 创建产品（code和name必填）
- `ProductUpdate`: 更新产品（所有字段可选）
- `ProductResponse`: 响应模型（包含id和时间戳）

#### 1.3 模型更新

**Quote模型更新** (`C:\Users\Admin\Desktop\报价\backend\models\quote.py`):
- 新增字段: `product_id = Column(Integer, ForeignKey("products.id"))`
- 新增关系: `product = relationship("Product", back_populates="quotes")`

**模型初始化** (`C:\Users\Admin\Desktop\报价\backend\models\__init__.py`):
- 添加Product模型导入和导出

**数据库初始化** (`C:\Users\Admin\Desktop\报价\backend\config\database.py`):
- init_db函数中添加product模块导入

#### 1.4 路由注册

**文件**: `C:\Users\Admin\Desktop\报价\backend\main.py`
```python
from api import products
app.include_router(products.router, prefix="/api", tags=["产品管理"])
```

### 2. 前端实现

#### 2.1 产品管理页面

**文件**: `C:\Users\Admin\Desktop\报价\frontend\src\pages\ProductLibrary.jsx`

**功能特性**:
- ✅ 产品列表展示（支持分页）
- ✅ 多条件搜索（产品编码、名称、客户料号）
- ✅ 状态筛选（启用/停用）
- ✅ 新增产品（完整表单验证）
- ✅ 编辑产品（部分字段更新）
- ✅ 查看详情（分类展示：基础信息、材质信息、尺寸信息、技术要求）
- ✅ 删除产品（关联检查保护）
- ✅ 启用/停用切换（软删除）
- ✅ 响应式布局

**UI组件**:
- 表格展示（固定列、排序、分页）
- 详情对话框（Descriptions组件分类展示）
- 编辑对话框（多步骤表单，分组输入）
- 操作按钮（查看、编辑、启用/停用、删除）

#### 2.2 API服务

**文件**: `C:\Users\Admin\Desktop\报价\frontend\src\services\api.js`

**新增API方法**:
```javascript
// 产品管理 API
getProductList(params)          // 获取产品列表
getProduct(productId)           // 获取产品详情
getProductByCode(productCode)   // 根据编码获取
createProduct(data)             // 创建产品
updateProduct(productId, data)  // 更新产品
deleteProduct(productId)        // 删除产品
toggleProductStatus(productId)  // 切换状态
createProductFromDrawing(drawingId)  // 从图纸创建
getProductsSummary()            // 统计摘要
```

#### 2.3 路由配置

**App.jsx** (`C:\Users\Admin\Desktop\报价\frontend\src\App.jsx`):
- 导入ProductLibrary组件
- 添加路由: `/library/products`

**AppSider.jsx** (`C:\Users\Admin\Desktop\报价\frontend\src\components\AppSider.jsx`):
- 添加导航菜单项: "产品库"（数据库管理分组下）
- 图标: `AppstoreOutlined`
- 菜单顺序: 产品库 → 材料库 → 工艺库

## 文件清单

### 创建的文件
1. `C:\Users\Admin\Desktop\报价\backend\models\product.py` - 产品数据模型
2. `C:\Users\Admin\Desktop\报价\backend\api\products.py` - 产品API路由
3. `C:\Users\Admin\Desktop\报价\frontend\src\pages\ProductLibrary.jsx` - 产品管理页面

### 修改的文件
1. `C:\Users\Admin\Desktop\报价\backend\models\quote.py` - 添加product_id字段和关系
2. `C:\Users\Admin\Desktop\报价\backend\models\__init__.py` - 导入Product模型
3. `C:\Users\Admin\Desktop\报价\backend\config\database.py` - init_db添加product导入
4. `C:\Users\Admin\Desktop\报价\backend\main.py` - 注册products路由
5. `C:\Users\Admin\Desktop\报价\frontend\src\services\api.js` - 添加产品API方法
6. `C:\Users\Admin\Desktop\报价\frontend\src\App.jsx` - 添加产品路由
7. `C:\Users\Admin\Desktop\报价\frontend\src\components\AppSider.jsx` - 添加导航菜单

## 数据库迁移

### 新建表
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    code VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    customer_part_number VARCHAR(100),
    material VARCHAR(100),
    material_spec VARCHAR(200),
    density DECIMAL(10, 4),
    outer_diameter FLOAT,
    length FLOAT,
    width_or_od VARCHAR(50),
    weight_kg FLOAT,
    subpart_count INTEGER,
    tolerance VARCHAR(100),
    surface_roughness VARCHAR(50),
    heat_treatment VARCHAR(200),
    surface_treatment VARCHAR(200),
    customer_drawing_no VARCHAR(100),
    drawing_id INTEGER,
    version VARCHAR(20) DEFAULT 'A.0',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (drawing_id) REFERENCES drawings(id)
);
```

### 修改表
```sql
ALTER TABLE quotes ADD COLUMN product_id INTEGER;
ALTER TABLE quotes ADD FOREIGN KEY (product_id) REFERENCES products(id);
```

## 使用说明

### 1. 启动系统

**后端**:
```bash
cd C:\Users\Admin\Desktop\报价\backend
python main.py
```

**前端**:
```bash
cd C:\Users\Admin\Desktop\报价\frontend
npm run dev
```

### 2. 访问产品库

1. 打开浏览器访问前端地址
2. 导航: 数据库管理 → 产品库
3. 或直接访问: http://localhost:5173/library/products

### 3. 主要操作流程

#### 3.1 手动创建产品
1. 点击"新增产品"按钮
2. 填写必填字段：产品编码、产品名称
3. 填写可选字段：材质、尺寸、技术要求等
4. 提交保存

#### 3.2 从图纸创建产品
```javascript
// 通过API调用
const drawing_id = 123;
const product = await createProductFromDrawing(drawing_id);
```

#### 3.3 查询产品
```javascript
// 按编码查询
const product = await getProductByCode('PROD-001');

// 列表查询（支持筛选）
const products = await getProductList({
  skip: 0,
  limit: 10,
  search: '304',
  is_active: true,
  material: '不锈钢'
});
```

#### 3.4 更新产品
```javascript
await updateProduct(productId, {
  material: 'SUS304',
  outer_diameter: 20.5,
  version: 'B.0'
});
```

#### 3.5 启用/停用产品
```javascript
// 切换状态（不删除数据）
await toggleProductStatus(productId);
```

## 技术特性

### 1. 后端特性
- ✅ RESTful API设计
- ✅ Pydantic v2数据验证
- ✅ SQLAlchemy ORM关系映射
- ✅ 软删除设计（is_active字段）
- ✅ 唯一性校验（产品编码）
- ✅ 关联检查（删除前检查报价关联）
- ✅ 自动时间戳（created_at, updated_at）
- ✅ 中文注释和文档
- ✅ 异常处理和错误提示

### 2. 前端特性
- ✅ React Hooks + Ant Design
- ✅ React Query数据管理
- ✅ 响应式表格设计
- ✅ 表单验证
- ✅ 乐观更新
- ✅ 加载状态处理
- ✅ 错误提示
- ✅ 确认对话框
- ✅ 分页和搜索
- ✅ 状态筛选

### 3. 数据安全
- ✅ 产品编码唯一性验证
- ✅ 删除关联检查（防止误删）
- ✅ 软删除设计（可恢复）
- ✅ 外键约束
- ✅ 输入验证

## 下一步建议

### 1. 功能增强
- [ ] **批量导入**: Excel批量导入产品数据
- [ ] **导出功能**: 导出产品清单到Excel
- [ ] **版本管理**: 产品版本历史记录
- [ ] **图片上传**: 产品图片/3D模型上传
- [ ] **工艺路线**: 为产品配置标准工艺路线
- [ ] **BOM结构**: 支持多层级产品结构（父子件关系）
- [ ] **产品分类**: 添加产品分类树形结构
- [ ] **产品变体**: 支持产品系列和变体管理

### 2. 业务集成
- [ ] **报价关联**: 在创建报价时选择产品（而非图纸）
- [ ] **成本计算**: 基于产品主数据自动计算标准成本
- [ ] **价格管理**: 产品价格版本历史
- [ ] **库存管理**: 关联产品库存数据
- [ ] **订单管理**: 产品订单跟踪
- [ ] **质量管理**: 产品质量检验标准

### 3. 数据分析
- [ ] **产品统计**: 按材质、客户、尺寸等维度统计
- [ ] **报价分析**: 产品报价历史分析
- [ ] **成本趋势**: 产品成本变化趋势
- [ ] **热门产品**: Top N产品排行
- [ ] **客户分析**: 客户产品偏好分析

### 4. 系统优化
- [ ] **搜索优化**: 全文搜索、模糊匹配
- [ ] **缓存机制**: Redis缓存常用产品数据
- [ ] **权限控制**: 产品数据的增删改权限
- [ ] **审批流程**: 产品新增/变更审批
- [ ] **操作日志**: 记录产品变更历史
- [ ] **数据校验**: 更严格的数据完整性检查

### 5. 用户体验
- [ ] **快速创建**: 从历史产品复制创建
- [ ] **智能推荐**: 基于图纸自动推荐相似产品
- [ ] **批量操作**: 批量启用/停用、批量更新
- [ ] **高级筛选**: 多条件组合筛选
- [ ] **自定义视图**: 用户自定义列显示
- [ ] **收藏功能**: 收藏常用产品

## API测试示例

### 使用curl测试

```bash
# 1. 获取产品列表
curl http://localhost:8001/api/products

# 2. 创建产品
curl -X POST http://localhost:8001/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "code": "PROD-001",
    "name": "精密轴承座",
    "material": "SUS304",
    "outer_diameter": 50.0,
    "length": 120.0
  }'

# 3. 根据编码获取产品
curl http://localhost:8001/api/products/code/PROD-001

# 4. 更新产品
curl -X PUT http://localhost:8001/api/products/1 \
  -H "Content-Type: application/json" \
  -d '{"version": "B.0"}'

# 5. 切换产品状态
curl -X PATCH http://localhost:8001/api/products/1/toggle

# 6. 从图纸创建产品
curl -X POST http://localhost:8001/api/products/from-drawing/1

# 7. 获取统计摘要
curl http://localhost:8001/api/products/stats/summary

# 8. 删除产品
curl -X DELETE http://localhost:8001/api/products/1
```

### 使用Python测试

```python
import requests

BASE_URL = "http://localhost:8001/api"

# 创建产品
product_data = {
    "code": "PROD-002",
    "name": "法兰盘",
    "material": "45#钢",
    "material_spec": "Φ80×200",
    "density": 7.85,
    "outer_diameter": 80.0,
    "length": 25.0,
    "weight_kg": 0.982,
    "tolerance": "IT7",
    "surface_roughness": "Ra3.2"
}

response = requests.post(f"{BASE_URL}/products", json=product_data)
print(response.json())

# 查询产品
response = requests.get(f"{BASE_URL}/products", params={
    "search": "法兰",
    "is_active": True
})
print(response.json())
```

## 常见问题

### Q1: 产品编码重复怎么办？
A: 系统会自动检查编码唯一性，如果重复会返回400错误。建议使用统一的编码规则，如：`PROD-{序号}`或`{客户代码}-{产品类型}-{序号}`。

### Q2: 删除产品时提示"已关联报价单"？
A: 为保护数据完整性，已关联报价的产品不能删除。建议使用"停用"功能代替删除。

### Q3: 如何批量导入产品数据？
A: 目前暂不支持批量导入，建议后续开发Excel导入功能。临时方案可使用API脚本批量创建。

### Q4: 从图纸创建产品后，修改图纸是否会同步更新产品？
A: 不会自动同步。产品创建后独立于图纸存在，如需更新请手动修改产品信息。

### Q5: 如何管理产品版本？
A: 当前版本支持version字段记录版本号（如A.0, B.0），未来可扩展完整的版本管理功能。

## 总结

本次更新成功为报价系统添加了完整的产品管理模块，实现了：

1. ✅ **完整的CRUD功能**: 创建、读取、更新、删除产品
2. ✅ **灵活的查询能力**: 支持多条件搜索和筛选
3. ✅ **数据关联**: 与图纸、报价模块建立关联关系
4. ✅ **友好的用户界面**: 直观的列表、详情和编辑页面
5. ✅ **数据安全保护**: 唯一性检查、关联检查、软删除
6. ✅ **扩展性设计**: 为未来功能预留扩展空间

产品模块作为工程数据系统的核心，为后续开发BOM管理、工艺路线、成本核算等高级功能奠定了坚实基础。
