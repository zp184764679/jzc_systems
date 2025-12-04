# ============================================================
# 将WSL守护进程注册为Windows系统服务
# 需要管理员权限运行
# ============================================================

# 检查管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ 此脚本需要管理员权限运行" -ForegroundColor Red
    Write-Host "请右键选择'以管理员身份运行'" -ForegroundColor Yellow
    pause
    exit 1
}

$SERVICE_NAME = "WSLCaigouGuardian"
$DISPLAY_NAME = "WSL采购系统守护服务"
$DESCRIPTION = "监控并自动重启WSL采购系统进程"
$SCRIPT_PATH = "C:\Users\Admin\Desktop\采购\运维工具\WSL进程守护者.ps1"
$NSSM_PATH = "C:\Users\Admin\Desktop\采购\运维工具\nssm.exe"

Write-Host "======================================"
Write-Host "  注册Windows系统服务"
Write-Host "======================================"
Write-Host ""

# 检查服务是否已存在
$existingService = Get-Service -Name $SERVICE_NAME -ErrorAction SilentlyContinue

if ($existingService) {
    Write-Host "服务已存在，正在卸载..." -ForegroundColor Yellow
    Stop-Service -Name $SERVICE_NAME -Force -ErrorAction SilentlyContinue
    sc.exe delete $SERVICE_NAME
    Start-Sleep -Seconds 2
}

# 检查NSSM工具
if (-not (Test-Path $NSSM_PATH)) {
    Write-Host "⚠️  未找到NSSM工具，正在下载..." -ForegroundColor Yellow
    Write-Host "NSSM (Non-Sucking Service Manager) 用于将脚本注册为系统服务"
    Write-Host ""

    # 下载NSSM
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $nssmZip = "$env:TEMP\nssm.zip"
    $nssmExtract = "$env:TEMP\nssm"

    try {
        Write-Host "正在下载NSSM..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip -UseBasicParsing

        Write-Host "正在解压..." -ForegroundColor Cyan
        Expand-Archive -Path $nssmZip -DestinationPath $nssmExtract -Force

        # 复制对应架构的NSSM
        $arch = if ([Environment]::Is64BitOperatingSystem) { "win64" } else { "win32" }
        Copy-Item "$nssmExtract\nssm-2.24\$arch\nssm.exe" -Destination $NSSM_PATH

        Write-Host "✅ NSSM下载完成" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ 下载失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "请手动下载NSSM并放置在：$NSSM_PATH" -ForegroundColor Yellow
        Write-Host "下载地址：https://nssm.cc/download" -ForegroundColor Yellow
        pause
        exit 1
    }
}

Write-Host "正在注册服务..." -ForegroundColor Cyan

# 使用NSSM注册服务
& $NSSM_PATH install $SERVICE_NAME powershell.exe "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File `"$SCRIPT_PATH`""

# 配置服务
& $NSSM_PATH set $SERVICE_NAME DisplayName $DISPLAY_NAME
& $NSSM_PATH set $SERVICE_NAME Description $DESCRIPTION
& $NSSM_PATH set $SERVICE_NAME Start SERVICE_AUTO_START
& $NSSM_PATH set $SERVICE_NAME AppStdout "C:\Users\Admin\Desktop\采购\运维工具\服务日志.txt"
& $NSSM_PATH set $SERVICE_NAME AppStderr "C:\Users\Admin\Desktop\采购\运维工具\服务错误日志.txt"
& $NSSM_PATH set $SERVICE_NAME AppRotateFiles 1
& $NSSM_PATH set $SERVICE_NAME AppRotateBytes 1048576  # 1MB

Write-Host ""
Write-Host "✅ 服务注册完成！" -ForegroundColor Green
Write-Host ""
Write-Host "服务信息：" -ForegroundColor Cyan
Write-Host "  服务名称：$SERVICE_NAME"
Write-Host "  显示名称：$DISPLAY_NAME"
Write-Host "  启动类型：自动"
Write-Host ""

# 启动服务
Write-Host "正在启动服务..." -ForegroundColor Cyan
Start-Service -Name $SERVICE_NAME

Start-Sleep -Seconds 2

$service = Get-Service -Name $SERVICE_NAME
if ($service.Status -eq "Running") {
    Write-Host "✅ 服务已启动并运行中！" -ForegroundColor Green
}
else {
    Write-Host "⚠️  服务启动失败，状态：$($service.Status)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================"
Write-Host "  管理命令"
Write-Host "======================================"
Write-Host "查看服务状态：Get-Service $SERVICE_NAME"
Write-Host "停止服务：Stop-Service $SERVICE_NAME"
Write-Host "启动服务：Start-Service $SERVICE_NAME"
Write-Host "卸载服务：$NSSM_PATH remove $SERVICE_NAME confirm"
Write-Host ""
Write-Host "或在Windows服务管理器(services.msc)中管理"
Write-Host ""

pause
