@echo off
chcp 65001 >nul
color 0A
echo ====================================================
echo 📋 MySQL本地部署 - 快速配置指南
echo ====================================================
echo.
echo 已完成的配置:
echo ✅ Backend配置文件已更新 (backend/.env)
echo    - 数据库: caigou_local@localhost:3306
echo    - 用户: caigou_admin
echo    - 密码: caigou2025!@#
echo.
echo ====================================================
echo 需要手动完成的步骤 (需要管理员权限):
echo ====================================================
echo.
echo [步骤1] 修改MySQL配置文件
echo    双击运行: "运行-修改MySQL配置.bat"
echo    - 会请求管理员权限
echo    - 自动添加 bind-address = 0.0.0.0
echo.
echo [步骤2] 创建数据库和用户
echo    请选择以下方式之一:
echo.
echo    方式A: 使用Python脚本 (自动尝试常见密码)
echo       python create_database.py
echo.
echo    方式B: 使用MySQL命令 (需要输入root密码)
echo       mysql -u root -p ^< setup_mysql_local.sql
echo.
echo    方式C: 手动执行SQL
echo       1. mysql -u root -p
echo       2. source C:/Users/Admin/Desktop/采购/部署工具/setup_mysql_local.sql
echo.
echo [步骤3] 配置Windows防火墙
echo    以管理员身份运行命令提示符,执行:
echo    netsh advfirewall firewall add rule name="MySQL Port 3306" dir=in action=allow protocol=TCP localport=3306
echo.
echo [步骤4] 重启MySQL服务
echo    以管理员身份运行命令提示符,执行:
echo    net stop MySQL90
echo    net start MySQL90
echo.
echo [步骤5] 测试数据库连接
echo    双击运行: "3_测试数据库连接.bat"
echo.
echo ====================================================
echo 💡 提示:
echo ====================================================
echo.
echo 如果您有MySQL root密码,可以直接运行:
echo    mysql -u root -p ^< setup_mysql_local.sql
echo.
echo 如果忘记root密码,请:
echo    1. 搜索 "MySQL重置root密码"
echo    2. 或使用MySQL Workbench创建数据库
echo.
echo ====================================================
echo.
pause
