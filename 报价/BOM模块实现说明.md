# BOM（物料清单）模块实现说明

## 一、创建的文件列表

### 后端文件 (Backend)

1. **C:\Users\Admin\Desktop\报价\backend\models\bom.py**
   - BOM数据模型
   - 包含 `BOM` 主表和 `BOMItem` 明细表
   - 支持层级式物料清单管理

2. **C:\Users\Admin\Desktop\报价\backend\api\boms.py**
   - BOM管理API路由
   - 完整的CRUD操作
   - 版本复制功能

### 前端文件 (Frontend)

3. **C:\Users\Admin\Desktop\报价\frontend\src\pages\BOMManage.jsx**
   - BOM管理界面
   - 支持增删改查、查看明细、版本复制

---

## 二、修改的文件列表

### 后端修改

1. **C:\Users\Admin\Desktop\报价\backend\models\product.py**
   - 添加了与BOM的关系：`boms = relationship("BOM", back_populates="product")`

2. **C:\Users\Admin\Desktop\报价\backend\models\__init__.py**
   - 导入BOM模型：`from .bom import BOM, BOMItem`
   - 添加到 `__all__` 列表

3. **C:\Users\Admin\Desktop\报价\backend\config\database.py**
   - 在 `init_db()` 函数中添加 `bom` 模块导入

4. **C:\Users\Admin\Desktop\报价\backend\main.py**
   - 导入boms路由：`from api import boms`
   - 注册路由：`app.include_router(boms.router, prefix="/api", tags=["BOM管理"])`

### 前端修改

5. **C:\Users\Admin\Desktop\报价\frontend\src\services\api.js**
   - 添加9个BOM相关API方法

---

## 三、API端点清单

### 基础CRUD操作

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/boms` | 获取BOM列表（支持分页、产品筛选、状态筛选） |
| POST | `/api/boms` | 创建BOM（包含明细） |
| GET | `/api/boms/{bom_id}` | 获取BOM详情 |
| PUT | `/api/boms/{bom_id}` | 更新BOM |
| DELETE | `/api/boms/{bom_id}` | 删除BOM（级联删除明细） |

### 扩展功能

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/boms/{bom_id}/copy` | 复制BOM创建新版本 |
| GET | `/api/products/{product_id}/boms` | 获取产品的所有BOM |
| PATCH | `/api/boms/{bom_id}/toggle` | 切换BOM启用状态 |
| GET | `/api/boms/search` | 搜索BOM（按编码、版本） |

---

## 四、前端功能清单

### 页面功能

#### 1. BOM列表页
- ✅ 表格展示所有BOM
- ✅ 分页功能（默认20条/页）
- ✅ 按产品筛选
- ✅ 按启用状态筛选
- ✅ 显示物料类型（成品/半成品/原材料/标准件）
- ✅ 显示启用状态（带图标）
- ✅ 显示明细数量

#### 2. BOM创建/编辑
- ✅ 模态框表单
- ✅ 基础信息录入
  - BOM编码（必填）
  - 产品选择（必填）
  - 版本号（必填）
  - 物料类型（下拉选择）
  - 单位
  - 生效期间（日期范围）
  - 制表人、审核人
  - 备注
  - 启用状态（开关）

#### 3. BOM明细管理
- ✅ 表格式明细编辑
- ✅ 动态添加/删除明细行
- ✅ 支持字段：
  - 层级（如：1, 1.1, 1.1.1）
  - 零件编号
  - 零件名称
  - 规格型号
  - 单位
  - 用量（数值输入）
  - 损耗率（百分比）
  - 替代料
  - 供应商
  - 备注

#### 4. 操作功能
- ✅ 查看明细（只读模态框）
- ✅ 编辑BOM
- ✅ 复制BOM（创建新版本）
- ✅ 删除BOM（带确认）
- ✅ 导出Excel（按钮已预留）

---

## 五、数据模型说明

