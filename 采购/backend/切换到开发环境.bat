@echo off
chcp 65001 >nul
echo ============================================================
echo 切换到开发环境配置
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/2] 备份当前.env文件...
if exist .env (
    copy /Y .env .env.backup >nul
    echo ✅ 已备份到 .env.backup
) else (
    echo ⚠️  当前没有.env文件
)
echo.

echo [2/2] 应用开发环境配置...
copy /Y .env.development .env >nul
echo ✅ 已切换到开发环境
echo.

echo ============================================================
echo ✅ 开发环境配置已生效
echo ============================================================
echo.
echo 📝 当前配置：
echo    • 环境：Windows本地开发
echo    • 数据库：localhost:3306
echo    • Backend：localhost:5001
echo    • Frontend：localhost:3000
echo    • Redis：localhost:6379
echo    • 企业微信：本地测试模式
echo.
echo 💡 现在可以启动开发服务器：
echo    运行: ..\运维工具\启动采购系统.bat
echo.
pause
