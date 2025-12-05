# JZC Systems 生产服务器部署说明

## 服务器信息
- **服务器地址**: jzchardware.cn
- **用户**: aaa
- **代码目录**: `/www/jzc_systems/` (GitHub管理)
- **Git仓库**: `git@github.com:zp184764679/jzc_systems.git`
- **访问地址**: `https://jzchardware.cn:8888`
- **SSH部署密钥**: `~/.ssh/jzc_deploy`

---

## 目录结构

```
/www/jzc_systems/
├── Portal/              # 门户系统 (统一登录入口)
│   ├── backend/         # Flask后端
│   └── dist/            # 前端构建产物
├── HR/                  # 人事管理系统
│   ├── backend/
│   └── frontend/dist/
├── account/             # 账户管理系统
│   ├── backend/
│   └── frontend/dist/
├── 报价/                # 报价系统 (quotation)
│   ├── backend/         # FastAPI后端
│   └── frontend/dist/
├── 采购/                # 采购系统 (caigou)
│   ├── backend/
│   └── frontend/dist/
├── SHM/                 # 出货管理系统
│   ├── backend/
│   └── frontend/dist/
├── shared/              # 共享认证模块 (各后端symlink引用)
│   └── auth/
├── deploy/              # 部署相关文档
├── CRM/                 # CRM系统 (未部署)
├── EAM/                 # 资产管理 (未部署)
├── MES/                 # 制造执行 (未部署)
└── SCM/                 # 供应链 (未部署)
```

---

## 后端服务 (PM2管理)

| 服务名 | 端口 | 框架 | 目录 | 启动命令 |
|--------|------|------|------|----------|
| portal-backend | 3002 | Flask | Portal/backend | `venv/bin/python3 main.py` |
| hr-backend | 8003 | Flask | HR/backend | `venv/bin/python3 main.py` |
| account-backend | 8004 | Flask | account/backend | `venv/bin/python3 main.py` |
| quotation-backend | 8001 | FastAPI | 报价/backend | `venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001` |
| caigou-backend | 5001 | Flask | 采购/backend | `venv/bin/python3 app.py` |
| shm-backend | 8006 | Flask | SHM/backend | `venv/bin/python3 app.py` |

---

## 前端路由 (Nginx静态文件)

| 系统 | URL路径 | API路径 | 静态文件目录 |
|------|---------|---------|--------------|
| Portal | `/` | `/api/` | Portal/dist |
| HR | `/hr/` | `/hr/api/` | HR/frontend/dist |
| Account | `/account/` | `/account/api/` | account/frontend/dist |
| Quotation | `/quotation/` | `/quotation/api/` | 报价/frontend/dist |
| Caigou | `/caigou/` | `/caigou/api/` | 采购/frontend/dist |
| SHM | `/shm/` | `/shm/api/` | SHM/frontend/dist |

---

## 常用运维命令

### 代码更新
```bash
# 拉取最新代码
cd /www/jzc_systems
GIT_SSH_COMMAND="ssh -i ~/.ssh/jzc_deploy -o StrictHostKeyChecking=no" git pull
```

### 前端构建
```bash
# 构建所有前端
cd /www/jzc_systems/Portal && npm install && npm run build
cd /www/jzc_systems/HR/frontend && npm install && npm run build
cd /www/jzc_systems/account/frontend && npm install && npm run build
cd /www/jzc_systems/报价/frontend && npm install && npm run build
cd /www/jzc_systems/采购/frontend && npm install && npm run build
cd /www/jzc_systems/SHM/frontend && npm install && npm run build
```

### 后端管理
```bash
# 查看服务状态
pm2 list

# 重启所有后端
pm2 restart all

# 重启单个服务
pm2 restart portal-backend

# 查看日志
pm2 logs                    # 所有日志
pm2 logs hr-backend         # 指定服务日志
pm2 logs --lines 100        # 最近100行

# 保存PM2配置 (重启后自动恢复)
pm2 save
```

### Nginx管理
```bash
# 测试配置
sudo nginx -t

# 重新加载配置
sudo systemctl reload nginx

# 查看状态
sudo systemctl status nginx
```

### 健康检查
```bash
# 检查所有API
curl http://127.0.0.1:3002/health   # Portal
curl http://127.0.0.1:8003/health   # HR
curl http://127.0.0.1:8004/health   # Account
curl http://127.0.0.1:8001/health   # Quotation
curl http://127.0.0.1:5001/api/health  # Caigou
curl http://127.0.0.1:8006/api/health  # SHM
```

---

## 配置文件位置

| 配置 | 路径 |
|------|------|
| Nginx主配置 | `/etc/nginx/nginx.conf` |
| SSL证书 | `/etc/letsencrypt/live/jzchardware.cn/` |
| PM2配置 | `~/.pm2/dump.pm2` |
| 环境变量 | 各后端目录下 `.env` 文件 |
| 共享认证模块 | `/www/jzc_systems/shared/` |

---

## 数据库

- **MySQL**: localhost:3306
  - 数据库: `hr`, `account`, `quotation`, `caigou`, `shm`, `auth`
  - 用户: 见各系统 `.env` 文件

---

## 部署流程 (完整更新)

```bash
# 1. 拉取代码
cd /www/jzc_systems
GIT_SSH_COMMAND="ssh -i ~/.ssh/jzc_deploy -o StrictHostKeyChecking=no" git pull

# 2. 安装后端依赖 (如有新依赖)
cd /www/jzc_systems/HR/backend && ./venv/bin/pip install -r requirements.txt
# ... 其他系统类似

# 3. 构建前端
cd /www/jzc_systems/Portal && npm install && npm run build
cd /www/jzc_systems/HR/frontend && npm install && npm run build
cd /www/jzc_systems/account/frontend && npm install && npm run build
cd /www/jzc_systems/报价/frontend && npm install && npm run build
cd /www/jzc_systems/采购/frontend && npm install && npm run build
cd /www/jzc_systems/SHM/frontend && npm install && npm run build

# 4. 重启后端服务
pm2 restart all

# 5. 保存配置
pm2 save
```

---

## 注意事项

1. **共享模块**: 各后端通过symlink引用 `/www/jzc_systems/shared/`，修改shared会影响所有系统
2. **环境变量**: `.env` 文件不在Git中，需手动维护
3. **端口冲突**: SHM使用8006端口 (不是8005)
4. **中文目录**: `报价/` 和 `采购/` 是中文目录名，命令行操作时注意引号
5. **SSL证书**: Let's Encrypt证书，需定期更新
