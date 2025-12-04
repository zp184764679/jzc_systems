@echo off
chcp 65001 >nul
echo ====================================================
echo 📊 MySQL本机配置脚本
echo ====================================================
echo.

echo [步骤1/5] 检查MySQL服务状态...
sc query MySQL90 | find "RUNNING" >nul
if errorlevel 1 (
    echo ❌ MySQL服务未运行，正在启动...
    net start MySQL90
    timeout /t 3 >nul
) else (
    echo ✅ MySQL服务正在运行
)
echo.

echo [步骤2/5] 执行数据库初始化脚本...
echo 请输入MySQL root密码:
mysql -u root -p < "setup_mysql_local.sql"
if errorlevel 1 (
    echo ❌ 数据库初始化失败！
    pause
    exit /b 1
)
echo ✅ 数据库初始化成功
echo.

echo [步骤3/5] 配置MySQL允许外网访问...
echo.
echo ⚠️  需要手动修改MySQL配置文件:
echo.
echo 📝 文件位置: C:\ProgramData\MySQL\MySQL Server 9.0\my.ini
echo.
echo 请在 [mysqld] 部分添加或修改以下内容:
echo.
echo    bind-address = 0.0.0.0
echo    mysqlx-bind-address = 0.0.0.0
echo.
echo 修改完成后按任意键继续...
pause >nul
echo.

echo [步骤4/5] 重启MySQL服务以应用配置...
net stop MySQL90
timeout /t 2 >nul
net start MySQL90
timeout /t 3 >nul
echo ✅ MySQL服务已重启
echo.

echo [步骤5/5] 配置Windows防火墙...
netsh advfirewall firewall delete rule name="MySQL Port 3306" >nul 2>&1
netsh advfirewall firewall add rule name="MySQL Port 3306" dir=in action=allow protocol=TCP localport=3306
echo ✅ 防火墙规则已添加
echo.

echo ====================================================
echo ✅ MySQL配置完成！
echo ====================================================
echo.
echo 📊 数据库信息:
echo    数据库名: caigou_local
echo    用户名: caigou_admin
echo    密码: caigou2025!@#
echo    端口: 3306
echo.
echo 🌐 可访问IP:
echo    本地: localhost / 127.0.0.1
echo    局域网: 192.168.0.6
echo    Ubuntu/WSL2: 172.x.x.x
echo    外网: 61.145.212.28 (需路由器端口映射)
echo.
echo 下一步: 运行 "2_更新Backend配置.bat"
echo ====================================================
pause
