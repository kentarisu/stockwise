@echo off
title StockWise ngrok Setup
color 0A

echo.
echo ===============================================
echo    StockWise ngrok Setup Assistant
echo ===============================================
echo.

echo Step 1: Creating ngrok directory...
if not exist "C:\ngrok" mkdir "C:\ngrok"
echo Directory created: C:\ngrok
echo.

echo Step 2: Checking if ngrok is already installed...
if exist "C:\ngrok\ngrok.exe" (
    echo ngrok.exe found! Skipping download.
    goto :configure
) else (
    echo ngrok.exe not found.
    goto :download
)

:download
echo.
echo Step 3: Manual Download Required
echo ================================
echo.
echo Please follow these steps:
echo.
echo 1. Open your web browser
echo 2. Go to: https://ngrok.com/download
echo 3. Download "Windows (64-bit)" version
echo 4. Extract ngrok.exe to C:\ngrok\
echo 5. Press any key when done...
pause >nul

if not exist "C:\ngrok\ngrok.exe" (
    echo.
    echo ERROR: ngrok.exe not found in C:\ngrok\
    echo Please make sure you extracted it correctly.
    pause
    exit /b 1
)

:configure
echo.
echo Step 4: ngrok Account Setup
echo ===========================
echo.
echo Please follow these steps:
echo.
echo 1. Go to: https://ngrok.com/
echo 2. Sign up for a FREE account
echo 3. Login and go to: https://dashboard.ngrok.com/get-started/your-authtoken
echo 4. Copy your authtoken
echo.
echo Press any key when you have your authtoken...
pause >nul

echo.
echo Please enter your ngrok authtoken:
set /p authtoken="Authtoken: "

echo.
echo Configuring ngrok...
"C:\ngrok\ngrok.exe" config add-authtoken %authtoken%

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS! ngrok is now configured.
) else (
    echo.
    echo ERROR: Failed to configure ngrok.
    echo Please check your authtoken and try again.
    pause
    exit /b 1
)

echo.
echo Step 5: Starting StockWise Server
echo ==================================
echo.
echo Starting Django development server...
start "StockWise Server" cmd /k "python manage.py runserver 8000"

echo.
echo Step 6: Starting ngrok Tunnel
echo =============================
echo.
echo Starting ngrok tunnel...
echo Your StockWise system will be accessible via a public URL!
echo.
echo Press Ctrl+C to stop ngrok when done.
echo.
"C:\ngrok\ngrok.exe" http 8000

echo.
echo ngrok tunnel stopped.
pause

