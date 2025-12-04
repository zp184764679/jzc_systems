# EAM系统文件清单

## 总览

- **系统名称**: EAM设备管理系统
- **创建日期**: 2025-11-15
- **总文件数**: 20个
- **后端文件**: 8个
- **前端文件**: 8个
- **文档文件**: 6个

## 目录结构

```
C:\Users\Admin\Desktop\EAM\
├── backend/                          # 后端服务
│   ├── app/                          # Flask应用
│   │   ├── models/                   # 数据模型
│   │   │   ├── __init__.py          # 模型包初始化
│   │   │   └── machine.py           # 设备模型（从PM复制）
│   │   ├── routes/                   # API路由
│   │   │   ├── __init__.py          # 路由包初始化
│   │   │   └── machines.py          # 设备API路由（从PM复制）
│   │   └── __init__.py              # Flask工厂函数
│   ├── .env                          # 环境变量配置
│   ├── .gitignore                    # Git忽略文件
│   ├── main.py                       # 应用入口
│   └── requirements.txt              # Python依赖
│
├── frontend/                         # 前端应用
│   ├── src/                          # 源代码
│   │   ├── pages/                    # 页面组件
│   │   │   └── machines/
│   │   │       └── MachineList.jsx  # 设备列表页面（Ant Design）
│   │   ├── services/                 # 服务层
│   │   │   └── api.js               # API封装
│   │   ├── App.css                   # 全局样式
│   │   ├── App.jsx                   # 主应用组件
│   │   └── main.jsx                  # 应用入口
│   ├── .gitignore                    # Git忽略文件
│   ├── index.html                    # HTML模板
│   ├── package.json                  # NPM依赖
│   └── vite.config.js               # Vite配置
│
├── API_TEST.md                       # API测试文档
├── COMPARISON.md                     # 与PM系统对比文档
├── FILES.md                          # 本文件（文件清单）
├── README.md                         # 项目说明文档
└── STARTUP.md                        # 启动指南
```

## 文件详细说明

### 后端文件 (Backend)

#### 1. `backend/main.py`
- **作用**: Flask应用入口文件
- **端口**: 8005
- **来源**: 参考SCM系统创建

#### 2. `backend/.env`
- **作用**: 环境变量配置
- **配置**: 数据库连接、端口、密钥等
- **数据库**: localhost/cncplan

#### 3. `backend/requirements.txt`
- **作用**: Python依赖包清单
- **主要依赖**:
  - Flask 3.1.0
  - SQLAlchemy 2.0.36
  - Flask-CORS 5.0.0
  - PyMySQL 1.1.1

#### 4. `backend/app/__init__.py`
- **作用**: Flask工厂函数
- **功能**:
  - 应用初始化
  - 数据库配置
  - CORS配置
  - 蓝图注册
- **来源**: 参考SCM系统，针对EAM定制

#### 5. `backend/app/models/__init__.py`
- **作用**: 模型包初始化
- **导出**: Machine模型

#### 6. `backend/app/models/machine.py`
- **作用**: 设备数据模型
- **表名**: machines
- **来源**: 从PM系统完整复制
- **字段**: 19个（含时间戳）

#### 7. `backend/app/routes/__init__.py`
- **作用**: 路由包初始化
- **导出**: machines路由

#### 8. `backend/app/routes/machines.py`
- **作用**: 设备API路由
- **来源**: 从PM系统完整复制
- **API**:
  - GET /api/machines - 列表
  - POST /api/machines - 创建
  - GET /api/machines/{id} - 详情
  - PUT /api/machines/{id} - 更新
  - DELETE /api/machines/{id} - 删除

#### 9. `backend/.gitignore`
- **作用**: Git版本控制忽略文件
- **忽略**: Python缓存、虚拟环境、数据库文件等

### 前端文件 (Frontend)

#### 1. `frontend/package.json`
- **作用**: NPM项目配置和依赖
- **主要依赖**:
  - React 19.2.0
  - Vite 7.2.2
  - Ant Design 5.28.1
  - React Router 7.9.6

#### 2. `frontend/vite.config.js`
- **作用**: Vite构建配置
- **端口**: 7200
- **代理**: /api -> localhost:8005

#### 3. `frontend/index.html`
- **作用**: HTML入口文件
- **标题**: EAM设备管理系统

#### 4. `frontend/src/main.jsx`
- **作用**: React应用入口
- **挂载点**: #root

#### 5. `frontend/src/App.jsx`
- **作用**: 主应用组件
- **功能**:
  - 路由配置
  - 导航菜单
  - 布局组件
  - 中文化配置
- **来源**: 参考SCM系统，完全中文化

