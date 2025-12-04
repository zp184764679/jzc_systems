@echo off
chcp 65001 >nul
echo ========================================
echo   创建开机自启快捷方式
echo ========================================
echo.

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%~dp0..
set LAUNCHER="%SCRIPT_DIR%launcher.pyw"
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

echo 启动器路径: %LAUNCHER%
echo 项目目录: %PROJECT_DIR%
echo 启动文件夹: %STARTUP_FOLDER%
echo.

:: 创建快捷方式（使用PowerShell）
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%STARTUP_FOLDER%\报价系统.lnk'); $SC.TargetPath = '%SCRIPT_DIR%launcher.pyw'; $SC.WorkingDirectory = '%PROJECT_DIR%'; $SC.WindowStyle = 7; $SC.Description = '机加工报价系统自动启动'; $SC.Save()"

if exist "%STARTUP_FOLDER%\报价系统.lnk" (
    echo.
    echo ========================================
    echo   ✓ 成功！开机自启已设置
    echo ========================================
    echo.
    echo 快捷方式已创建到启动文件夹
    echo 下次开机会自动启动报价系统
    echo.
    echo 如需取消自启，请删除以下文件：
    echo %STARTUP_FOLDER%\报价系统.lnk
) else (
    echo.
    echo ========================================
    echo   ✗ 创建失败
    echo ========================================
)

echo.
pause
