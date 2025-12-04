# SHM 出货管理系统 - 部署指南

**系统名称**: SHM (Shipping Management System) - 出货管理系统
**版本**: 2.0
**部署日期**: 2025-12-01
**技术栈**: React 19 + Antd 6 + Flask + SQLite/MySQL

---

## 🎉 重要更新

本次部署包含以下重要升级：

### ⬆️ 技术栈升级

| 组件 | 旧版本 | 新版本 | 说明 |
|-----|--------|--------|------|
| **React** | 18.3.1 | **19.0.0** | ⬆️ 最新稳定版 |
| **Ant Design** | 5.22.0 | **6.0.0** | ⬆️ 原生支持React 19 |
| **@ant-design/icons** | 5.5.0 | **6.0.0** | ⬆️ 配套升级 |

### ✅ 已修复的问题

1. **401未授权错误** - 添加JWT token自动注入
2. **React 19兼容性警告** - 升级到Antd 6原生支持
3. **Spin组件警告** - 使用fullscreen模式
4. **性能优化** - Bundle减少10-20%

详见: `UPGRADE_TO_V6.md`

---

## 📦 部署包内容

### 核心文件（必需）

```
SHM/
├── frontend/
│   └── dist/                      # 前端构建产物 ✅
│       ├── index.html
│       └── assets/
│           ├── index-01aF4e9B.css  (0.59 kB)
│           └── index-B_Vw3C3n.js   (1.35 MB)
│
└── backend/                       # 后端代码 ✅
    ├── app.py                     # Flask应用入口
    ├── config.py                  # 配置文件
    ├── extensions.py              # 扩展初始化
    ├── requirements.txt           # Python依赖
    ├── .env                       # 环境变量
    ├── models/                    # 数据库模型
    ├── routes/                    # API路由
    │   ├── shipments.py           # 出货单API
    │   ├── addresses.py           # 客户地址API
    │   ├── requirements.py        # 交货要求API
    │   ├── integration.py         # 系统集成API
    │   ├── base_data.py           # 基础数据API
    │   └── auth.py                # 认证API (SSO)
    └── services/                  # 业务逻辑
```

### 辅助文件（推荐）

```
├── deploy.sh                      # Linux/Mac部署脚本
├── deploy.bat                     # Windows部署脚本
├── DEPLOYMENT_GUIDE.md            # 本文档
├── UPGRADE_TO_V6.md               # 升级说明
└── README_DEPLOYMENT.md           # 快速部署指南
```

---

## ⚠️ 部署前准备

### 创建MySQL数据库（必需）

**重要**: SHM系统使用MySQL作为生产数据库，部署前必须先创建数据库。

```sql
-- 1. 登录MySQL
mysql -u root -p

-- 2. 创建数据库
CREATE DATABASE shm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 3. 创建应用用户
CREATE USER 'app'@'localhost' IDENTIFIED BY 'app';
GRANT ALL PRIVILEGES ON shm.* TO 'app'@'localhost';
FLUSH PRIVILEGES;

-- 4. 验证
SHOW DATABASES;
EXIT;
```

**生产环境安全提示**:
- ⚠️ 请修改默认密码 `app` 为强密码
- ⚠️ 修改后同步更新 `backend/.env` 中的 `MYSQL_PASSWORD`

**详细配置指南**: 查看 `MYSQL_SETUP.md`

---

## 🚀 快速部署

### 方法一: 一键部署（推荐）

**Windows**:
```cmd
deploy.bat
```

**Linux/Mac**:
```bash
chmod +x deploy.sh
./deploy.sh
```

### 方法二: 手动部署

#### 1. 安装依赖

**Node.js工具**:
```bash
npm install -g serve pm2
```

**Python依赖**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

pip install -r requirements.txt
deactivate
```

#### 2. 启动服务

**前端** (端口 7500):
```bash
cd frontend
pm2 start serve --name shm-frontend -- -s dist -l 7500
```

**后端** (端口 8006):

Linux/Mac:
```bash
cd backend
pm2 start app.py --name shm-backend --interpreter $(pwd)/venv/bin/python
```

Windows:
```cmd
cd backend
pm2 start app.py --name shm-backend --interpreter venv\Scripts\python.exe
```

#### 3. 保存配置

```bash
pm2 save
pm2 startup  # 配置开机自启（可选）
```

---

## 🔧 系统配置

### 1. 后端配置 (.env)

创建或编辑 `backend/.env`:

```bash
# 数据库配置 - MySQL (生产环境)
DB_HOST=localhost
MYSQL_USER=app
MYSQL_PASSWORD=app
MYSQL_DATABASE=shm

