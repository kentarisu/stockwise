@echo off
echo Setting up ngrok for StockWise...
echo.
echo Please enter your ngrok authtoken (get it from https://dashboard.ngrok.com/get-started/your-authtoken):
set /p authtoken="Enter your authtoken: "
echo.
echo Configuring ngrok...
C:\ngrok\ngrok.exe config add-authtoken %authtoken%
echo.
echo ngrok configured successfully!
echo.
echo Now you can run start_ngrok.bat to start the tunnel
pause
