@echo off
chcp 65001 >nul
cd /d "%~dp0\..\..\"

echo ============================================================
echo 采购系统 - 数据库初始化
echo ============================================================
echo.

echo [1/3] 创建caigou数据库...
mysql -u root -pexak472008 -e "CREATE DATABASE IF NOT EXISTS caigou CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>nul
if %errorlevel% == 0 (
    echo ✅ 数据库创建成功
) else (
    echo ❌ 数据库创建失败，请检查MySQL密码
    pause
    exit /b 1
)
echo.

echo [2/3] 初始化数据库表结构...
cd 部署工具
python 快速初始化远程数据库.py
echo.

echo [3/3] 验证初始化结果...
mysql -u root -pexak472008 caigou -e "SHOW TABLES;" 2>nul
if %errorlevel% == 0 (
    echo ✅ 数据库初始化成功！
) else (
    echo ❌ 验证失败
    pause
    exit /b 1
)
echo.

echo ============================================================
echo 初始化完成！
echo ============================================================
echo.
echo 测试账号：
echo.
echo   👤 管理员账户:
echo      用户名: 周鹏
echo      密码: exak472008
echo      邮箱: jzchardware@gmail.com
echo.
echo   👤 测试用户:
echo      用户名: exzzz
echo      密码: exak472008
echo.
echo 启动项目：
echo   使用: 运维工具\启动采购系统.bat
echo.
pause
