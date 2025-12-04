@echo off
chcp 65001 >nul
echo ====================================================
echo 🔧 更新Backend配置连接本地MySQL
echo ====================================================
echo.

cd /d "%~dp0..\backend"

echo [1/3] 备份当前.env文件...
if exist .env (
    copy /y .env .env.backup.%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
    echo ✅ 已备份到 .env.backup.*
) else (
    echo ⚠️  .env文件不存在，将创建新文件
)
echo.

echo [2/3] 生成新的.env配置...
(
echo # ==========================================
echo # 采购系统Backend配置文件
echo # 环境: Windows本机开发 + Ubuntu部署
echo # ==========================================
echo.
echo # ========== MySQL数据库配置 ==========
echo # 本地开发（Windows）
echo DB_HOST=localhost
echo DB_PORT=3306
echo DB_USER=caigou_admin
echo DB_PASSWORD=caigou2025!@#
echo DB_NAME=caigou_local
echo.
echo # Ubuntu部署时修改为:
echo # DB_HOST=192.168.0.6  ^(Windows的局域网IP^)
echo.
echo # ========== Flask应用配置 ==========
echo FLASK_APP=app.py
echo FLASK_ENV=development
echo FLASK_DEBUG=True
echo SECRET_KEY=dev-secret-key-change-in-production
echo.
echo # ========== JWT配置 ==========
echo JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
echo JWT_ACCESS_TOKEN_EXPIRES=86400
echo.
echo # ========== 文件上传配置 ==========
echo UPLOAD_FOLDER=uploads
echo MAX_CONTENT_LENGTH=16777216
echo.
echo # ========== 企业微信配置 ==========
echo WEWORK_CORP_ID=ww7f7bb9e8fc040434
echo WEWORK_AGENT_ID=1000010
echo WEWORK_SECRET=g_N-OEw3TsrBYyv07exCaUzCT56dCzvjN1G8TW1_NHM
echo.
echo # ========== Celery配置 ==========
echo CELERY_BROKER_URL=redis://localhost:6379/0
echo CELERY_RESULT_BACKEND=redis://localhost:6379/0
echo.
echo # ========== OCR配置 ==========
echo USE_BAIDU_OCR=false
echo # BAIDU_OCR_APP_ID=
echo # BAIDU_OCR_API_KEY=
echo # BAIDU_OCR_SECRET_KEY=
echo.
echo # ========== 日志配置 ==========
echo LOG_LEVEL=INFO
echo LOG_FILE=logs/app.log
) > .env

echo ✅ 新配置文件已生成
echo.

echo [3/3] 显示当前配置...
type .env | findstr /V "PASSWORD SECRET"
echo    ^(敏感信息已隐藏^)
echo.

echo ====================================================
echo ✅ Backend配置更新完成！
echo ====================================================
echo.
echo 📝 配置文件位置: %CD%\.env
echo.
echo 🔍 关键配置:
echo    数据库: caigou_local@localhost:3306
echo    用户: caigou_admin
echo.
echo 下一步: 运行 "3_测试数据库连接.bat"
echo ====================================================
pause
