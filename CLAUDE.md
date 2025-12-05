# JZC 企业管理系统 - Claude Code 项目上下文

## 项目概述
这是一个包含 10 个子系统的企业 ERP 系统，采用微服务架构。

## 技术栈
- **前端**: React 18 + Vite + Ant Design
- **后端**: Python Flask + SQLAlchemy
- **数据库**: MySQL 8.0
- **认证**: JWT (统一 SSO)
- **部署**: PM2 + Nginx + GitHub Actions

## 子系统列表

| 系统 | 目录 | 后端端口 | 前端路径 | 数据库 |
|------|------|----------|----------|--------|
| Portal | Portal/ | 3002 | / | cncplan |
| HR | HR/ | 8003 | /hr | hr_system |
| CRM | CRM/ | 8002 | /crm | cncplan |
| SCM | SCM/ | 8005 | /scm | cncplan |
| SHM | SHM/ | 8006 | /shm | cncplan |
| EAM | EAM/ | 8008 | /eam | cncplan |
| MES | MES/ | 8007 | /mes | cncplan |
| Account | account/ | 8001 | /account | cncplan |
| 报价 | 报价/ | 8009 | /quote | cncplan |
| 采购 | 采购/ | 8010 | /purchase | cncplan |

## 目录结构规范
每个子系统遵循统一结构：
```
{系统名}/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models/      # SQLAlchemy 模型
│   │   └── routes/      # Flask 路由
│   ├── main.py          # Flask 入口
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.jsx
        ├── components/
        └── pages/
```

## 常用命令

### 开发
```bash
# 启动后端 (在各子系统的 backend 目录)
python main.py

# 启动前端 (在各子系统的 frontend 目录)
npm run dev

# 构建前端
npm run build
```

### PM2 管理
```bash
pm2 list              # 查看所有服务
pm2 restart all       # 重启所有服务
pm2 logs [name]       # 查看日志
pm2 monit             # 监控面板
```

### Git 部署
```bash
git add . && git commit -m "更新说明" && git push origin main
gh workflow run deploy.yml --repo zp184764679/jzc_systems
```

### 数据库
```bash
mysqldump -u root -p cncplan > backup.sql
mysqldump -u root -p hr_system > hr_backup.sql
```

## 系统集成关系
- 所有子系统共享 Portal 的 SSO 认证 (JWT Token)
- HR 系统提供员工/部门信息给其他系统
- SHM 调用 SCM 扣减库存
- 采购系统与 CRM 同步供应商信息

## 生产环境
- **域名**: https://jzchardware.cn:8888
- **GitHub**: https://github.com/zp184764679/jzc_systems
- **自动部署**: Push 到 main 分支触发 GitHub Actions

## 注意事项
- 所有 API 地址使用环境变量配置，不要硬编码
- JWT 密钥在 .env.production 中配置
- 跨系统调用时验证 Token 有效性
