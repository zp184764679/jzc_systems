# WSL端口转发配置脚本
# 请右键此文件，选择"以管理员身份运行PowerShell"

Write-Host "正在配置WSL端口转发..." -ForegroundColor Green

# 获取WSL IP地址
$wslIp = (wsl -d Ubuntu-22.04 -- bash -c "ip addr show eth0 | grep 'inet ' | awk '{print `$2}' | cut -d/ -f1")
Write-Host "WSL IP地址: $wslIp" -ForegroundColor Yellow

# 删除旧的端口转发规则
Write-Host "清理旧规则..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=5000 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=5001 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0 2>$null

# 添加新的端口转发规则
Write-Host "配置端口转发..." -ForegroundColor Yellow
netsh interface portproxy add v4tov4 listenport=5001 listenaddress=0.0.0.0 connectport=5001 connectaddress=$wslIp
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=$wslIp

# 配置防火墙规则
Write-Host "配置防火墙规则..." -ForegroundColor Yellow
netsh advfirewall firewall delete rule name="WSL Backend API 5001" 2>$null
netsh advfirewall firewall delete rule name="WSL Frontend 3000" 2>$null

netsh advfirewall firewall add rule name="WSL Backend API 5001" dir=in action=allow protocol=TCP localport=5001
netsh advfirewall firewall add rule name="WSL Frontend 3000" dir=in action=allow protocol=TCP localport=3000

# 显示配置结果
Write-Host ""
Write-Host "端口转发配置完成:" -ForegroundColor Green
netsh interface portproxy show all

Write-Host ""
Write-Host "测试连接..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5001/api/health" -TimeoutSec 3
    Write-Host "后端API测试成功!" -ForegroundColor Green
    Write-Host $response.Content
} catch {
    Write-Host "后端API测试失败: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "配置完成！现在可以通过以下地址访问:" -ForegroundColor Green
Write-Host "  内网访问: http://192.168.5.125:5001" -ForegroundColor Cyan
Write-Host "  公网访问: http://61.145.212.28:5001" -ForegroundColor Cyan
Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
