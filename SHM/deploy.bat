@echo off
REM SHM 出货管理系统部署脚本 (Windows)
REM 使用方法: deploy.bat

echo ======================================
echo   SHM 出货管理系统部署脚本
echo ======================================
echo.

REM 检查Node.js
echo [1/7] 检查Node.js环境...
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)
node --version
echo.

REM 检查Python
echo [2/7] 检查Python环境...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)
python --version
echo.

REM 检查PM2
echo [3/7] 检查PM2...
where pm2 >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 未找到PM2，正在安装...
    npm install -g pm2
)
echo PM2已安装
echo.

REM 安装serve
echo [4/7] 安装serve工具...
where serve >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    npm install -g serve
)
echo serve已安装
echo.

REM 设置后端Python虚拟环境
echo [5/7] 配置Python虚拟环境...
cd backend
if not exist venv (
    python -m venv venv
    echo 虚拟环境已创建
) else (
    echo 虚拟环境已存在
)

REM 激活虚拟环境并安装依赖
echo   安装Python依赖...
call venv\Scripts\activate.bat
pip install -r requirements.txt
call deactivate
cd ..
echo Python依赖已安装
echo.

REM 配置PM2服务
echo [6/7] 配置PM2服务...

REM 停止旧服务（如果存在）
pm2 delete shm-frontend 2>nul
pm2 delete shm-backend 2>nul

REM 启动前端服务
echo   启动前端服务 (端口 7500)...
cd frontend
pm2 start serve --name shm-frontend -- -s dist -l 7500
cd ..
echo 前端服务已启动

REM 启动后端服务
echo   启动后端服务 (端口 8006)...
pm2 start backend\app.py --name shm-backend --interpreter backend\venv\Scripts\python.exe
echo 后端服务已启动
echo.

REM 保存PM2配置
echo [7/7] 保存PM2配置...
pm2 save
echo PM2配置已保存
echo.

REM 显示服务状态
echo ======================================
echo   部署完成！
echo ======================================
echo.
pm2 list

echo.
echo 访问地址:
echo   前端: http://localhost:7500
echo   后端: http://localhost:8006
echo.
echo 常用命令:
echo   查看状态: pm2 list
echo   查看日志: pm2 logs shm-frontend
echo            pm2 logs shm-backend
echo   重启服务: pm2 restart shm-frontend
echo            pm2 restart shm-backend
echo.
pause
