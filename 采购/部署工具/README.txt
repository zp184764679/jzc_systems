====================================================
采购系统MySQL本地部署工具包
====================================================

## 📋 部署架构

Windows本机:
- 开发环境 (Backend + Frontend)
- MySQL数据库 (对外提供服务)
- 文件存储

Ubuntu (WSL2或双系统):
- 生产环境部署 (Nginx + Gunicorn + Celery)
- 连接Windows上的MySQL数据库

## 🚀 快速开始

### 方法1: 一键自动配置 (推荐)

直接运行: "一键配置MySQL本地部署.bat"

这个脚本会自动完成:
1. 修改MySQL配置允许外网访问
2. 重启MySQL服务
3. 创建数据库和用户
4. 配置Windows防火墙
5. 更新Backend配置文件
6. 测试数据库连接

注意: 需要输入MySQL root密码

### 方法2: 分步手动配置

步骤1: 配置MySQL外网访问
运行: "1_配置MySQL本机访问.bat"
- 需要手动编辑my.ini文件
- 需要输入MySQL root密码

步骤2: 更新Backend配置
运行: "2_更新Backend配置.bat"

步骤3: 测试数据库连接
运行: "3_测试数据库连接.bat"

## 📊 数据库信息

数据库名: caigou_local
用户名: caigou_admin
密码: caigou2025!@#
端口: 3306

## 🌐 访问地址

本地开发 (Windows):
- 数据库: localhost:3306
- Backend: http://localhost:5001
- Frontend: http://localhost:3000

局域网访问:
- 数据库: 192.168.0.6:3306
- Backend: http://192.168.0.6:5001
- Frontend: http://192.168.0.6:3000

外网访问 (需配置路由器端口映射):
- 公网IP: 61.145.212.28
- 数据库: 61.145.212.28:3306

Ubuntu部署访问 (从Ubuntu连接Windows):
- 数据库: 192.168.0.6:3306 (局域网)
- 或: 172.x.x.x:3306 (WSL2)

## 📝 配置文件说明

setup_mysql_local.sql
- MySQL数据库初始化脚本
- 创建数据库和用户
- 配置访问权限

修改MySQL配置.ps1
- 修改MySQL的my.ini文件
- 添加bind-address配置
- 需要管理员权限

test_mysql_connection.py
- 测试数据库连接
- 验证配置是否正确

ubuntu_deploy_config.sh
- Ubuntu部署配置脚本
- 配置环境变量和服务

## ⚠️ 注意事项

1. 防火墙配置
   - Windows防火墙需允许3306端口
   - 路由器需配置端口映射(如需外网访问)

2. MySQL配置
   - my.ini中bind-address必须设置为0.0.0.0
   - 重启MySQL服务后才生效

3. 安全建议
   - 生产环境请修改数据库密码
   - 配置SSL加密连接
   - 限制数据库访问IP范围

4. Ubuntu部署
   - 确保Ubuntu能访问Windows的IP地址
   - 修改backend/.env中的DB_HOST为Windows IP
   - 使用ubuntu_deploy_config.sh配置环境

## 🔧 故障排查

问题1: 无法连接数据库
解决:
- 检查MySQL服务是否运行
- 检查my.ini中bind-address配置
- 检查Windows防火墙3306端口
- 使用 netstat -an | findstr 3306 查看端口监听

问题2: 权限不足
解决:
- 以管理员身份运行脚本
- 检查MySQL用户权限

问题3: Ubuntu无法连接Windows MySQL
解决:
- ping Windows IP地址测试网络
- 检查Windows防火墙
- 确认MySQL监听0.0.0.0而非127.0.0.1
- WSL2需要使用Windows的实际IP,不能用localhost

## 📞 技术支持

如有问题,请检查:
1. backend/logs/app.log
2. MySQL错误日志
3. Windows事件查看器

====================================================
