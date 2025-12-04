@echo off
chcp 65001 >nul
color 0B
echo ====================================================
echo 📊 采购系统 - 数据库一键初始化
echo ====================================================
echo.
echo 本脚本将完成:
echo [1] 创建数据库 caigou
echo [2] 创建用户 exzzz (密码: exak472008)
echo [3] 初始化表结构
echo [4] 创建测试用户: 周鹏
echo [5] 创建2个供应商测试数据
echo.
echo ====================================================
pause
echo.

:: 步骤1: 创建数据库和用户
echo [步骤1/3] 创建数据库和用户...
echo.
echo 请输入MySQL root密码:
mysql -u root -p < "%~dp0init_caigou_db.sql"

if errorlevel 1 (
    echo.
    echo ❌ 数据库创建失败
    echo.
    echo 请确认:
    echo 1. MySQL服务是否在运行
    echo 2. root密码是否正确
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ 数据库和用户创建成功
echo.
timeout /t 2 >nul

:: 步骤2: 初始化表结构
echo [步骤2/3] 初始化表结构...
echo.

cd /d "C:\Users\Admin\Desktop\采购\backend"
python -c "from app import db, app; app.app_context().push(); db.create_all(); print('✅ 表结构创建成功')"

if errorlevel 1 (
    echo.
    echo ❌ 表结构创建失败
    echo.
    pause
    exit /b 1
)

echo.
timeout /t 2 >nul

:: 步骤3: 创建测试数据
echo [步骤3/3] 创建测试数据...
echo.

cd /d "%~dp0"
python create_test_data.py

if errorlevel 1 (
    echo.
    echo ⚠️  测试数据创建失败（可手动重试）
    echo.
)

echo.
echo ====================================================
echo ✅ 初始化完成！
echo ====================================================
echo.
echo 📊 数据库配置:
echo    数据库: caigou
echo    用户: exzzz
echo    密码: exak472008
echo.
echo 👤 测试账号:
echo    用户: 周鹏
echo    邮箱: jzchardware@gmail.com
echo    电话: 13590217332
echo.
echo 🏭 测试供应商:
echo    供应商1: 深圳市XX电子有限公司
echo    供应商2: 广州YY科技有限公司
echo.
echo 现在可以重启Backend服务并测试登录了！
echo ====================================================
pause
