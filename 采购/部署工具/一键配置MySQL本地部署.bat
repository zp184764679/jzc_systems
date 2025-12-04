@echo off
chcp 65001 >nul
echo ====================================================
echo 🚀 一键配置MySQL本地部署环境
echo ====================================================
echo.
echo 本脚本将自动完成以下操作:
echo [1] 修改MySQL配置允许外网访问
echo [2] 创建数据库和用户
echo [3] 配置Windows防火墙
echo [4] 重启MySQL服务
echo [5] 更新Backend配置
echo [6] 测试数据库连接
echo.
echo ====================================================
pause
echo.

:: ============================================
:: 步骤1: 修改MySQL配置(需要管理员权限)
:: ============================================
echo.
echo [步骤1/6] 修改MySQL配置文件...
echo.
echo ⚠️  需要管理员权限修改 my.ini 文件
echo 即将打开管理员权限窗口...
echo.
echo 请在管理员窗口中按任意键继续,完成后关闭窗口...
echo.

:: 使用PowerShell以管理员身份运行配置脚本
PowerShell -Command "Start-Process PowerShell -ArgumentList '-ExecutionPolicy Bypass -File \"\"%~dp0修改MySQL配置.ps1\"\"' -Verb RunAs -Wait"

echo.
echo ✅ MySQL配置文件已更新
echo.

:: ============================================
:: 步骤2: 重启MySQL服务
:: ============================================
echo [步骤2/6] 重启MySQL服务使配置生效...
net stop MySQL90 2>nul
timeout /t 2 >nul
net start MySQL90
if errorlevel 1 (
    echo ❌ MySQL服务启动失败
    pause
    exit /b 1
)
timeout /t 3 >nul
echo ✅ MySQL服务已重启
echo.

:: ============================================
:: 步骤3: 创建数据库和用户
:: ============================================
echo [步骤3/6] 创建数据库和用户...
echo.
echo 请输入MySQL root密码:
mysql -u root -p < "%~dp0setup_mysql_local.sql"
if errorlevel 1 (
    echo ❌ 数据库初始化失败
    pause
    exit /b 1
)
echo.
echo ✅ 数据库和用户创建成功
echo.

:: ============================================
:: 步骤4: 配置Windows防火墙
:: ============================================
echo [步骤4/6] 配置Windows防火墙...
netsh advfirewall firewall delete rule name="MySQL Port 3306" >nul 2>&1
netsh advfirewall firewall add rule name="MySQL Port 3306" dir=in action=allow protocol=TCP localport=3306 >nul
if errorlevel 1 (
    echo ⚠️  防火墙配置可能需要管理员权限
) else (
    echo ✅ 防火墙规则已添加
)
echo.

:: ============================================
:: 步骤5: 更新Backend配置
:: ============================================
echo [步骤5/6] 更新Backend配置文件...
cd /d "%~dp0..\backend"

if exist .env (
    copy /y .env .env.backup.%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2% >nul
    echo ✅ 已备份原配置文件
)

(
echo # ==========================================
echo # 采购系统Backend配置文件
echo # 环境: Windows本机开发 + Ubuntu部署
echo # ==========================================
echo.
echo # ========== MySQL数据库配置 ==========
echo DB_HOST=localhost
echo DB_PORT=3306
echo DB_USER=caigou_admin
echo DB_PASSWORD=caigou2025!@#
echo DB_NAME=caigou_local
echo.
echo # Ubuntu部署时修改为: DB_HOST=192.168.0.6
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
echo.
echo # ========== 日志配置 ==========
echo LOG_LEVEL=INFO
echo LOG_FILE=logs/app.log
) > .env

echo ✅ Backend配置已更新
echo.

:: ============================================
:: 步骤6: 测试数据库连接
:: ============================================
echo [步骤6/6] 测试数据库连接...
echo.
cd /d "%~dp0"
python test_mysql_connection.py
if errorlevel 1 (
    echo.
    echo ❌ 数据库连接测试失败
    echo.
    pause
    exit /b 1
)

:: ============================================
:: 完成
:: ============================================
echo.
echo ====================================================
echo ✅ 所有配置完成！
echo ====================================================
echo.
echo 📊 数据库信息:
echo    数据库: caigou_local@localhost:3306
echo    用户: caigou_admin
echo    密码: caigou2025!@#
echo.
echo 🌐 可访问IP:
echo    本地: localhost / 127.0.0.1
echo    局域网: 192.168.0.6
echo    外网: 61.145.212.28 (需路由器端口映射)
echo.
echo 📝 Backend配置文件: %~dp0..\backend\.env
echo.
echo ====================================================
pause
