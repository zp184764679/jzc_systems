@echo off
echo ================================================
echo HR System Backend - Starting Server
echo ================================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)
echo.

echo Starting Flask application...
python main.py
