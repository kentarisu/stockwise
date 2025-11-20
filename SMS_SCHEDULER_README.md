# StockWise SMS Scheduler - Quick Start Guide

## What It Does

Automatically sends SMS notifications:
- **Daily Sales Summary** - Every day at 8:00 PM (or your configured time)
- **Low Stock Alerts** - **REAL-TIME** (sent immediately when stock drops below threshold)
- **Pricing Recommendations** - Every 3 days at 10:00 AM

## Quick Start

### Option 1: Run in Foreground (Recommended for Testing)

**Double-click:** `start_sms_scheduler.bat`

Or in terminal:
```bash
cd C:\Users\Orly\stockwise
start_sms_scheduler.bat
```

The scheduler will run and show logs in the window. Press `Ctrl+C` to stop.

### Option 2: Run in Background (Recommended for Production)

**Right-click** `start_sms_scheduler_background.ps1` → **Run with PowerShell**

Or in PowerShell:
```powershell
cd C:\Users\Orly\stockwise
.\start_sms_scheduler_background.ps1
```

The scheduler will run in the background even if you close the terminal.

### Stop the Scheduler

**Right-click** `stop_sms_scheduler.ps1` → **Run with PowerShell**

Or in PowerShell:
```powershell
.\stop_sms_scheduler.ps1
```

## View Logs

The scheduler saves logs to `sms_scheduler.log`

To view live logs:
```powershell
Get-Content sms_scheduler.log -Wait
```

Or just open `sms_scheduler.log` in a text editor.

## Enable/Disable Notifications

Go to **Settings > SMS Settings** in StockWise and toggle:
- ✅ Sales Summary Enabled
- ✅ Low Stock Alerts Enabled  
- ✅ Pricing Recommendations Enabled

The scheduler will automatically respect these settings.

## Scheduled Times

| Notification | Time | Frequency |
|-------------|------|-----------|
| Sales Summary | 8:00 PM | Daily |
| Low Stock Alerts | **REAL-TIME** | Sent immediately when stock ≤ threshold |
| Pricing Recommendations | 10:00 AM | Every 3 days |

**Note:** Sales time can be changed in SMS Settings. Low stock alerts are event-driven (sent when stock drops), not time-based.

## Troubleshooting

### Scheduler not sending SMS

1. **Check if scheduler is running:**
   ```powershell
   Get-Process -Name python | Where-Object { $_.CommandLine -like "*sms_scheduler*" }
   ```

2. **Check logs:**
   ```powershell
   Get-Content sms_scheduler.log -Tail 50
   ```

3. **Check SMS Settings:**
   - Open StockWise → Settings → SMS Settings
   - Ensure notifications are enabled

4. **Manually test commands:**
   ```bash
   python manage.py send_daily_sms --now
   python manage.py send_low_stock_alerts --test
   python manage.py send_auto_pricing --force
   ```

### Scheduler won't start

1. **Ensure virtual environment exists:**
   ```bash
   venv\Scripts\activate
   ```

2. **Check Python installation:**
   ```bash
   python --version
   ```

3. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running on Server Startup (Optional)

To make the scheduler start automatically when Windows boots:

1. Press `Win + R`, type `shell:startup`, press Enter
2. Create a shortcut to `start_sms_scheduler_background.ps1`
3. Right-click shortcut → Properties
4. In "Target" field, add:
   ```
   powershell.exe -WindowStyle Hidden -File "C:\Users\Orly\stockwise\start_sms_scheduler_background.ps1"
   ```
5. Click OK

Now the scheduler will start automatically on system boot!

## Files

- `sms_scheduler.py` - Main scheduler script
- `start_sms_scheduler.bat` - Start in foreground (shows logs)
- `start_sms_scheduler_background.ps1` - Start in background
- `stop_sms_scheduler.ps1` - Stop the scheduler
- `sms_scheduler.log` - Log file
- `sms_scheduler.pid` - Process ID file (auto-created)

## Support

For issues, check:
1. `sms_scheduler.log` for errors
2. SMS Settings are enabled
3. Admin phone numbers are configured
4. SMS credits are available at https://iprogsms.com

---

**Last Updated:** November 2025

