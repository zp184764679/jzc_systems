# PowerShell脚本: 修改MySQL配置允许外网访问
# 需要管理员权限运行

$myIniPath = "C:\ProgramData\MySQL\MySQL Server 9.0\my.ini"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "🔧 修改MySQL配置文件允许外网访问" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# 检查文件是否存在
if (-not (Test-Path $myIniPath)) {
    Write-Host "❌ 未找到MySQL配置文件: $myIniPath" -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] 备份当前配置文件..." -ForegroundColor Yellow
$backupPath = "$myIniPath.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item $myIniPath $backupPath -Force
Write-Host "✅ 已备份到: $backupPath" -ForegroundColor Green
Write-Host ""

Write-Host "[2/3] 检查是否已配置bind-address..." -ForegroundColor Yellow
$content = Get-Content $myIniPath -Raw

if ($content -match "bind-address\s*=") {
    Write-Host "⚠️  已存在bind-address配置，将进行更新" -ForegroundColor Yellow
    # 更新现有配置
    $content = $content -replace "bind-address\s*=\s*[\d\.]+", "bind-address = 0.0.0.0"
} else {
    Write-Host "📝 添加新的bind-address配置" -ForegroundColor Yellow
    # 在port=3306后面添加配置
    $content = $content -replace "(port=3306)", "`$1`r`n`r`n# Allow connections from any IP address (0.0.0.0 = all interfaces)`r`nbind-address = 0.0.0.0`r`nmysqlx-bind-address = 0.0.0.0"
}

# 同样处理mysqlx-bind-address
if ($content -match "mysqlx-bind-address\s*=") {
    $content = $content -replace "mysqlx-bind-address\s*=\s*[\d\.]+", "mysqlx-bind-address = 0.0.0.0"
} elseif ($content -notmatch "mysqlx-bind-address") {
    # 如果没有mysqlx配置,在bind-address后面添加
    $content = $content -replace "(bind-address = 0\.0\.0\.0)", "`$1`r`nmysqlx-bind-address = 0.0.0.0"
}

Write-Host "✅ 配置内容已准备完成" -ForegroundColor Green
Write-Host ""

Write-Host "[3/3] 写入配置文件..." -ForegroundColor Yellow
try {
    Set-Content -Path $myIniPath -Value $content -Force -Encoding UTF8
    Write-Host "✅ 配置文件修改成功！" -ForegroundColor Green
} catch {
    Write-Host "❌ 写入失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "✅ MySQL配置修改完成！" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 已添加配置:" -ForegroundColor Yellow
Write-Host "   bind-address = 0.0.0.0" -ForegroundColor White
Write-Host "   mysqlx-bind-address = 0.0.0.0" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  重要: 需要重启MySQL服务才能生效！" -ForegroundColor Yellow
Write-Host ""
Write-Host "按任意键继续..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
