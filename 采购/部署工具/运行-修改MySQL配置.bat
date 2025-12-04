@echo off
chcp 65001 >nul
echo ====================================================
echo 🔧 以管理员权限修改MySQL配置
echo ====================================================
echo.
echo 即将请求管理员权限...
echo.

PowerShell -Command "Start-Process PowerShell -ArgumentList '-ExecutionPolicy Bypass -File \"%~dp0修改MySQL配置.ps1\"' -Verb RunAs"

echo.
echo 请在新窗口中查看执行结果
pause
