# -*- coding: utf-8 -*-
# PowerShell脚本: 配置网络优先级和服务器外网访问
# 需要管理员权限运行

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "🌐 配置网络优先级和服务器外网访问" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ 需要管理员权限运行此脚本" -ForegroundColor Red
    Write-Host "请以管理员身份运行PowerShell" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ 管理员权限验证通过" -ForegroundColor Green
Write-Host ""

# ============================================
# 步骤1: 查看当前网络接口配置
# ============================================
Write-Host "[1/4] 查看当前网络接口配置..." -ForegroundColor Yellow
Write-Host ""

$adapters = Get-NetIPInterface -AddressFamily IPv4 | Where-Object {$_.ConnectionState -eq 'Connected' -and $_.InterfaceAlias -match 'Ethernet'}

Write-Host "当前活动的Ethernet接口:" -ForegroundColor Cyan
$adapters | Format-Table InterfaceAlias, InterfaceIndex, InterfaceMetric, ConnectionState -AutoSize

$ethernetIndex = ($adapters | Where-Object {$_.InterfaceAlias -eq 'Ethernet'}).InterfaceIndex
$ethernet4Index = ($adapters | Where-Object {$_.InterfaceAlias -eq 'Ethernet 4'}).InterfaceIndex

Write-Host ""
Write-Host "Ethernet (日常用): InterfaceIndex=$ethernetIndex" -ForegroundColor White
Write-Host "Ethernet 4 (服务器用): InterfaceIndex=$ethernet4Index" -ForegroundColor White
Write-Host ""

# ============================================
# 步骤2: 设置网络优先级
# ============================================
Write-Host "[2/4] 设置网络优先级..." -ForegroundColor Yellow
Write-Host ""

# Ethernet - 日常用，优先级最高 (Metric值小 = 优先级高)
Write-Host "设置 Ethernet (日常用) 为最高优先级 (Metric=1)..." -ForegroundColor Cyan
try {
    Set-NetIPInterface -InterfaceIndex $ethernetIndex -InterfaceMetric 1
    Write-Host "✅ Ethernet 优先级已设置为 1 (最高)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Ethernet 优先级设置失败: $_" -ForegroundColor Yellow
}

# Ethernet 4 - 服务器用，优先级次高 (Metric=10)
Write-Host "设置 Ethernet 4 (服务器用) 优先级 (Metric=10)..." -ForegroundColor Cyan
try {
    Set-NetIPInterface -InterfaceIndex $ethernet4Index -InterfaceMetric 10
    Write-Host "✅ Ethernet 4 优先级已设置为 10" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Ethernet 4 优先级设置失败: $_" -ForegroundColor Yellow
}

Write-Host ""

# 显示更新后的配置
Write-Host "更新后的网络接口配置:" -ForegroundColor Cyan
Get-NetIPInterface -AddressFamily IPv4 | Where-Object {$_.ConnectionState -eq 'Connected' -and $_.InterfaceAlias -match 'Ethernet'} | Format-Table InterfaceAlias, InterfaceIndex, InterfaceMetric, ConnectionState -AutoSize

Write-Host ""

# ============================================
# 步骤3: 配置防火墙允许端口访问
# ============================================
Write-Host "[3/4] 配置Windows防火墙..." -ForegroundColor Yellow
Write-Host ""

# 允许MySQL端口3306
Write-Host "配置MySQL端口 3306..." -ForegroundColor Cyan
netsh advfirewall firewall delete rule name="MySQL Port 3306" >$null 2>&1
netsh advfirewall firewall add rule name="MySQL Port 3306" dir=in action=allow protocol=TCP localport=3306 | Out-Null
Write-Host "✅ 防火墙规则已添加: MySQL Port 3306" -ForegroundColor Green

# 允许Backend端口5001
Write-Host "配置Backend端口 5001..." -ForegroundColor Cyan
netsh advfirewall firewall delete rule name="Backend API Port 5001" >$null 2>&1
netsh advfirewall firewall add rule name="Backend API Port 5001" dir=in action=allow protocol=TCP localport=5001 | Out-Null
Write-Host "✅ 防火墙规则已添加: Backend API Port 5001" -ForegroundColor Green

# 允许Frontend端口3000
Write-Host "配置Frontend端口 3000..." -ForegroundColor Cyan
netsh advfirewall firewall delete rule name="Frontend Port 3000" >$null 2>&1
netsh advfirewall firewall add rule name="Frontend Port 3000" dir=in action=allow protocol=TCP localport=3000 | Out-Null
Write-Host "✅ 防火墙规则已添加: Frontend Port 3000" -ForegroundColor Green

Write-Host ""

# ============================================
# 步骤4: 显示配置摘要
# ============================================
Write-Host "[4/4] 配置摘要..." -ForegroundColor Yellow
Write-Host ""

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "✅ 网络配置完成！" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 网络接口配置:" -ForegroundColor Yellow
Write-Host "   Ethernet (日常用):" -ForegroundColor White
Write-Host "     - IP: 192.168.0.6" -ForegroundColor Gray
Write-Host "     - 优先级: 1 (最高)" -ForegroundColor Gray
Write-Host "     - 用途: 日常上网，2000m带宽" -ForegroundColor Gray
Write-Host ""
Write-Host "   Ethernet 4 (服务器用):" -ForegroundColor White
Write-Host "     - IP: 192.168.5.125" -ForegroundColor Gray
Write-Host "     - 公网IP: 61.145.212.28" -ForegroundColor Gray
Write-Host "     - 优先级: 10" -ForegroundColor Gray
Write-Host "     - 用途: 服务器外网访问" -ForegroundColor Gray
Write-Host ""

Write-Host "🔥 防火墙规则:" -ForegroundColor Yellow
Write-Host "   ✅ MySQL Port 3306" -ForegroundColor Green
Write-Host "   ✅ Backend API Port 5001" -ForegroundColor Green
Write-Host "   ✅ Frontend Port 3000" -ForegroundColor Green
Write-Host ""

Write-Host "🌐 外网访问地址:" -ForegroundColor Yellow
Write-Host "   Backend API: http://61.145.212.28:5001" -ForegroundColor Gray
Write-Host "   Frontend: http://61.145.212.28:3000" -ForegroundColor Gray
Write-Host "   MySQL: 61.145.212.28:3306" -ForegroundColor Gray
Write-Host ""

Write-Host "📝 下一步:" -ForegroundColor Yellow
Write-Host "   1. 确保路由器已配置端口映射" -ForegroundColor Gray
Write-Host "   2. Backend需要监听在 0.0.0.0 (所有接口)" -ForegroundColor Gray
Write-Host "   3. MySQL需要配置 bind-address = 0.0.0.0" -ForegroundColor Gray
Write-Host ""

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "按任意键继续..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
