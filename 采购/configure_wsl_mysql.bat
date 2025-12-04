@echo off
echo ============================================================
echo 配置WSL到Windows MySQL连接
echo ============================================================
echo.

echo [1/3] 配置Windows防火墙，允许MySQL端口3306...
netsh advfirewall firewall add rule name="MySQL for WSL" dir=in action=allow protocol=TCP localport=3306
if %errorlevel% == 0 (
    echo ✅ 防火墙规则添加成功
) else (
    echo ❌ 防火墙规则添加失败
)
echo.

echo [2/3] 删除端口代理规则（将请求从WSL重定向回Windows）...
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0
netsh interface portproxy delete v4tov4 listenport=5001 listenaddress=0.0.0.0
if %errorlevel% == 0 (
    echo ✅ 端口代理规则删除成功
) else (
    echo ❌ 端口代理规则删除失败
)
echo.

echo [3/3] 验证端口代理状态...
netsh interface portproxy show all
echo.

echo ============================================================
echo 配置完成！
echo.
echo 接下来需要：
echo 1. 修改WSL backend配置文件，将数据库地址改为172.22.32.1
echo 2. 重启WSL backend服务
echo.
echo 注意：从WSL访问Windows主机，使用IP地址 172.22.32.1
echo ============================================================
pause
