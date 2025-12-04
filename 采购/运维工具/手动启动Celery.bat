@echo off
chcp 65001 >nul
cd /d "%~dp0\backend"

echo ========================================
echo    Celery Worker 启动器
echo ========================================
echo.
echo 正在启动 Celery Worker...
echo.

python -m celery -A app.celery worker --loglevel=info --pool=solo

pause
