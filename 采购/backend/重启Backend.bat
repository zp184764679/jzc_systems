@echo off
chcp 65001 >nul

echo ============================================================
echo 重启Backend服务
echo ============================================================
echo.

echo [1/2] 停止旧的Backend进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001.*LISTENING"') do (
    echo 找到进程 PID: %%a
    taskkill /PID %%a /F >nul 2>&1
)
echo ✅ 旧进程已停止
echo.

echo [2/2] 启动新的Backend进程...
cd /d "%~dp0"
start "采购系统-Backend" cmd /k "python app.py"
echo ✅ Backend已重新启动
echo.

echo 等待3秒检查状态...
timeout /t 3 /nobreak >nul

netstat -ano | findstr ":5001.*LISTENING" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Backend正在监听端口 5001
) else (
    echo ⚠️  Backend可能未成功启动，请检查窗口
)

echo.
echo ============================================================
pause
