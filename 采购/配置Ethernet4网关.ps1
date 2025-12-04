# 配置Ethernet 4网关
# 请以管理员身份运行

Write-Host "正在配置Ethernet 4网关..." -ForegroundColor Green

# 配置Ethernet 4的网关为192.168.5.1
netsh interface ipv4 set address name="Ethernet 4" source=static addr=192.168.5.125 mask=255.255.255.0 gateway=192.168.5.1

Write-Host ""
Write-Host "配置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "验证配置:" -ForegroundColor Yellow
netsh interface ipv4 show config name="Ethernet 4"

Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