### BOM主表 (boms)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| bom_code | String(64) | BOM编码（唯一） |
| product_id | Integer | 产品ID（外键） |
| version | String(20) | 版本号（默认A.01） |
| material_type | String(20) | 物料类型 |
| unit | String(20) | 单位（默认"套"） |
| effective_from | Date | 生效日期 |
| effective_to | Date | 失效日期 |
| maker | String(64) | 制表人 |
| approver | String(64) | 审核人 |
| remark | Text | 备注 |
| is_active | Boolean | 是否启用 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### BOM明细表 (bom_items)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| bom_id | Integer | BOM ID（外键） |
| level | String(20) | 层级序号 |
| sequence | Integer | 排序序号 |
| part_no | String(100) | 零件编号 |
| part_name | String(200) | 零件名称 |
| spec | String(200) | 规格型号 |
| unit | String(20) | 单位（默认PCS） |
| qty | Decimal(12,4) | 用量 |
| loss_rate | Decimal(5,4) | 损耗率(%) |
| alt_part | String(100) | 替代料 |
| supplier | String(200) | 供应商 |
| remark | Text | 备注 |
| created_at | DateTime | 创建时间 |

---

## 六、关系说明

```
Product (产品)
  ├── 1:N → BOM (物料清单)
           ├── 1:N → BOMItem (明细行)
```

- 一个产品可以有多个BOM（不同版本）
- 一个BOM包含多个BOMItem（明细行）
- 删除BOM时级联删除所有明细行

---

## 七、使用说明

### 1. 启动系统后自动创建表

系统启动时会自动执行 `init_db()`，创建 `boms` 和 `bom_items` 表。

### 2. 创建BOM

1. 进入BOM管理页面
2. 点击"新增BOM"
3. 填写基础信息
4. 点击"添加明细行"添加物料
5. 填写明细信息
6. 点击"确定"保存

### 3. 复制BOM版本

1. 在列表中找到要复制的BOM
2. 点击"复制"按钮
3. 输入新版本号（如：B.01）
4. 系统自动复制所有明细

### 4. 查看产品的所有BOM

使用API：`GET /api/products/{product_id}/boms`

---

## 八、技术特点

### 后端特点

1. **SQLAlchemy ORM**
   - 使用声明式基类
   - 关系映射清晰
   - 级联删除支持

2. **Pydantic验证**
   - 请求数据自动验证
   - 响应数据自动序列化
   - 类型安全

3. **RESTful设计**
   - 标准HTTP方法
   - 资源化路由
   - 清晰的响应格式

### 前端特点

1. **Ant Design组件**
   - Table表格展示
   - Modal模态框
   - Form表单（含嵌套表单）
   - DatePicker日期范围
   - Tag标签

2. **交互体验**
   - 行内编辑明细
   - 动态添加/删除行
   - 二次确认删除
   - 实时筛选

3. **数据管理**
   - useState管理状态
   - useEffect加载数据
   - Form.List处理动态列表

---

## 九、扩展建议

### 已预留功能

1. **Excel导入导出**
   - 按钮已预留在界面
   - 可参考报价模块的Excel导出实现

2. **拖拽排序**
   - 可使用 react-beautiful-dnd 库
   - 更新 sequence 字段

3. **层级树形展示**
   - 可使用 Ant Design TreeTable
   - 基于 level 字段构建树形结构

### 功能增强方向

1. 成本计算（基于明细用量）
2. BOM对比（版本差异）
3. 替代料管理
4. 供应商管理集成
5. 审批流程
6. 变更历史追踪

---

## 十、注意事项

1. **不要运行服务** - 按要求未执行任何启动命令
2. **导入路径正确** - 所有相对导入已验证
3. **级联删除** - 删除BOM会自动删除所有明细行
4. **唯一约束** - BOM编码必须唯一
5. **外键约束** - product_id 必须存在于 products 表

---

## 十一、文件路径总结

### 创建的文件（3个）
```
C:\Users\Admin\Desktop\报价\backend\models\bom.py
C:\Users\Admin\Desktop\报价\backend\api\boms.py
C:\Users\Admin\Desktop\报价\frontend\src\pages\BOMManage.jsx
```

### 修改的文件（5个）
```
C:\Users\Admin\Desktop\报价\backend\models\product.py
C:\Users\Admin\Desktop\报价\backend\models\__init__.py
C:\Users\Admin\Desktop\报价\backend\config\database.py
C:\Users\Admin\Desktop\报价\backend\main.py
C:\Users\Admin\Desktop\报价\frontend\src\services\api.js
```

---

完成日期：2025年（根据任务要求）
模块状态：✅ 完整实现，未启动服务
