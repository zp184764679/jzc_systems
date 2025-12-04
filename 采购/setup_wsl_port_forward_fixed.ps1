# WSL端口转发配置脚本
# 以管理员身份运行

Write-Host "配置WSL端口转发..." -ForegroundColor Green

# 获取WSL IP地址
$wslIP = wsl -d Ubuntu-22.04 -- bash -c "ip addr show eth0 | grep 'inet ' | awk '{print `$2}' | cut -d/ -f1"
Write-Host "WSL IP: $wslIP" -ForegroundColor Yellow

# 删除旧的端口转发规则
Write-Host "`n删除旧规则..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=5001 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0 2>$null

# 添加新的端口转发规则
Write-Host "添加新规则..." -ForegroundColor Yellow
netsh interface portproxy add v4tov4 listenport=5001 listenaddress=0.0.0.0 connectport=5001 connectaddress=$wslIP
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=$wslIP

# 显示配置
Write-Host "`n当前端口转发配置:" -ForegroundColor Green
netsh interface portproxy show all

# 配置防火墙规则
Write-Host "`n配置防火墙规则..." -ForegroundColor Yellow
netsh advfirewall firewall delete rule name="WSL Backend API 5001" 2>$null
netsh advfirewall firewall delete rule name="WSL Frontend 3000" 2>$null

netsh advfirewall firewall add rule name="WSL Backend API 5001" dir=in action=allow protocol=TCP localport=5001
netsh advfirewall firewall add rule name="WSL Frontend 3000" dir=in action=allow protocol=TCP localport=3000

Write-Host "`n✅ 配置完成!" -ForegroundColor Green
Write-Host "`n访问地址:" -ForegroundColor Cyan
Write-Host "  本地:     http://localhost:5001" -ForegroundColor White
Write-Host "  内网:     http://192.168.5.125:5001" -ForegroundColor White
Write-Host "  公网:     http://61.145.212.28:5001" -ForegroundColor White

Write-Host "`n按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