# 服务端口
PORT=8006

# JWT配置 (用于SSO认证)
SECRET_KEY=your-secret-key-please-change-in-production
ALGORITHM=HS256

# Portal SSO服务地址
PORTAL_URL=http://localhost:3002

# Flask配置
FLASK_ENV=production
DEBUG=False

# 跨系统API配置
SCM_API_BASE_URL=http://localhost:8005
PDM_API_BASE_URL=http://localhost:8001
CRM_API_BASE_URL=http://localhost:8002
HR_API_BASE_URL=http://localhost:8003
```

**重要配置说明**:
- ✅ 使用MySQL数据库（已在 config.py 中配置）
- ⚠️ `MYSQL_USER` 和 `MYSQL_PASSWORD` 必须与MySQL数据库创建时一致
- ⚠️ 生产环境必须修改 `SECRET_KEY` 为强随机字符串
- ⚠️ 生产环境建议修改 `MYSQL_PASSWORD` 为强密码

### 2. 前端配置

前端已使用代理配置，无需额外配置。API请求会自动转发到后端。

如需修改API地址，编辑 `frontend/vite.config.js`:

```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8006',  // 后端地址
        changeOrigin: true
      }
    }
  }
})
```

### 3. 数据库配置

#### MySQL（生产环境）

SHM系统使用MySQL作为生产数据库。部署前必须先创建数据库（参见上方"部署前准备"章节）。

**自动初始化**: 部署脚本会自动创建数据库表结构。

**手动初始化**（如需要）:
```bash
cd backend
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 方法1: 使用Flask-Migrate
flask db upgrade

# 方法2: 使用Python脚本
python -c "from app import app, db; \
with app.app_context(): \
    db.create_all(); \
    print('✅ 数据库表创建成功')"
```

**验证数据库连接**:
```bash
python -c "from app import app, db; \
with app.app_context(): \
    db.engine.connect(); \
    print('✅ MySQL连接成功')"
```

**详细MySQL配置**: 查看 `MYSQL_SETUP.md`

---

## 🔐 SSO集成

SHM系统已集成Portal的SSO认证系统。

### 工作流程

1. **用户从Portal登录** → 获取JWT token
2. **Portal跳转到SHM** → URL携带token参数
   `http://localhost:7500?token=xxx`
3. **SHM验证token** → 调用Portal后端验证
4. **登录成功** → 存储用户信息，访问系统

### 配置要点

**后端 (app.py)**:
```python
# CORS配置 - 允许Portal前端访问
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:7500", "http://localhost:3001"]
    }
})
```

**前端 (ssoAuth.js)**:
```javascript
// Portal SSO后端地址
const API_BASE_URL = 'http://localhost:8006'

// 验证token端点
POST /api/auth/sso-login
```

---

## ✅ 验证部署

### 1. 检查服务状态
```bash
pm2 list
```

应显示：
- ✅ shm-frontend (online) - 端口 7500
- ✅ shm-backend (online) - 端口 8006

### 2. 测试前端
浏览器访问: **http://localhost:7500**

应看到登录页面或从Portal跳转过来

### 3. 测试后端API
```bash
# 健康检查
curl http://localhost:8006/api/health

# 应返回
{"status":"ok","service":"SHM - 出货管理系统"}
```

### 4. 测试SSO认证

1. 访问Portal: http://localhost:3001
2. 登录成功后点击"出货管理系统"
3. 应自动跳转到SHM并完成登录

### 5. 功能测试

- [ ] Dashboard统计数据显示
- [ ] 出货单列表加载
- [ ] 创建出货单
- [ ] 编辑出货单
- [ ] 更新出货状态
- [ ] 客户地址管理
- [ ] 交货要求管理
- [ ] 基础数据管理

---

## 📊 端口配置

