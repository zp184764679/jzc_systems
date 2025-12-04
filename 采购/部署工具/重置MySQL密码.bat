@echo off
chcp 65001 >nul
color 0C
echo ====================================================
echo ⚠️  MySQL Root 密码重置工具
echo ====================================================
echo.
echo 本脚本将重置MySQL root密码为: exak472008
echo.
echo 警告: 此操作需要管理员权限
echo.
echo ====================================================
pause
echo.

echo [步骤1/4] 停止MySQL服务...
net stop MySQL90
if errorlevel 1 (
    echo ❌ 停止服务失败，可能需要管理员权限
    pause
    exit /b 1
)
echo ✅ MySQL服务已停止
echo.
timeout /t 2 >nul

echo [步骤2/4] 以安全模式启动MySQL...
cd "C:\Program Files\MySQL\MySQL Server 9.0\bin"
start "MySQL Safe Mode" mysqld --skip-grant-tables --console
echo ✅ MySQL已在安全模式启动
echo.
timeout /t 5 >nul

echo [步骤3/4] 重置root密码...
mysql -u root -e "FLUSH PRIVILEGES; ALTER USER 'root'@'localhost' IDENTIFIED BY 'exak472008'; FLUSH PRIVILEGES;"
if errorlevel 1 (
    echo ❌ 密码重置失败
    echo 正在关闭MySQL...
    taskkill /F /IM mysqld.exe 2>nul
    pause
    exit /b 1
)
echo ✅ 密码已重置为: exak472008
echo.

echo [步骤4/4] 重启MySQL服务...
echo 正在关闭安全模式...
taskkill /F /IM mysqld.exe 2>nul
timeout /t 3 >nul

echo 正在启动MySQL服务...
net start MySQL90
if errorlevel 1 (
    echo ❌ 服务启动失败
    pause
    exit /b 1
)
echo ✅ MySQL服务已正常启动
echo.

echo ====================================================
echo ✅ 密码重置完成！
echo ====================================================
echo.
echo 新的MySQL root密码: exak472008
echo.
echo 现在可以运行 "一键初始化.bat" 了
echo ====================================================
pause
