@echo off
chcp 65001 >nul
color 0B
echo ====================================================
echo 🌐 配置使用远程数据库
echo ====================================================
echo.
echo 本脚本将配置Backend使用远程MySQL:
echo    主机: 61.145.212.28:3306
echo    数据库: caigou
echo    用户: zhoupeng
echo    密码: exak472008
echo.
echo ====================================================
pause
echo.

cd /d "C:\Users\Admin\Desktop\采购\backend"

echo [1/2] 更新.env配置文件...

powershell -Command "(Get-Content .env) -replace 'SQLALCHEMY_DATABASE_URI=mysql\+pymysql://exzzz:exak472008@localhost:3306/caigou', 'SQLALCHEMY_DATABASE_URI=mysql+pymysql://zhoupeng:exak472008@61.145.212.28:3306/caigou' | Set-Content .env"

powershell -Command "(Get-Content .env) -replace 'DB_HOST=localhost', 'DB_HOST=61.145.212.28' | Set-Content .env"

powershell -Command "(Get-Content .env) -replace 'DB_USER=exzzz', 'DB_USER=zhoupeng' | Set-Content .env"

echo ✅ 配置文件已更新
echo.

echo [2/2] 测试远程数据库连接...
python -c "import pymysql; conn = pymysql.connect(host='61.145.212.28', user='zhoupeng', password='exak472008', database='caigou'); print('✅ 远程数据库连接成功'); conn.close()"

if errorlevel 1 (
    echo ❌ 远程数据库连接失败
    echo.
    echo 可能原因:
    echo 1. 网络连接问题
    echo 2. 远程MySQL未开启外网访问
    echo 3. 用户名或密码不正确
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo ✅ 配置完成！
echo ====================================================
echo.
echo 现在Backend将使用远程数据库
echo 请重启Backend服务
echo.
echo ====================================================
pause
