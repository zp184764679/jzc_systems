@echo off
chcp 65001 >nul
color 0B

:MENU
cls
echo ====================================================
echo 📊 采购系统 - 数据库配置菜单
echo ====================================================
echo.
echo 请选择操作:
echo.
echo [1] 重置MySQL root密码 (推荐)
echo     将本地MySQL root密码重置为: exak472008
echo.
echo [2] 使用远程数据库
echo     配置Backend使用远程MySQL (61.145.212.28)
echo.
echo [3] 一键初始化数据库
echo     创建数据库、用户和测试数据
echo.
echo [4] 打开部署工具文件夹
echo.
echo [0] 退出
echo.
echo ====================================================
echo.
set /p choice=请输入选项 (0-4):

if "%choice%"=="1" goto RESET_PASSWORD
if "%choice%"=="2" goto USE_REMOTE
if "%choice%"=="3" goto INIT_DB
if "%choice%"=="4" goto OPEN_FOLDER
if "%choice%"=="0" exit
goto MENU

:RESET_PASSWORD
cls
echo.
echo 正在启动密码重置工具...
echo 注意: 需要管理员权限
echo.
pause
powershell -Command "Start-Process '%~dp0重置MySQL密码.bat' -Verb RunAs"
goto MENU

:USE_REMOTE
cls
echo.
echo 正在配置远程数据库...
echo.
call "%~dp0使用远程数据库.bat"
pause
goto MENU

:INIT_DB
cls
echo.
echo 正在启动数据库初始化...
echo.
call "%~dp0一键初始化.bat"
pause
goto MENU

:OPEN_FOLDER
start "" "%~dp0"
goto MENU
