# SMS Notification System Setup Instructions

## Overview
This SMS notification system automatically sends daily sales summaries to admin users every night at 11:00 PM.

## Features
- Daily sales summary SMS notifications
- Admin-only configuration interface
- Test SMS functionality
- Secure phone number storage
- Automatic scheduling

## Setup Steps

### 1. Install Required Dependencies
```bash
pip install twilio
```

### 2. Set Up Twilio Account
1. Go to [Twilio Console](https://console.twilio.com/)
2. Get your Account SID and Auth Token
3. Purchase a phone number for sending SMS

### 3. Configure Environment Variables
Add these to your environment or `.env` file:
```bash
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

### 4. Run Database Migration
```bash
python manage.py makemigrations core
python manage.py migrate
```

### 5. Set Up Scheduled Task

#### Option A: Using Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to "Daily" at 11:00 PM
4. Set action to start program: `python`
5. Add arguments: `manage.py send_daily_sms`
6. Set start in: `C:\Users\Orly\stockwise`

#### Option B: Using Django-crontab (Linux/Mac)
```bash
pip install django-crontab
```
Add to settings.py:
```python
CRONJOBS = [
    ('0 23 * * *', 'core.management.commands.send_daily_sms'),
]
```

### 6. Configure SMS Settings
1. Log in as admin
2. Go to SMS Settings in the navigation
3. Enter your phone number with country code (e.g., +1234567890)
4. Enable SMS notifications
5. Test the SMS functionality

## Usage

### Manual Testing
```bash
python manage.py send_daily_sms --test
```

### Daily Automatic
The system will automatically send SMS at 11:00 PM with:
- Total revenue for the day
- Number of transactions
- Total boxes sold
- Top 3 selling products

### SMS Format Example
```
📊 StockWise Daily Sales Summary
📅 Date: December 15, 2024

💰 Total Revenue: ₱15,250.00
📦 Total Boxes Sold: 45
🛒 Total Transactions: 12

🏆 Top Selling Products:
1. Green Grapes: 15 boxes
2. Red Grapes: 12 boxes
3. Apples: 8 boxes

📱 Sent by StockWise System
```

## Security Notes
- Phone numbers are stored securely in the database
- Only admin users can configure SMS settings
- SMS service credentials are stored as environment variables
- No personal data is shared in SMS messages

## Troubleshooting
- Check Twilio credentials are correct
- Verify phone number format includes country code
- Check server logs for SMS sending errors
- Test SMS functionality before enabling daily notifications
