@echo off
chcp 65001 >nul
echo ============================================================
echo MySQL 安装验证工具
echo ============================================================
echo.

echo [1/5] 检查MySQL服务（MySQL80）...
sc query MySQL80 2>nul
if %errorlevel% == 0 (
    echo ✅ MySQL80 服务存在
) else (
    echo ⚠️  MySQL80 服务不存在，尝试MySQL90...
    sc query MySQL90 2>nul
    if %errorlevel% == 0 (
        echo ✅ MySQL90 服务存在
    ) else (
        echo ❌ 未找到MySQL服务！请重新安装
        pause
        exit
    )
)
echo.

echo [2/5] 检查3306端口...
netstat -ano | findstr :3306 2>nul
if %errorlevel% == 0 (
    echo ✅ MySQL正在监听3306端口
) else (
    echo ⚠️  3306端口未监听，MySQL可能未启动
)
echo.

echo [3/5] 检查MySQL命令...
where mysql 2>nul
if %errorlevel% == 0 (
    echo ✅ MySQL命令可用
) else (
    echo ⚠️  MySQL命令不在PATH中
)
echo.

echo [4/5] 尝试连接MySQL（root/exak472008）...
mysql -u root -pexak472008 -e "SELECT VERSION();" 2>nul
if %errorlevel% == 0 (
    echo ✅ MySQL连接成功！
) else (
    echo ❌ 连接失败，请检查密码或MySQL服务状态
)
echo.

echo [5/5] 检查caigou数据库...
mysql -u root -pexak472008 -e "SHOW DATABASES LIKE 'caigou';" 2>nul | findstr caigou >nul
if %errorlevel% == 0 (
    echo ✅ caigou数据库已存在
) else (
    echo ⚠️  caigou数据库不存在，需要初始化
)
echo.

echo ============================================================
echo 验证完成！
echo ============================================================
echo.
echo 如果MySQL连接成功，请运行：3_初始化数据库.bat
echo 如果连接失败，请检查MySQL服务和密码
echo.
pause
