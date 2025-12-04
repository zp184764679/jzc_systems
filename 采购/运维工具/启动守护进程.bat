@echo off
chcp 65001 >nul
echo ====================================
echo   启动WSL进程守护者
echo ====================================
echo.
echo 守护进程将在后台运行，监控WSL采购系统
echo 如果服务被停止，将自动重启
echo.
echo 按任意键启动守护进程...
pause >nul

echo.
echo 正在启动守护进程（隐藏窗口模式）...

powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0WSL进程守护者.ps1"

echo.
echo ✅ 守护进程已在后台启动
echo.
echo 查看日志：%~dp0守护者日志.txt
echo 停止守护：任务管理器关闭 powershell.exe（WSL进程守护者）
echo.
pause
