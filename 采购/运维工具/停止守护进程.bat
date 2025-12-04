@echo off
chcp 65001 >nul
echo ====================================
echo   停止WSL进程守护者
echo ====================================
echo.

echo 正在查找守护进程...
powershell -ExecutionPolicy Bypass -Command ^
    "$processes = Get-WmiObject Win32_Process -Filter \"name='powershell.exe'\"; " ^
    "$found = $false; " ^
    "foreach ($proc in $processes) { " ^
    "    if ($proc.CommandLine -like '*WSL进程守护者.ps1*') { " ^
    "        Write-Host \"找到守护进程 PID: $($proc.ProcessId)\" -ForegroundColor Yellow; " ^
    "        Stop-Process -Id $proc.ProcessId -Force; " ^
    "        Write-Host \"✅ 守护进程已停止\" -ForegroundColor Green; " ^
    "        $found = $true; " ^
    "    } " ^
    "} " ^
    "if (-not $found) { " ^
    "    Write-Host \"未找到运行中的守护进程\" -ForegroundColor Gray; " ^
    "}"

echo.
pause
