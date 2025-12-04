# SHM 出货管理系统 (Shipment Management System)

一个完整的出货/发货管理系统，支持出货单管理、客户地址管理、交货要求管理，并与SCM库存系统对接。

## 系统架构

- **后端**: Flask 3.0 + SQLAlchemy 2.x + MySQL
- **前端**: React 19 + Ant Design 5 + Vite
- **端口配置**:
  - 前端: 7500
  - 后端: 8006

## 功能特性

### 1. 出货单管理
- 创建、编辑、删除、查询出货单
- 多产品出货明细
- 状态流转：待出货 → 已发货 → 已签收
- 支持取消操作（待出货状态）

### 2. 客户收货地址
- 管理客户的多个收货地址
- 设置默认地址
- 自动填充地址信息

### 3. 交货要求管理
- 包装类型：标准/防潮/防震/真空
- 包装材料：纸箱/木箱/泡沫/托盘
- 标签要求、送货时间窗口
- 质检报告要求
- 特殊说明

### 4. SCM系统对接
- 发货时自动扣减SCM系统库存
- 调用 `POST /api/inventory/out` 接口

## 快速开始

### 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py
```

后端将在 http://localhost:8006 运行

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:7500 运行

## 数据库配置

修改 `backend/.env` 文件：

```
DB_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=cncplan
PORT=8006
```

## API 端点

### 出货单 API
- `GET /api/shipments` - 获取出货单列表
- `POST /api/shipments` - 创建出货单
- `GET /api/shipments/{id}` - 获取出货单详情
- `PUT /api/shipments/{id}` - 更新出货单
- `DELETE /api/shipments/{id}` - 删除出货单
- `POST /api/shipments/{id}/ship` - 发货（扣减库存）
- `PATCH /api/shipments/{id}/status` - 更新状态
- `GET /api/shipments/stats` - 获取统计数据

### 客户地址 API
- `GET /api/addresses` - 获取地址列表
- `POST /api/addresses` - 创建地址
- `GET /api/addresses/{id}` - 获取地址详情
- `GET /api/addresses/customer/{customer_id}` - 获取客户地址
- `PUT /api/addresses/{id}` - 更新地址
- `DELETE /api/addresses/{id}` - 删除地址

### 交货要求 API
- `GET /api/requirements` - 获取要求列表
- `POST /api/requirements` - 创建要求
- `GET /api/requirements/{id}` - 获取要求详情
- `GET /api/requirements/customer/{customer_id}` - 获取客户要求
- `PUT /api/requirements/{id}` - 更新要求
- `DELETE /api/requirements/{id}` - 删除要求

## 数据模型

### Shipment (出货单主表)
- shipment_no: 出货单号（唯一）
- order_no: 关联订单号
- customer_id/customer_name: 客户信息
- delivery_date: 出货日期
- expected_arrival: 预计到达日期
- shipping_method: 运输方式
- carrier: 承运商
- tracking_no: 物流单号
- status: 状态
- warehouse_id/contact/phone: 仓库信息
- receiver_contact/phone/address: 收货信息

### ShipmentItem (出货明细)
- product_code: 产品编码
- product_name: 产品名称
- qty: 数量
- unit: 单位
- bin_code: 仓位
- batch_no: 批次号

### CustomerAddress (客户收货地址)
- contact_person/phone: 联系信息
- province/city/district/address: 地址信息
- postal_code: 邮编
- is_default: 是否默认

### DeliveryRequirement (交货要求)
- packaging_type: 包装类型
- packaging_material: 包装材料
- labeling_requirement: 标签要求
- delivery_time_window: 送货时间窗口
- quality_cert_required: 是否需要质检报告
- special_instructions: 特殊说明

## SCM对接说明

当出货单状态从"待出货"变为"已发货"时，系统会自动调用SCM系统的库存扣减API：

```python
POST http://localhost:8004/api/inventory/out
{
    "product_text": "产品编码",
    "qty_delta": 数量,
    "order_no": "出货单号",
    "remark": "出货单 SHMxxxxxxxx 发货扣减"
}
```

如果SCM系统不可用或库存不足，发货操作将失败并返回错误信息。

## 许可证

MIT License