#### 6. `frontend/src/App.css`
- **作用**: 全局样式
- **内容**: 基础重置和字体设置

#### 7. `frontend/src/services/api.js`
- **作用**: API封装层
- **功能**:
  - Axios实例配置
  - 请求/响应拦截器
  - machineAPI方法封装

#### 8. `frontend/src/pages/machines/MachineList.jsx`
- **作用**: 设备列表页面组件
- **技术**: React + Ant Design
- **功能**:
  - 设备列表展示
  - 搜索和筛选
  - 分页和排序
  - 新增/编辑/删除
  - Modal表单
- **来源**: 参考PM的Machines.jsx，重构为Ant Design

#### 9. `frontend/.gitignore`
- **作用**: Git版本控制忽略文件
- **忽略**: node_modules、dist、环境变量等

### 文档文件 (Documentation)

#### 1. `README.md`
- **作用**: 项目说明文档
- **内容**:
  - 系统架构
  - 技术栈
  - 功能模块
  - 数据库表结构
  - API接口
  - 安装说明

#### 2. `STARTUP.md`
- **作用**: 快速启动指南
- **内容**:
  - 后端启动步骤
  - 前端启动步骤
  - 访问地址
  - 常见问题

#### 3. `API_TEST.md`
- **作用**: API测试文档
- **内容**:
  - 接口测试示例
  - curl命令
  - Postman配置
  - 测试场景
  - 错误响应

#### 4. `COMPARISON.md`
- **作用**: 与PM系统对比文档
- **内容**:
  - 系统定位对比
  - 功能对比
  - 技术栈对比
  - 数据表说明
  - 代码来源
  - 使用场景

#### 5. `FILES.md`
- **作用**: 本文件，完整文件清单
- **内容**: 所有文件的详细说明

## 代码统计

### 后端代码
- Python文件: 4个
- 总行数: ~600行
- 主要功能: Flask应用、数据模型、API路由

### 前端代码
- JavaScript/JSX文件: 4个
- 总行数: ~400行
- 主要功能: React组件、API封装、路由配置

### 配置文件
- 后端配置: 3个（.env, requirements.txt, .gitignore）
- 前端配置: 4个（package.json, vite.config.js, index.html, .gitignore）

### 文档文件
- Markdown文件: 5个
- 总字数: ~8000字
- 涵盖: 说明、启动、测试、对比、清单

## 技术特点

### 后端特点
✅ Flask工厂模式
✅ RESTful API设计
✅ SQLAlchemy ORM
✅ 完整CRUD操作
✅ 数据验证
✅ 错误处理
✅ CORS支持

### 前端特点
✅ React 19 最新版
✅ Ant Design 5 组件库
✅ React Router 路由
✅ React Query 数据管理
✅ 响应式设计
✅ 完全中文化
✅ 模态框编辑
✅ 搜索分页排序

## 与PM系统的关系

### 复用的代码
1. `backend/app/models/machine.py` - 100%复制自PM
2. `backend/app/routes/machines.py` - 100%复制自PM

### 参考的代码
1. `frontend/src/pages/machines/MachineList.jsx` - 参考PM的Machines.jsx
2. `backend/app/__init__.py` - 参考SCM系统
3. `frontend/src/App.jsx` - 参考SCM系统

### 共享的资源
- 数据库: cncplan
- 数据表: machines
- 数据完全同步

## 安装要求

### 后端要求
- Python 3.8+
- MySQL 5.7+ / 8.0+
- pip (Python包管理器)

### 前端要求
- Node.js 16+
- npm 或 yarn

### 系统要求
- 端口7200可用（前端）
- 端口8005可用（后端）
- MySQL服务运行中
- 数据库cncplan已创建

## 下一步操作

1. ✅ 所有文件已创建完成
2. ⏭️ 安装后端依赖: `cd backend && pip install -r requirements.txt`
3. ⏭️ 安装前端依赖: `cd frontend && npm install`
4. ⏭️ 启动后端服务: `cd backend && python main.py`
5. ⏭️ 启动前端服务: `cd frontend && npm run dev`
6. ⏭️ 访问系统: http://localhost:7200

## 维护说明

### 定期更新
- 定期更新依赖包版本
- 关注安全漏洞修复
- 同步PM系统的设备模型变更

### 扩展开发
- 维护管理模块
- 备件管理模块
- 设备监控模块
- 资产分析模块

### 问题反馈
如遇问题，请检查：
1. 数据库连接是否正常
2. 端口是否被占用
3. 依赖是否完整安装
4. 配置文件是否正确

---

**创建完成时间**: 2025-11-15
**系统版本**: v1.0.0
**状态**: ✅ 就绪，可以启动使用
