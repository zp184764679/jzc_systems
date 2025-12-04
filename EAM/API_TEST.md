# EAM API 测试文档

## 基础信息

- **后端地址**: http://localhost:8005
- **API前缀**: /api

## API接口测试

### 1. 健康检查

```bash
# 测试后端是否正常运行
curl http://localhost:8005/api/health
```

预期响应:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 2. 获取设备列表

```bash
# 获取所有设备（分页）
curl http://localhost:8005/api/machines?page=1&page_size=10

# 搜索设备
curl "http://localhost:8005/api/machines?q=加工中心"

# 按部门筛选
curl "http://localhost:8005/api/machines?dept_name=数控车间"
```

预期响应:
```json
{
  "page": 1,
  "page_size": 10,
  "total": 5,
  "items": [
    {
      "id": 1,
      "machine_code": "MC-001",
      "code": "MC-001",
      "name": "立式加工中心",
      "brand": "Mazak",
      "model": "VCN-430A",
      "dept_name": "数控车间",
      "factory_location": "深圳",
      "status": "在用",
      "capacity": 100,
      "created_at": "2025-01-15T10:00:00",
      "updated_at": "2025-01-15T10:00:00"
    }
  ]
}
```

### 3. 获取单个设备详情

```bash
# 通过ID获取
curl http://localhost:8005/api/machines/1

# 通过设备编码获取
curl "http://localhost:8005/api/machines?code=MC-001"
```

### 4. 创建设备

```bash
curl -X POST http://localhost:8005/api/machines \
  -H "Content-Type: application/json" \
  -d '{
    "code": "MC-002",
    "name": "卧式加工中心",
    "brand": "Haas",
    "model": "UMC-750",
    "dept_name": "数控车间",
    "factory_location": "深圳",
    "status": "在用",
    "capacity": 80,
    "place": "一号厂房A区",
    "manufacturer": "Haas Automation"
  }'
```

预期响应:
```json
{
  "id": 2,
  "machine_code": "MC-002",
  "name": "卧式加工中心",
  "brand": "Haas",
  "model": "UMC-750",
  "status": "在用",
  ...
}
```

### 5. 更新设备

```bash
curl -X PUT http://localhost:8005/api/machines/2 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "卧式加工中心(已升级)",
    "status": "维修",
    "capacity": 90
  }'
```

### 6. 删除设备

```bash
curl -X DELETE http://localhost:8005/api/machines/2
```

预期响应:
```json
{
  "ok": true,
  "id": 2
}
```

## 完整的测试场景

### 场景1: 新增设备

```bash
# 1. 新增一台设备
curl -X POST http://localhost:8005/api/machines \
  -H "Content-Type: application/json" \
  -d '{
    "code": "MC-003",
    "name": "数控车床",
    "brand": "Fanuc",
    "model": "T-2000",
    "dept_name": "车削车间",
    "factory_location": "东莞",
    "status": "在用",
    "serial_no": "SN12345678",
    "manufacturer": "Fanuc Corporation",
    "place": "二号厂房B区",
    "capacity": 120,
    "mfg_date": "2024-06-15",
    "purchase_date": "2024-08-01"
  }'

# 2. 验证是否创建成功
curl "http://localhost:8005/api/machines?code=MC-003"
```

### 场景2: 查询和更新

```bash
# 1. 搜索车削车间的设备
curl "http://localhost:8005/api/machines?dept_name=车削车间"

# 2. 更新设备状态为维修
curl -X PUT http://localhost:8005/api/machines/3 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "维修"
  }'

# 3. 验证更新结果
curl http://localhost:8005/api/machines/3
```

### 场景3: 批量测试

```bash
# 创建多台设备
for i in {4..8}; do
  curl -X POST http://localhost:8005/api/machines \
    -H "Content-Type: application/json" \
    -d "{
      \"code\": \"MC-00$i\",
      \"name\": \"设备$i\",
      \"brand\": \"Test Brand\",
      \"model\": \"Model-$i\",
      \"dept_name\": \"测试部门\",
      \"factory_location\": \"深圳\",
      \"status\": \"在用\"
    }"
  sleep 1
done

# 查询所有测试设备
curl "http://localhost:8005/api/machines?dept_name=测试部门"

# 清理测试数据
for i in {4..8}; do
  curl -X DELETE http://localhost:8005/api/machines/$i
done
```

## 使用Postman测试

### 导入Postman Collection

创建以下请求集合:

1. **GET** - 设备列表
   - URL: `http://localhost:8005/api/machines`
   - Params: `page=1&page_size=10`

2. **GET** - 设备详情
   - URL: `http://localhost:8005/api/machines/1`

3. **POST** - 创建设备
   - URL: `http://localhost:8005/api/machines`
   - Body (JSON):
   ```json
   {
     "code": "MC-TEST",
     "name": "测试设备",
     "brand": "测试品牌",
     "dept_name": "测试部门",
     "status": "在用"
   }
   ```

4. **PUT** - 更新设备
   - URL: `http://localhost:8005/api/machines/1`
   - Body (JSON):
   ```json
   {
     "status": "维修"
   }
   ```

5. **DELETE** - 删除设备
   - URL: `http://localhost:8005/api/machines/1`

## 错误响应

### 400 Bad Request
```json
{
  "error": "name is required"
}
```

### 404 Not Found
```json
{
  "error": "not found"
}
```

### 409 Conflict
```json
{
  "error": "machine_code duplicated"
}
```

### 500 Internal Server Error
```json
{
  "error": "db error",
  "detail": "详细错误信息"
}
```

## 数据字段说明

### 必填字段
- `name` - 设备名称

### 可选字段
- `code` / `machine_code` - 设备编码（不填则自动生成）
- `brand` - 品牌
- `model` - 型号
- `dept_name` - 所属部门
- `factory_location` - 工厂位置（深圳/东莞）
- `serial_no` - 出厂编号
- `manufacturer` - 生产厂商
- `place` - 放置场所
- `capacity` - 产能（件/天）
- `status` - 状态（在用/停用/维修/报废）
- `mfg_date` - 出厂日期（YYYY-MM-DD）
- `purchase_date` - 购入日期（YYYY-MM-DD）

## 查询参数说明

- `page` - 页码（默认1）
- `page_size` / `ps` - 每页条数（默认10）
- `q` / `keyword` - 全局搜索关键词
- `code` - 按设备编码搜索
- `name` - 按设备名称搜索
- `dept_name` - 按部门筛选
- `sort_by` - 排序字段（created_at/name/machine_code等）
- `order` - 排序方向（asc/desc，默认desc）
