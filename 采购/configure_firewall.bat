@echo off
echo ============================================================
echo 配置Windows防火墙，允许端口3000和5001
echo ============================================================
echo.

echo [1/2] 添加端口3000防火墙规则...
netsh advfirewall firewall add rule name="Frontend Port 3000" dir=in action=allow protocol=TCP localport=3000
if %errorlevel% == 0 (
    echo ✅ 端口3000防火墙规则添加成功
) else (
    echo ❌ 端口3000防火墙规则添加失败
)
echo.

echo [2/2] 添加端口5001防火墙规则...
netsh advfirewall firewall add rule name="Backend Port 5001" dir=in action=allow protocol=TCP localport=5001
if %errorlevel% == 0 (
    echo ✅ 端口5001防火墙规则添加成功
) else (
    echo ❌ 端口5001防火墙规则添加失败
)
echo.

echo ============================================================
echo 配置完成！
echo.
echo 当前防火墙规则：
netsh advfirewall firewall show rule name="Frontend Port 3000"
echo.
netsh advfirewall firewall show rule name="Backend Port 5001"
echo ============================================================
pause
