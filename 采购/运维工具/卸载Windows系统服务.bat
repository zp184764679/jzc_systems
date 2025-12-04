@echo off
chcp 65001 >nul
echo ====================================
echo   卸载Windows系统服务
echo ====================================
echo.
echo 此操作将卸载WSL采购系统守护服务
echo.
pause

powershell -ExecutionPolicy Bypass -Command ^
    "if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) { " ^
    "    Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -Command \"Stop-Service WSLCaigouGuardian -Force; sc.exe delete WSLCaigouGuardian; Write-Host ''''; Write-Host ''✅ 服务已卸载'' -ForegroundColor Green; pause\"' -Verb RunAs; " ^
    "} else { " ^
    "    Stop-Service WSLCaigouGuardian -Force -ErrorAction SilentlyContinue; " ^
    "    sc.exe delete WSLCaigouGuardian; " ^
    "    Write-Host ''; " ^
    "    Write-Host '✅ 服务已卸载' -ForegroundColor Green; " ^
    "    pause; " ^
    "}"
