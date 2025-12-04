@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo 手动启动Backend（用于调试）
echo ============================================================
echo.

echo 当前目录: %CD%
echo.

echo 检查.env文件...
if exist .env (
    echo ✅ .env 文件存在
) else (
    echo ❌ .env 文件不存在！
    echo 请先运行: 切换到开发环境.bat
    pause
    exit /b 1
)
echo.

echo 启动Backend服务...
echo 按 Ctrl+C 可以停止服务
echo.
echo ============================================================
echo.

python app.py

echo.
echo ============================================================
echo Backend已停止
echo ============================================================
pause
