# SMS Automated Feature Deployment Guide

This guide ensures all automated/scheduled SMS notifications work correctly with sender_name "kaprets" in both local and Digital Ocean (or Render) hosting environments.

## Overview

All automated SMS notifications in StockWise use the sender_name "kaprets" and include:
1. **Daily Sales Summary** - Sent daily at configured time (default: 8:00 PM)
2. **Low Stock Alerts** - Sent in real-time when stock drops below threshold
3. **Pricing Recommendations** - Sent periodically based on configured schedule

## Configuration

### Sender Name Enforcement

The sender_name is **hardcoded to "kaprets"** in the SMS service to ensure consistency:

```python
# core/sms_service.py - Always uses 'kaprets'
self.sender_name = 'kaprets'  # Always use 'kaprets' regardless of settings
```

### Environment Variables

#### Required for Both Local and Production:

```bash
IPROG_API_TOKEN=your_api_token_here
IPROG_SENDER_NAME=kaprets  # Optional - will default to 'kaprets' anyway
```

#### Optional:
```bash
ENABLE_INTERNAL_SCHEDULER=true  # Only for local development
```

## Local Development Setup

### Option 1: Internal Scheduler (Recommended for Development)

1. Set environment variable:
   ```bash
   set ENABLE_INTERNAL_SCHEDULER=true  # Windows
   export ENABLE_INTERNAL_SCHEDULER=true  # Linux/Mac
   ```

2. Run Django server:
   ```bash
   python manage.py runserver
   ```
   
   The scheduler will start automatically in a background thread.

### Option 2: Separate Scheduler Process

Run the scheduler in a separate terminal:

```bash
python sms_scheduler.py
```

This will check for scheduled notifications every minute.

### Testing SMS Sending

Test SMS functionality:

```bash
python manage.py test_sms +639123456789 "Test message"
```

This will verify:
- API token configuration
- Phone number normalization
- SMS sending functionality
- Sender name ("kaprets") usage

## Digital Ocean / Render Deployment

### Procfile Configuration

The `Procfile` defines two processes:

```
web: gunicorn stockwise_py.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
worker: python sms_scheduler.py
```

### Environment Variables on Digital Ocean / Render

Add these environment variables to **both** the web service and worker:

1. **IPROG_API_TOKEN** - Your iProg SMS API token
   - Get from: https://sms.iprogtech.com/
   - Set the same value for both web and worker services

2. **IPROG_SENDER_NAME** (Optional) - Set to `kaprets`
   - Will default to 'kaprets' if not set
   - Setting it explicitly ensures consistency

3. **DATABASE_URL** - PostgreSQL connection string
   - Automatically set by Digital Ocean/Render if database is linked

4. **SECRET_KEY** - Django secret key
   - Generate a secure key for production
   - Use the same key for both web and worker

### Worker Process Setup

The worker process (`sms_scheduler.py`) must run continuously to check for scheduled notifications.

**On Digital Ocean / Render:**
- The `worker` line in `Procfile` ensures the scheduler runs as a separate process
- It will restart automatically if it crashes
- Logs are available in the service logs

**Verification:**
1. Check worker service is running
2. Check logs for: `"StockWise SMS Scheduler initialized"`
3. Verify: `"SMS Service initialized with sender_name='kaprets'"`

## SMS Notification Types

### 1. Daily Sales Summary

- **Schedule**: Daily at configured time (default: 8:00 PM)
- **Recipients**: All admin users with phone numbers
- **Sender**: Always "kaprets"
- **Command**: `python manage.py send_notifications --type daily_sales`

### 2. Low Stock Alerts

- **Schedule**: Real-time (triggered immediately when stock drops)
- **Recipients**: All admin users with phone numbers
- **Sender**: Always "kaprets"
- **Trigger**: Django signals on Product stock updates
- **Cooldown**: 24 hours per product to prevent spam

### 3. Pricing Recommendations

- **Schedule**: Periodic (default: every 3 days at 8:00 AM)
- **Recipients**: All admin users with phone numbers
- **Sender**: Always "kaprets"
- **Command**: `python manage.py send_notifications --type pricing`

## Verification Steps

### 1. Verify Sender Name

Check logs when SMS service initializes:
```
INFO SMS Service initialized with sender_name='kaprets', api_token='CONFIGURED'
```

### 2. Test SMS Sending

```bash
python manage.py test_sms +639123456789 "Test SMS from StockWise"
```

Expected output:
- ✓ SMS sent successfully!
- Message Code: [message_id]
- Check phone for message from "kaprets"

### 3. Check Scheduler Status

**Local:**
```bash
# Check logs for:
"StockWise SMS Scheduler initialized"
"SMS Service Configuration:"
"  - Sender Name: kaprets"
```

**Production (Digital Ocean/Render):**
- Check worker service logs
- Look for scheduler initialization messages
- Verify no errors in SMS service configuration

### 4. Monitor SMS Delivery

- Check iProg SMS dashboard: https://sms.iprogtech.com/
- Verify messages appear with sender "kaprets"
- Check message delivery status

## Troubleshooting

### SMS Not Sending

1. **Check API Token:**
   ```bash
   # Verify token is set
   echo $IPROG_API_TOKEN
   ```

2. **Check Logs:**
   - Local: Check console output or `sms_debug.log`
   - Production: Check service logs
   - Look for: `"SMS send failed"` or `"API token not configured"`

3. **Verify Sender Name:**
   - Check logs for: `"Sending SMS with sender_name='kaprets'"`
   - If different, there's a configuration issue

### Scheduler Not Running

**Local:**
- Ensure `ENABLE_INTERNAL_SCHEDULER=true` is set
- Or run `python sms_scheduler.py` manually

**Production:**
- Verify worker process is running
- Check Procfile configuration
- Review worker service logs

### Messages Not Appearing on iProg Dashboard

1. **Check API Response:**
   - Review logs for API response codes
   - Verify `success: true` in response

2. **Check Phone Number Format:**
   - Must be in format: `+639123456789` or `09123456789`
   - Will be normalized to: `639123456789`

3. **Verify API Token:**
   - Token must be valid and active
   - Check iProg account for token status

## Code Locations

### SMS Service
- **File**: `core/sms_service.py`
- **Class**: `IPROGSMSService`
- **Sender Name**: Hardcoded to `'kaprets'` in `__init__` method

### Scheduler
- **File**: `sms_scheduler.py`
- **Class**: `SMSScheduler`
- **Verifies**: SMS service configuration on startup

### Scheduled Commands
- **File**: `core/management/commands/send_notifications.py`
- **Function**: `schedule_now()` - Uses direct SMS sending

### Real-time Alerts
- **File**: `core/signals.py`
- **Function**: `send_low_stock_alert()` - Sends via `sms_service.send_sms()`

## Summary

✅ **Sender name is always "kaprets"** - Hardcoded in SMS service
✅ **Works in local and production** - Same code, different deployment methods
✅ **Comprehensive logging** - All SMS operations are logged
✅ **Error handling** - Retries and fallbacks for reliability
✅ **Verification** - Startup checks verify configuration

All automated SMS notifications will use sender_name "kaprets" consistently across all environments.

