@echo off
chcp 65001 >nul
echo ========================================
echo 启动采购系统后台服务
echo ========================================

echo.
echo [1/3] 检查 Redis...
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Redis 未运行
    echo 请先安装并启动Redis，参见: 启动Redis和Celery.md
    echo.
    echo 快速启动方式:
    echo   Docker: docker run -d -p 6379:6379 redis
    echo   或下载: https://github.com/tporadowski/redis/releases
    pause
    exit /b 1
) else (
    echo ✅ Redis 已运行
)

echo.
echo [2/3] 启动 Celery Worker...
cd /d "%~dp0backend"
start "Celery Worker - 采购系统" cmd /k "celery -A celery_app worker --pool=solo --loglevel=info"
timeout /t 2 >nul

echo.
echo [3/3] 启动 Flask 后端...
start "Flask Backend - 采购系统" cmd /k "python app.py"

echo.
echo ========================================
echo ✅ 所有服务已启动！
echo ========================================
echo.
echo 打开的窗口:
echo   [窗口1] Celery Worker - 处理后台任务
echo   [窗口2] Flask Backend - API服务
echo.
echo 现在可以启动前端了:
echo   cd frontend
echo   npm run dev
echo.
pause
