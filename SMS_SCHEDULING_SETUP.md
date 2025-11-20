# StockWise SMS Notification Scheduling Setup

This guide explains how to set up automatic SMS notifications for StockWise on Windows.

## Overview

StockWise has three automatic SMS notifications:
1. **Daily Sales Summary** - Sent once per day
2. **Low Stock Alerts** - Sent when products fall below threshold
3. **Pricing Recommendations** - Sent every 3 days with AI-powered pricing suggestions

## Prerequisites

- Windows 10/11 or Windows Server
- StockWise system installed and running
- Admin phone numbers configured in the system
- SMS notifications enabled in Settings > SMS Settings

## Setup Using Windows Task Scheduler

### 1. Open Task Scheduler

1. Press `Win + R`, type `taskschd.msc`, and press Enter
2. Or search for "Task Scheduler" in the Start menu

### 2. Create Task for Daily Sales Summary

**Schedule: Daily at 8:00 PM (or time configured in SMS Settings)**

1. Click **"Create Basic Task"** in the right panel
2. **Name**: `StockWise - Daily Sales Summary`
3. **Description**: `Send daily sales summary SMS to admins`
4. **Trigger**: Select **"Daily"**
   - Start date: Today
   - Recur every: **1** days
   - Time: **20:00:00** (8:00 PM) - *Match your SMS Settings time*
5. **Action**: Select **"Start a program"**
   - **Program/script**: `C:\Users\Orly\stockwise\venv\Scripts\python.exe` *(adjust path to your Python)*
   - **Add arguments**: `manage.py send_daily_sms`
   - **Start in**: `C:\Users\Orly\stockwise` *(your project directory)*
6. Click **"Finish"**
7. Right-click the task > **Properties** > **Settings** tab
   - ✅ Check "Run task as soon as possible after a scheduled start is missed"
   - ✅ Check "If the task fails, restart every" > Set to **10 minutes** > Retry **3** times

### 3. Create Task for Low Stock Alerts

**Schedule: Daily at 9:00 AM**

1. Click **"Create Basic Task"**
2. **Name**: `StockWise - Low Stock Alerts`
3. **Description**: `Send low stock alerts SMS to admins`
4. **Trigger**: Select **"Daily"**
   - Start date: Today
   - Recur every: **1** days
   - Time: **09:00:00** (9:00 AM)
5. **Action**: Select **"Start a program"**
   - **Program/script**: `C:\Users\Orly\stockwise\venv\Scripts\python.exe`
   - **Add arguments**: `manage.py send_low_stock_alerts`
   - **Start in**: `C:\Users\Orly\stockwise`
6. Click **"Finish"**
7. Configure retry settings (same as above)

### 4. Create Task for Pricing Recommendations

**Schedule: Every 3 days at 10:00 AM**

1. Click **"Create Basic Task"**
2. **Name**: `StockWise - Pricing Recommendations`
3. **Description**: `Send AI-powered pricing recommendations SMS to admins`
4. **Trigger**: Select **"Daily"**
   - Start date: Today
   - Recur every: **3** days
   - Time: **10:00:00** (10:00 AM)
5. **Action**: Select **"Start a program"**
   - **Program/script**: `C:\Users\Orly\stockwise\venv\Scripts\python.exe`
   - **Add arguments**: `manage.py send_auto_pricing`
   - **Start in**: `C:\Users\Orly\stockwise`
6. Click **"Finish"**
7. Configure retry settings (same as above)

## Testing the SMS Commands

Before setting up the scheduler, test each command manually:

### Test Daily Sales Summary
```powershell
cd C:\Users\Orly\stockwise
.\venv\Scripts\activate
python manage.py send_daily_sms --now
```

### Test Low Stock Alerts
```powershell
python manage.py send_low_stock_alerts --test
```

### Test Pricing Recommendations
```powershell
python manage.py send_auto_pricing --force
```

## Monitoring and Logs

### Check Task Execution
1. Open Task Scheduler
2. Select your task
3. Click on the **"History"** tab to see execution logs

### Check Django Logs
SMS notifications are logged to the Django console and log files. Check:
```
C:\Users\Orly\stockwise\logs\
```

### Check SMS Credits
Monitor your SMS credits at: https://iprogsms.com
- Login with your account
- View credits balance
- Check SMS history

## SMS Settings Configuration

All SMS notifications respect the settings in **Settings > SMS Settings**:

- **Sales Summary**
  - ✅ Enable/Disable toggle
  - ⏰ Send Time (fixed at 20:00 or your configured time)

- **Low Stock Alerts**
  - ✅ Enable/Disable toggle
  - 📊 Threshold (fixed at 10 boxes or your configured threshold)

- **Pricing Recommendations**
  - ✅ Enable/Disable toggle
  - 📈 Sensitivity (conservative/moderate/aggressive)

## Troubleshooting

### SMS Not Sending

1. **Check if notifications are enabled**
   - Go to Settings > SMS Settings
   - Ensure the relevant notification type is enabled (toggle is ON)

2. **Check admin phone numbers**
   - Go to Profile > Account Management
   - Ensure admin accounts have valid phone numbers

3. **Check SMS credits**
   - Login to https://iprogsms.com
   - Ensure you have sufficient credits

4. **Check Task Scheduler logs**
   - Open Task Scheduler
   - Find your task
   - Check the "History" tab for errors

5. **Manually run the command**
   ```powershell
   cd C:\Users\Orly\stockwise
   .\venv\Scripts\activate
   python manage.py send_daily_sms --now
   ```

### Task Not Running at Scheduled Time

1. **Ensure computer is powered on**
   - Task Scheduler requires the computer to be running
   - For production, use a server that's always on

2. **Check task settings**
   - Right-click task > Properties > Settings
   - Ensure "Run task as soon as possible after a scheduled start is missed" is checked

3. **Check task user permissions**
   - Right-click task > Properties > General tab
   - Ensure "Run whether user is logged on or not" is selected
   - Ensure the user account has permissions

## Alternative: Using Python Schedule (Optional)

If you prefer a Python-based scheduler:

1. Install schedule:
```bash
pip install schedule
```

2. Create `scheduler.py` in your project root:
```python
import schedule
import time
import subprocess
import os

# Change to project directory
os.chdir(r'C:\Users\Orly\stockwise')

def run_daily_sales():
    subprocess.run(['python', 'manage.py', 'send_daily_sms'])

def run_low_stock():
    subprocess.run(['python', 'manage.py', 'send_low_stock_alerts'])

def run_pricing():
    subprocess.run(['python', 'manage.py', 'send_auto_pricing'])

# Schedule jobs
schedule.every().day.at("20:00").do(run_daily_sales)
schedule.every().day.at("09:00").do(run_low_stock)
schedule.every(3).days.at("10:00").do(run_pricing)

print("StockWise SMS Scheduler started...")
while True:
    schedule.run_pending()
    time.sleep(60)
```

3. Run the scheduler:
```bash
python scheduler.py
```

4. (Optional) Create a Windows Service to run it in the background.

## Support

For issues or questions:
- Check the Django logs
- Check Task Scheduler History
- Check iProg SMS documentation: https://iprogsms.com/api/v1/documentation
- Contact your system administrator

---

**Last Updated**: November 2025
**Version**: 1.0

