@echo off
chcp 65001 >nul
echo ============================================================
echo MySQL 完全卸载工具
echo ============================================================
echo.

echo ⚠️  警告：此操作将删除所有MySQL数据！
echo ⚠️  如果有重要数据，请先备份！
echo.
echo 按任意键继续卸载，或关闭窗口取消...
pause >nul
echo.

echo [1/6] 停止MySQL服务...
sc stop MySQL90 2>nul
sc stop MySQL80 2>nul
sc stop MySQL 2>nul
timeout /t 3 >nul
echo ✓ 完成
echo.

echo [2/6] 删除MySQL服务...
sc delete MySQL90 2>nul
sc delete MySQL80 2>nul
sc delete MySQL 2>nul
timeout /t 2 >nul
echo ✓ 完成
echo.

echo [3/6] 结束MySQL进程...
taskkill /F /IM mysqld.exe 2>nul
taskkill /F /IM mysql.exe 2>nul
echo ✓ 完成
echo.

echo [4/6] 删除MySQL程序文件...
rd /s /q "C:\Program Files\MySQL" 2>nul
echo ✓ 完成
echo.

echo [5/6] 删除MySQL数据目录...
rd /s /q "C:\ProgramData\MySQL" 2>nul
echo ✓ 完成
echo.

echo [6/6] 清理注册表...
reg delete "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\MySQL90" /f 2>nul
reg delete "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\MySQL80" /f 2>nul
reg delete "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\MySQL" /f 2>nul
echo ✓ 完成
echo.

echo ============================================================
echo ✅ MySQL 已完全卸载！
echo ============================================================
echo.
echo 接下来请重新安装MySQL 8.0
echo 参考文档: 数据库管理\MySQL安装指南.txt
echo.
pause
