@echo off
echo ================================================
echo HR System Backend - Installation Script
echo ================================================
echo.

echo Step 1: Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created successfully!
echo.

echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated!
echo.

echo Step 3: Upgrading pip...
python -m pip install --upgrade pip
echo.

echo Step 4: Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

echo ================================================
echo Installation completed successfully!
echo ================================================
echo.
echo Next steps:
echo 1. Make sure MySQL is running
echo 2. Create database: CREATE DATABASE cncplan;
echo 3. Update .env file with your database credentials
echo 4. Run the application: python main.py
echo.
pause
