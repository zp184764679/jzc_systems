@echo off
chcp 65001 >nul
echo ========================================
echo   安装报价系统启动器依赖
echo ========================================
echo.

echo 正在安装Python依赖包...
pip install pystray pillow psutil

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 现在可以双击 launcher.pyw 启动系统
echo 或者运行 create_startup_shortcut.bat 创建开机自启
echo.
pause
