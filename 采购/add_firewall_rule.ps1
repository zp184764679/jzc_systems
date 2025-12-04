# 添加防火墙规则允许5001端口入站
Write-Host "正在添加防火墙规则..." -ForegroundColor Yellow

# 删除可能存在的旧规则
netsh advfirewall firewall delete rule name="WSL Backend 5001" 2>$null

# 添加新规则
netsh advfirewall firewall add rule name="WSL Backend 5001" dir=in action=allow protocol=TCP localport=5001 profile=any

Write-Host "防火墙规则添加成功!" -ForegroundColor Green
Write-Host "`n现在5001端口应该可以从网络访问了" -ForegroundColor Cyan