| 服务 | 端口 | 说明 |
|-----|------|------|
| SHM前端 | 7500 | 前端React应用 |
| SHM后端 | 8006 | Flask API服务 |
| Portal前端 | 3001 | 门户系统（SSO） |
| Portal后端 | 3002 | Portal API（SSO认证） |

**注意**: 确保这些端口没有被其他服务占用。

---

## 🔍 故障排查

### 问题1: 401未授权错误

**现象**: API请求返回401
**原因**: Token未正确传递
**解决**:
1. 检查 `frontend/src/api.js` 拦截器是否正确
2. 清除浏览器localStorage并重新登录
3. 检查Portal SSO服务是否运行

### 问题2: 前端页面空白

**原因**: 可能是React 19兼容性问题
**解决**:
1. 确认已升级到Antd 6.0: `npm list antd`
2. 清除浏览器缓存 (Ctrl + Shift + R)
3. 检查控制台错误信息

### 问题3: 后端无法启动

**原因**: Python依赖或数据库连接问题
**解决**:
```bash
# 检查Python虚拟环境
cd backend
source venv/bin/activate  # Linux/Mac
pip list  # 查看已安装的包

# 检查数据库连接
python -c "from app import create_app; app = create_app(); print('OK')"
```

### 问题4: PM2服务频繁重启

**原因**: 端口冲突或代码错误
**解决**:
```bash
# 查看PM2日志
pm2 logs shm-backend --lines 50

# 检查端口占用
# Windows
netstat -ano | findstr :8006

# Linux
lsof -i :8006
```

---

## 🌐 生产环境配置

### 1. 使用Nginx反向代理

**nginx.conf**:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://localhost:7500;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后端API
    location /api {
        proxy_pass http://localhost:8006;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 启用HTTPS

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # ... 其他配置同上
}
```

### 3. 生产环境检查清单

- [ ] DEBUG=False (后端.env)
- [ ] 强SECRET_KEY (后端.env)
- [ ] 使用MySQL替代SQLite
- [ ] 配置CORS为实际域名
- [ ] 启用HTTPS
- [ ] 配置防火墙规则
- [ ] 设置日志轮转
- [ ] 配置PM2开机自启
- [ ] 建立数据库备份策略

---

## 📈 性能优化

### 前端优化

1. **代码分割** (已通过Vite自动处理)
2. **Gzip压缩** (Nginx配置)
3. **CDN加速** (可选)

### 后端优化

1. **数据库索引**:
```sql
CREATE INDEX idx_shipment_status ON shipments(status);
CREATE INDEX idx_shipment_customer ON shipments(customer_id);
CREATE INDEX idx_shipment_date ON shipments(ship_date);
```

2. **数据库连接池** (config.py):
```python
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20
```

3. **Redis缓存** (可选):
```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'redis'})
```

---

## 📞 技术支持

### 日志位置

- **PM2日志**: `~/.pm2/logs/`
- **Flask日志**: 控制台输出
- **Nginx日志**: `/var/log/nginx/`

### 常用命令

```bash
# PM2管理
pm2 list              # 查看所有服务
pm2 logs shm-backend  # 查看后端日志
pm2 restart shm-frontend  # 重启前端
pm2 stop all          # 停止所有服务
pm2 save              # 保存当前配置
pm2 startup           # 配置开机自启

# 数据库管理
cd backend
source venv/bin/activate
flask shell           # 进入Flask shell
flask db migrate      # 创建迁移
flask db upgrade      # 执行迁移
```

---

## 📋 系统要求

### 最低要求

- **Node.js**: >= 18.0
- **Python**: >= 3.8
- **内存**: >= 512MB
- **磁盘**: >= 1GB

### 推荐配置

- **Node.js**: >= 20.0
- **Python**: >= 3.10
- **内存**: >= 2GB
- **磁盘**: >= 5GB
- **MySQL**: >= 5.7 (生产环境)

---

## 🎯 下一步

1. **运行部署脚本** - `deploy.bat` 或 `deploy.sh`
2. **验证所有功能** - 按照验证清单测试
3. **配置生产环境** - 参考生产环境配置章节
4. **设置监控告警** - 配置PM2监控或第三方服务
5. **建立备份策略** - 定期备份数据库

---

**部署准备时间**: 2025-12-01
**文档版本**: 1.0
**状态**: ✅ 已准备就绪

**现在可以开始部署了！** 🚀
