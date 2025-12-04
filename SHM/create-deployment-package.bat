@echo off
REM 创建SHM部署包脚本
REM 打包出货管理系统的核心文件用于部署

echo ======================================
echo   创建 SHM 部署包
echo ======================================
echo.

set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set PACKAGE_NAME=SHM-Deployment-%TIMESTAMP%

echo 包名: %PACKAGE_NAME%
echo.

REM 创建临时目录
if exist %PACKAGE_NAME% rmdir /s /q %PACKAGE_NAME%
mkdir %PACKAGE_NAME%

echo [1/6] 复制前端构建文件...
mkdir %PACKAGE_NAME%\frontend
xcopy /E /I /Y frontend\dist %PACKAGE_NAME%\frontend\dist
echo.

echo [2/6] 复制后端代码...
mkdir %PACKAGE_NAME%\backend
copy /Y backend\app.py %PACKAGE_NAME%\backend\
copy /Y backend\config.py %PACKAGE_NAME%\backend\
copy /Y backend\extensions.py %PACKAGE_NAME%\backend\
copy /Y backend\requirements.txt %PACKAGE_NAME%\backend\
copy /Y backend\.env %PACKAGE_NAME%\backend\

mkdir %PACKAGE_NAME%\backend\models
xcopy /E /I /Y backend\models %PACKAGE_NAME%\backend\models

mkdir %PACKAGE_NAME%\backend\routes
xcopy /E /I /Y backend\routes %PACKAGE_NAME%\backend\routes

mkdir %PACKAGE_NAME%\backend\services
xcopy /E /I /Y backend\services %PACKAGE_NAME%\backend\services
echo.

echo [3/6] 复制部署脚本...
copy /Y deploy.sh %PACKAGE_NAME%\
copy /Y deploy.bat %PACKAGE_NAME%\
echo.

echo [4/6] 复制文档...
copy /Y DEPLOYMENT_GUIDE.md %PACKAGE_NAME%\
copy /Y README_DEPLOYMENT.md %PACKAGE_NAME%\
copy /Y MYSQL_SETUP.md %PACKAGE_NAME%\
copy /Y UPGRADE_TO_V6.md %PACKAGE_NAME%\
copy /Y 部署摘要.md %PACKAGE_NAME%\
echo.

echo [5/6] 创建README...
echo SHM 出货管理系统 - 部署包 > %PACKAGE_NAME%\README.txt
echo. >> %PACKAGE_NAME%\README.txt
echo 版本: 2.0 (React 19 + Antd 6) >> %PACKAGE_NAME%\README.txt
echo 创建时间: %date% %time% >> %PACKAGE_NAME%\README.txt
echo. >> %PACKAGE_NAME%\README.txt
echo 快速开始: >> %PACKAGE_NAME%\README.txt
echo   Windows: 运行 deploy.bat >> %PACKAGE_NAME%\README.txt
echo   Linux/Mac: 运行 deploy.sh >> %PACKAGE_NAME%\README.txt
echo. >> %PACKAGE_NAME%\README.txt
echo 详细文档: 查看 DEPLOYMENT_GUIDE.md >> %PACKAGE_NAME%\README.txt
echo.

echo [6/6] 创建压缩包...
powershell -Command "Compress-Archive -Path '%PACKAGE_NAME%\*' -DestinationPath '%PACKAGE_NAME%.zip' -Force"

if exist %PACKAGE_NAME%.zip (
    echo.
    echo ======================================
    echo   部署包创建成功！
    echo ======================================
    echo.
    echo 文件: %PACKAGE_NAME%.zip
    echo.

    REM 显示文件大小
    for %%A in (%PACKAGE_NAME%.zip) do (
        set size=%%~zA
    )
    echo 大小: %size% 字节
    echo.

    echo 包含内容:
    echo   - frontend/dist/        ^(前端构建文件 - React 19 + Antd 6^)
    echo   - backend/              ^(后端代码 - Flask + MySQL^)
    echo   - deploy.sh/.bat        ^(自动部署脚本^)
    echo   - *.md                  ^(部署文档 + MySQL配置指南^)
    echo.
    echo 技术栈:
    echo   - React 19.0 + Ant Design 6.0
    echo   - Flask + MySQL ^(生产数据库^)
    echo   - JWT SSO认证
    echo.
    echo 重要提示:
    echo   - 部署前必须先创建MySQL数据库
    echo   - 详见 MYSQL_SETUP.md
    echo.
    echo 下一步:
    echo   1. 上传 %PACKAGE_NAME%.zip 到服务器
    echo   2. 解压文件
    echo   3. 运行 deploy.sh 或 deploy.bat
    echo   4. 访问 http://localhost:7500
    echo.

    REM 清理临时目录
    rmdir /s /q %PACKAGE_NAME%
) else (
    echo.
    echo 错误: 压缩包创建失败
    echo.
)

pause
