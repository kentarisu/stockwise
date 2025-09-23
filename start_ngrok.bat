@echo off
echo Starting ngrok for StockWise...
echo.
echo Instructions:
echo 1. Make sure you have downloaded ngrok from https://ngrok.com/download
echo 2. Extract ngrok.exe to C:\ngrok\
echo 3. Sign up for a free ngrok account at https://ngrok.com/
echo 4. Get your authtoken from the dashboard
echo 5. Run: C:\ngrok\ngrok.exe config add-authtoken YOUR_AUTH_TOKEN
echo.
echo Starting ngrok tunnel...
C:\ngrok\ngrok.exe http 8000
pause
