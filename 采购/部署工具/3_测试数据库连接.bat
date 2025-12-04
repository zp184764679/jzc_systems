@echo off
chcp 65001 >nul
echo ====================================================
echo 🧪 测试MySQL数据库连接
echo ====================================================
echo.

cd /d "%~dp0"

echo 正在运行测试脚本...
echo.

python test_mysql_connection.py

echo.
echo ====================================================
pause
