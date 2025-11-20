@echo off
echo Starting StockWise SMS Scheduler...
echo.
echo This scheduler will automatically send:
echo - Daily Sales Summary at 8:00 PM
echo - Low Stock Alerts IMMEDIATELY when stock drops (real-time)
echo - Pricing Recommendations at 10:00 AM (every 3 days)
echo.
echo Press Ctrl+C to stop the scheduler
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat
python sms_scheduler.py

pause

