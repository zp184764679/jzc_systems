@echo off
chcp 65001 >nul
echo ====================================
echo   注册Windows系统服务（需要管理员权限）
echo ====================================
echo.
echo 此操作将：
echo 1. 下载并安装NSSM工具
echo 2. 将守护进程注册为Windows系统服务
echo 3. 配置服务开机自启动
echo.
echo 系统服务的优势：
echo - 开机自动启动
echo - 系统级保护，难以被误杀
echo - 可在服务管理器中统一管理
echo.
echo 按任意键继续...
pause >nul

echo.
echo 正在以管理员权限运行...
powershell -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File \"%~dp0注册Windows系统服务.ps1\"' -Verb RunAs"

echo.
echo 请在弹出的管理员窗口中查看执行结果
pause
