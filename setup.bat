@echo off
echo ============================================
echo   Fake Profile Detection - Backend Setup
echo ============================================
echo.

:: Check Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found

:: Check MySQL
where mysql >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] MySQL CLI not found in PATH.
    echo.
    echo To install MySQL:
    echo   Option 1: Download MySQL Installer from https://dev.mysql.com/downloads/installer/
    echo   Option 2: Install via winget: winget install Oracle.MySQL
    echo   Option 3: Use XAMPP: https://www.apachefriends.org/
    echo.
    echo After installing MySQL:
    echo   1. Start MySQL service
    echo   2. Update backend\.env with your MySQL credentials
    echo   3. Run this script again or run: npm start
    echo.
) else (
    echo [OK] MySQL found
)

:: Install dependencies
echo.
echo Installing Node.js dependencies...
cd /d "%~dp0"
call npm install
echo.

echo [DONE] Setup complete!
echo.
echo Next steps:
echo   1. Make sure MySQL is running
echo   2. Edit .env file with your MySQL credentials
echo   3. Run: npm start
echo.
pause
