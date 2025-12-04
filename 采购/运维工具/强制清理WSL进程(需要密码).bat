@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

color 0C
echo ====================================
echo   ⚠️  强制清理WSL采购系统进程
echo ====================================
echo.
echo 警告：此操作将关闭WSL中的采购系统！
echo.
echo 这包括：
echo   - Flask 后端服务 (5001, 5002)
echo   - Vite 前端服务 (5000)
echo   - Celery Worker
echo   - 所有相关Python进程
echo.
echo ====================================
echo.

REM 设置密码（您可以修改这个密码）
set "CORRECT_PASSWORD=caigou2025"

REM 提示输入密码
set /p "INPUT_PASSWORD=请输入管理员密码以继续: "

REM 验证密码
if not "!INPUT_PASSWORD!"=="%CORRECT_PASSWORD%" (
    echo.
    color 0C
    echo ❌ 密码错误！操作已取消。
    echo.
    echo WSL进程受到保护，未执行任何操作。
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ 密码正确，开始清理WSL进程...
echo.
color 0E

echo [1/3] 正在查找并终止WSL Python进程...
powershell -ExecutionPolicy Bypass -Command ^
    "$wslKeywords = @('caigou-prod', '/home/admin', 'venv/bin/python'); " ^
    "$processes = Get-WmiObject Win32_Process -Filter \"name='python.exe'\"; " ^
    "$killed = 0; " ^
    "foreach ($proc in $processes) { " ^
    "    $cmdLine = $proc.CommandLine; " ^
    "    $isWSL = $false; " ^
    "    foreach ($keyword in $wslKeywords) { " ^
    "        if ($cmdLine -like \"*$keyword*\") { $isWSL = $true; break; } " ^
    "    } " ^
    "    if ($isWSL) { " ^
    "        Write-Host \"[终止] WSL Python PID:$($proc.ProcessId) - $($cmdLine.Substring(0, [Math]::Min(60, $cmdLine.Length)))\" -ForegroundColor Red; " ^
    "        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue; " ^
    "        $killed++; " ^
    "    } " ^
    "} " ^
    "Write-Host \"`n已终止 $killed 个WSL Python进程\" -ForegroundColor Yellow"

echo.
echo [2/3] 正在查找并终止WSL Node进程...
powershell -ExecutionPolicy Bypass -Command ^
    "$wslKeywords = @('caigou-prod', '/home/admin', 'node_modules/.bin/vite'); " ^
    "$processes = Get-WmiObject Win32_Process -Filter \"name='node.exe'\"; " ^
    "$killed = 0; " ^
    "foreach ($proc in $processes) { " ^
    "    $cmdLine = $proc.CommandLine; " ^
    "    $isWSL = $false; " ^
    "    foreach ($keyword in $wslKeywords) { " ^
    "        if ($cmdLine -like \"*$keyword*\") { $isWSL = $true; break; } " ^
    "    } " ^
    "    if ($isWSL) { " ^
    "        Write-Host \"[终止] WSL Node PID:$($proc.ProcessId)\" -ForegroundColor Red; " ^
    "        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue; " ^
    "        $killed++; " ^
    "    } " ^
    "} " ^
    "Write-Host \"`n已终止 $killed 个WSL Node进程\" -ForegroundColor Yellow"

echo.
echo [3/3] 清理相关端口占用...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000.*LISTENING"') do (
    echo 清理端口5000，PID: %%a
    taskkill /F /PID %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001.*LISTENING"') do (
    echo 清理端口5001，PID: %%a
    taskkill /F /PID %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5002.*LISTENING"') do (
    echo 清理端口5002，PID: %%a
    taskkill /F /PID %%a 2>nul
)

echo.
color 0A
echo ====================================
echo   ✅ WSL进程清理完成！
echo ====================================
echo.
echo 后续操作建议：
echo 1. 在WSL中重新启动采购系统
echo 2. 检查数据库和Redis连接状态
echo 3. 验证所有服务正常运行
echo.
pause
