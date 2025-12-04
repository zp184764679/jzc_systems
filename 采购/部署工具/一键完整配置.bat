@echo off
chcp 65001 >nul
color 0B
echo ====================================================
echo 🚀 采购系统 - 一键完整配置
echo ====================================================
echo.
echo 本脚本将完成以下配置:
echo [1] 设置网络优先级 (Ethernet优先, Ethernet 4用于服务器)
echo [2] 配置Windows防火墙 (MySQL:3306, Backend:5001, Frontend:3000)
echo [3] 创建MySQL数据库和用户 (exzzz / exak472008)
echo [4] 修改MySQL配置允许外网访问
echo [5] 重启MySQL服务
echo.
echo 需要:
echo - 管理员权限
echo - MySQL root密码: exak472008
echo.
echo ====================================================
pause
echo.

:: ============================================
:: 步骤1: 配置网络优先级和防火墙
:: ============================================
echo [步骤1/5] 配置网络优先级和防火墙...
echo.
echo 正在请求管理员权限...
powershell -Command "Start-Process PowerShell -ArgumentList '-ExecutionPolicy Bypass -File \"%~dp0配置网络优先级.ps1\"' -Verb RunAs -Wait"

echo.
echo ✅ 网络和防火墙配置完成
echo.
timeout /t 2 >nul

:: ============================================
:: 步骤2: 修改MySQL配置
:: ============================================
echo [步骤2/5] 修改MySQL配置文件...
echo.
echo 正在请求管理员权限...
powershell -Command "Start-Process PowerShell -ArgumentList '-ExecutionPolicy Bypass -File \"%~dp0修改MySQL配置.ps1\"' -Verb RunAs -Wait"

echo.
echo ✅ MySQL配置文件已更新
echo.
timeout /t 2 >nul

:: ============================================
:: 步骤3: 创建数据库和用户
:: ============================================
echo [步骤3/5] 创建MySQL数据库和用户...
echo.

cd /d "%~dp0"

echo 尝试使用密码 exak472008 连接MySQL...
python create_database.py

if errorlevel 1 (
    echo.
    echo ⚠️  Python脚本失败，尝试使用MySQL命令...
    echo.
    mysql -u root -pexak472008 < setup_mysql_local.sql 2>nul

    if errorlevel 1 (
        echo ❌ 数据库创建失败
        echo.
        echo 请手动执行:
        echo    mysql -u root -p < setup_mysql_local.sql
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ✅ 数据库和用户创建成功
echo.
timeout /t 2 >nul

:: ============================================
:: 步骤4: 重启MySQL服务
:: ============================================
echo [步骤4/5] 重启MySQL服务...
echo.

echo 正在停止MySQL服务...
net stop MySQL90 2>nul
timeout /t 2 >nul

echo 正在启动MySQL服务...
net start MySQL90

if errorlevel 1 (
    echo ❌ MySQL服务启动失败
    echo.
    pause
    exit /b 1
)

echo ✅ MySQL服务已重启
echo.
timeout /t 2 >nul

:: ============================================
:: 步骤5: 测试数据库连接
:: ============================================
echo [步骤5/5] 测试数据库连接...
echo.

python test_mysql_connection.py

if errorlevel 1 (
    echo.
    echo ⚠️  数据库连接测试失败
    echo.
)

echo.

:: ============================================
:: 完成
:: ============================================
echo ====================================================
echo ✅ 所有配置已完成！
echo ====================================================
echo.
echo 📊 数据库配置:
echo    数据库: caigou_local@localhost:3306
echo    用户: exzzz
echo    密码: exak472008
echo.
echo 🌐 网络配置:
echo    日常网络: Ethernet (192.168.0.6) - 优先级 1
echo    服务器网络: Ethernet 4 (192.168.5.125) - 公网 61.145.212.28
echo.
echo 🔥 防火墙已开放端口:
echo    MySQL: 3306
echo    Backend: 5001
echo    Frontend: 3000
echo.
echo 📝 Backend已配置为:
echo    数据库用户: exzzz
echo    数据库密码: exak472008
echo.
echo 🚀 现在可以启动Backend和Frontend服务了!
echo.
echo ====================================================
pause
