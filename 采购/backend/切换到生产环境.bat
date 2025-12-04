@echo off
chcp 65001 >nul
echo ============================================================
echo 切换到生产环境配置
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

echo [2/2] 应用生产环境配置...
copy /Y .env.production .env >nul
echo ✅ 已切换到生产环境
echo.

echo ============================================================
echo ✅ 生产环境配置已生效
echo ============================================================
echo.
echo 📝 当前配置：
echo    • 环境：WSL/Linux生产环境
echo    • 数据库：localhost:3306 (共用)
echo    • Backend：61.145.212.28:5001
echo    • Frontend：61.145.212.28:3000
echo    • 企业微信：公网服务器模式
echo.
echo ⚠️  注意：
echo    生产环境应该在WSL中部署，而不是在Windows中运行
echo    请参考: 运维工具\生产部署\WSL部署指南.md
echo.
pause
