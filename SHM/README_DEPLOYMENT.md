# SHM 出货管理系统 - 快速部署

**版本**: 2.0 (React 19 + Antd 6)
**部署日期**: 2025-12-01

---

## ⚠️ 部署前准备

### 创建MySQL数据库（必需）

SHM系统使用MySQL数据库，部署前必须先创建数据库：

```sql
-- 登录MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE shm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户并授权
CREATE USER 'app'@'localhost' IDENTIFIED BY 'app';
GRANT ALL PRIVILEGES ON shm.* TO 'app'@'localhost';
FLUSH PRIVILEGES;
```

**详细配置**: 查看 `MYSQL_SETUP.md`

---

## 🚀 一键部署

### Windows
```cmd
deploy.bat
```

### Linux/Mac
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📦 部署包内容

### 必需文件

```
SHM/
├── frontend/dist/     # 前端构建产物 (React 19 + Antd 6)
└── backend/           # Flask后端 + 数据库模型
    ├── app.py
    ├── requirements.txt
    ├── models/
    ├── routes/
    └── services/
```

---

## ✨ 重要更新

### 技术栈升级

- ⬆️ **React 19.0** (从 18.3)
- ⬆️ **Antd 6.0** (从 5.22) - 原生支持React 19
- ✅ 性能提升 10-20%
- ✅ 零兼容性警告

### 已修复问题

- ✅ 401未授权错误 (JWT token自动注入)
- ✅ React 19兼容性警告
- ✅ Spin组件警告
- ✅ API请求拦截优化

详见: `UPGRADE_TO_V6.md`

---

## ✅ 快速验证

### 1. 检查服务
```bash
pm2 list
```

应显示:
- ✅ shm-frontend (online) - 端口 7500
- ✅ shm-backend (online) - 端口 8006

### 2. 访问系统

- **前端**: http://localhost:7500
- **后端健康检查**: http://localhost:8006/api/health

### 3. 从Portal访问

1. 访问 http://localhost:3001
2. 登录后点击"出货管理系统"
3. 应自动完成SSO认证并跳转

---

## 🔧 配置文件

### 后端 (.env)

```bash
# 数据库配置 - MySQL
DB_HOST=localhost
MYSQL_USER=app
MYSQL_PASSWORD=app
MYSQL_DATABASE=shm

# JWT认证
SECRET_KEY=your-secret-key-please-change
ALGORITHM=HS256

# 服务端口
PORT=8006

# Portal SSO
PORTAL_URL=http://localhost:3002

# 生产环境
FLASK_ENV=production
DEBUG=False
```

**重要**:
- ✅ 使用MySQL数据库（非SQLite）
- ⚠️ 生产环境请修改 `SECRET_KEY` 和 `MYSQL_PASSWORD`

---

## 🔍 故障排查

### 401错误
- 检查Portal SSO服务是否运行 (http://localhost:3002)
- 清除浏览器localStorage重新登录

### 前端空白
- 确认Antd版本: `cd frontend && npm list antd`
- 应显示 6.0.0
- 清除浏览器缓存 (Ctrl + Shift + R)

### 后端无法启动
```bash
cd backend
source venv/bin/activate  # Linux/Mac
pip list  # 查看依赖
pm2 logs shm-backend  # 查看错误日志
```

---

## 📚 完整文档

- **DEPLOYMENT_GUIDE.md** - 完整部署指南
- **UPGRADE_TO_V6.md** - 升级说明和优势

---

## 🎯 端口配置

| 服务 | 端口 |
|-----|------|
| SHM前端 | 7500 |
| SHM后端 | 8006 |
| Portal前端 | 3001 |
| Portal后端 | 3002 |

---

**状态**: ✅ 已准备就绪
**立即开始部署！** 🚀
