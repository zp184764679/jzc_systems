# EAM设备管理系统 - 启动指南

## 快速启动

### 1. 后端启动

```bash
# 进入后端目录
cd C:\Users\Admin\Desktop\EAM\backend

# 安装依赖
pip install -r requirements.txt

# 启动后端服务（端口 8005）
python main.py
```

后端将运行在: http://localhost:8005

### 2. 前端启动

```bash
# 打开新终端，进入前端目录
cd C:\Users\Admin\Desktop\EAM\frontend

# 安装依赖
npm install

# 启动前端服务（端口 7200）
npm run dev
```

前端将运行在: http://localhost:7200

## 访问系统

浏览器打开: http://localhost:7200

## 菜单导航

1. **首页** - 系统欢迎页
2. **设备台账** - 设备信息管理（CRUD操作）
3. **设备产能配置** - 产能管理（开发中）
4. **维护记录** - 维护历史（开发中）

## 测试API

### 健康检查
```bash
curl http://localhost:8005/api/health
```

### 获取设备列表
```bash
curl http://localhost:8005/api/machines
```

## 数据库配置

确保以下配置正确（`backend/.env`）:

```
DB_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=cncplan
PORT=8005
```

## 端口说明

- **前端**: 7200
- **后端**: 8005
- **数据库**: 3306 (MySQL)

## 常见问题

### 1. 端口被占用
如果端口被占用，可以修改：
- 前端端口: `frontend/vite.config.js`
- 后端端口: `backend/.env` (PORT变量)

### 2. 数据库连接失败
- 确保MySQL服务已启动
- 确保数据库 `cncplan` 已创建
- 检查 `.env` 文件中的数据库配置

### 3. CORS错误
后端已配置允许 `http://localhost:7200` 访问，如果修改了前端端口，需要同步修改 `backend/app/__init__.py` 中的CORS配置。

## 开发工具

### 查看数据库
```bash
mysql -u root -p
use cncplan;
select * from machines;
```

### 查看日志
后端运行时会在控制台显示详细日志，包括：
- HTTP请求日志
- 数据库查询日志
- 错误信息

## 系统特性

### 后端特性
- ✅ RESTful API设计
- ✅ Flask工厂模式
- ✅ SQLAlchemy ORM
- ✅ 自动时间戳
- ✅ 完整的CRUD操作
- ✅ 数据验证
- ✅ 错误处理
- ✅ CORS支持

### 前端特性
- ✅ React 19 + Vite 7
- ✅ Ant Design 5 组件库
- ✅ React Router 路由管理
- ✅ React Query 数据管理
- ✅ 响应式设计
- ✅ 中文界面
- ✅ 搜索、分页、排序
- ✅ 表单验证
- ✅ 模态框编辑

## 下一步

1. 启动后端和前端服务
2. 访问 http://localhost:7200
3. 测试设备的增删改查功能
4. 根据需求扩展其他功能模块
