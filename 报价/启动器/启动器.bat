@echo off
chcp 65001 >nul
title 机加工报价系统 - 启动器

echo ========================================
echo    机加工报价系统 - 启动器
echo ========================================
echo.

:: 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

:: 检查依赖是否安装
python -c "import psutil, requests, redis" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装启动器依赖...
    pip install -r requirements.txt
    echo.
)

:: 启动 GUI
echo [启动] 正在启动图形界面...
echo.
python launcher.py

if errorlevel 1 (
    echo.
    echo [错误] 启动失败，请检查错误信息
    pause
)
