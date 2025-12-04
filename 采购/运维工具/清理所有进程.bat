@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ====================================
echo   清理采购系统所有进程 (WSL保护版)
echo ====================================
echo.

REM 设置WSL保护关键词 - 如果进程命令行包含这些，将被保护
set "WSL_PROTECT=caigou-prod venv/bin/python /home/admin redis-server ollama"

echo [1/4] 正在停止前端服务 (端口3000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING"') do (
    echo 终止进程 PID: %%a
    taskkill /F /PID %%a 2>nul
)

echo.
echo [2/4] 正在停止后端服务 (端口5001)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001.*LISTENING"') do (
    echo 终止进程 PID: %%a
    taskkill /F /PID %%a 2>nul
)

echo.
echo [3/4] 正在停止Python进程 (保护WSL进程)...
powershell -ExecutionPolicy Bypass -Command ^
    "$wslKeywords = @('caigou-prod', '/home/admin', 'venv/bin/python', 'redis-server', 'ollama'); " ^
    "$processes = Get-WmiObject Win32_Process -Filter \"name='python.exe'\"; " ^
    "$killed = 0; $protected = 0; " ^
    "foreach ($proc in $processes) { " ^
    "    $cmdLine = $proc.CommandLine; " ^
    "    $isWSL = $false; " ^
    "    foreach ($keyword in $wslKeywords) { " ^
    "        if ($cmdLine -like \"*$keyword*\") { $isWSL = $true; break; } " ^
    "    } " ^
    "    if ($isWSL) { " ^
    "        Write-Host \"[保护] WSL进程 PID:$($proc.ProcessId) - $($cmdLine.Substring(0, [Math]::Min(80, $cmdLine.Length)))\" -ForegroundColor Green; " ^
    "        $protected++; " ^
    "    } else { " ^
    "        Write-Host \"[终止] Windows进程 PID:$($proc.ProcessId)\" -ForegroundColor Yellow; " ^
    "        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue; " ^
    "        $killed++; " ^
    "    } " ^
    "} " ^
    "Write-Host \"`n已终止: $killed 个, 已保护: $protected 个\" -ForegroundColor Cyan"

echo.
echo [4/4] 正在停止Node进程 (排除Claude Code和WSL)...
powershell -ExecutionPolicy Bypass -Command ^
    "$wslKeywords = @('caigou-prod', '/home/admin', 'node_modules/.bin/vite', 'redis-server', 'ollama'); " ^
    "$excludeKeywords = @('claude-code'); " ^
    "$processes = Get-WmiObject Win32_Process -Filter \"name='node.exe'\"; " ^
    "$killed = 0; $protected = 0; " ^
    "foreach ($proc in $processes) { " ^
    "    $cmdLine = $proc.CommandLine; " ^
    "    $isWSL = $false; $isExcluded = $false; " ^
    "    foreach ($keyword in $wslKeywords) { " ^
    "        if ($cmdLine -like \"*$keyword*\") { $isWSL = $true; break; } " ^
    "    } " ^
    "    foreach ($keyword in $excludeKeywords) { " ^
    "        if ($cmdLine -like \"*$keyword*\") { $isExcluded = $true; break; } " ^
    "    } " ^
    "    if ($isWSL -or $isExcluded) { " ^
    "        $reason = if ($isWSL) { 'WSL' } else { 'Claude Code' }; " ^
    "        Write-Host \"[保护] $reason 进程 PID:$($proc.ProcessId)\" -ForegroundColor Green; " ^
    "        $protected++; " ^
    "    } else { " ^
    "        Write-Host \"[终止] Windows进程 PID:$($proc.ProcessId)\" -ForegroundColor Yellow; " ^
    "        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue; " ^
    "        $killed++; " ^
    "    } " ^
    "} " ^
    "Write-Host \"`n已终止: $killed 个, 已保护: $protected 个\" -ForegroundColor Cyan"

echo.
echo ====================================
echo   清理完成！
echo ====================================
echo.
echo ✅ WSL采购系统进程已受保护（含Ollama），未被清理
echo ℹ️  如需清理WSL进程，请使用专用脚本
echo.
pause
