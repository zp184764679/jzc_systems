@echo off
chcp 65001 >nul
echo ========================================
echo 📊 采购系统健康检查
echo ========================================
echo.

echo 🔍 检查核心服务状态...
echo.

REM MySQL
echo [1/5] MySQL数据库...
sc query MySQL90 | find "RUNNING" >nul
if %errorlevel%==0 (
    echo     ✅ MySQL90 运行中
) else (
    sc query MySQL80 | find "RUNNING" >nul
    if %errorlevel%==0 (
        echo     ✅ MySQL80 运行中
    ) else (
        echo     ❌ MySQL 未运行
    )
)

REM Redis
echo [2/5] Redis缓存...
tasklist | findstr /i "redis-server" >nul
if %errorlevel%==0 (
    echo     ✅ Redis 运行中
) else (
    echo     ❌ Redis 未运行
)

REM Backend
echo [3/5] Flask后端...
netstat -ano | findstr ":5001.*LISTENING" >nul
if %errorlevel%==0 (
    echo     ✅ Backend 运行中 (端口5001)
) else (
    echo     ❌ Backend 未运行
)

REM Celery
echo [4/5] Celery任务队列...
tasklist | findstr /i "python" | findstr /i "celery" >nul
if %errorlevel%==0 (
    echo     ✅ Celery 运行中
) else (
    echo     ❌ Celery 未运行 - 异步任务将无法工作
)

REM Frontend
echo [5/5] React前端...
netstat -ano | findstr ":3000.*LISTENING" >nul
if %errorlevel%==0 (
    echo     ✅ Frontend 运行中 (端口3000)
) else (
    echo     ❌ Frontend 未运行
)

echo.
echo ========================================
echo 🔧 检查Python环境...
echo ========================================
echo.

cd /d "C:\Users\Admin\Desktop\采购\backend"

echo [1/3] PaddlePaddle...
python -c "import paddle; print('    ✅ PaddlePaddle 已安装')" 2>nul
if %errorlevel% NEQ 0 (
    echo     ❌ PaddlePaddle 未安装
)

echo [2/3] PaddleOCR...
python -c "import paddleocr; print('    ✅ PaddleOCR 已安装')" 2>nul
if %errorlevel% NEQ 0 (
    echo     ❌ PaddleOCR 未安装
)

echo [3/3] Celery...
python -c "import celery; print('    ✅ Celery 已安装')" 2>nul
if %errorlevel% NEQ 0 (
    echo     ❌ Celery 未安装
)

echo.
echo ========================================
echo 📝 功能状态
echo ========================================
echo.

REM 检查Celery是否运行来判断异步功能
tasklist | findstr /i "python" | findstr /i "celery" >nul
if %errorlevel%==0 (
    echo ✅ RFQ异步发送: 可用
    echo ✅ AI分类异步处理: 可用
) else (
    echo ❌ RFQ异步发送: 不可用 - 需要启动Celery
    echo ❌ AI分类异步处理: 不可用 - 需要启动Celery
)

REM 检查OCR
python -c "import paddleocr" 2>nul
if %errorlevel%==0 (
    echo ✅ 发票OCR识别: 可用 (需要下载模型)
) else (
    echo ⚠️  发票OCR识别: 不可用 - 可手动输入发票信息
)

echo.
echo ========================================
echo 💡 快速操作指南
echo ========================================
echo.
echo 启动所有服务:    双击 "启动采购系统.bat"
echo 启动Celery:      双击 "手动启动Celery.bat"
echo 清理所有进程:    双击 "清理所有进程.bat"
echo.

pause
