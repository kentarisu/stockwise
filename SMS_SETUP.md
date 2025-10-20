# SMS Notification System Setup Instructions

## Overview
This SMS notification system automatically sends daily sales summaries to admin users every night at 11:00 PM using iProg SMS API.

## Features
- Daily sales summary SMS notifications
- Admin-only configuration interface
- Test SMS functionality
- Secure phone number storage
- Automatic scheduling
- iProg SMS API integration (Philippines-focused)

## Setup Steps

### 1. Install Required Dependencies
```bash
pip install requests
```

### 2. Set Up iProg SMS API Account
1. Go to [iProg SMS API](https://sms.iprogtech.com/)
2. Register for an account
3. Navigate to your profile to retrieve your unique API token
4. Note: iProg SMS API is optimized for Philippine mobile networks (Globe, Smart, TNT, Sun)

### 3. Configure Environment Variables
Add these to your environment or `.env` file:
```bash
IPROG_API_TOKEN=your_api_token_here
IPROG_SENDER_ID=STOCKWISE
```

Or add directly to `stockwise_py/settings.py`:
```python
IPROG_API_TOKEN = 'your_api_token_here'
IPROG_SENDER_ID = 'STOCKWISE'  # Custom sender name (max 11 characters)
```

**Note**: Custom sender IDs must be registered with iProg first. Contact iProg support to register "STOCKWISE" as your sender ID. Until approved, messages will show "IPROGSMS" as the sender.

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
3. Enter your phone number (formats accepted):
   - With country code: +639123456789
   - Without country code: 09123456789 or 9123456789
   - System will automatically format to iProg format (639123456789)
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

## Technical Details

### Phone Number Format
iProg SMS API requires phone numbers in the format: `639xxxxxxxxx` (12 digits)
- The system automatically converts various formats:
  - `09123456789` → `639123456789`
  - `+639123456789` → `639123456789`
  - `9123456789` → `639123456789`

### API Endpoint
- **URL**: `https://sms.iprogtech.com/api/v1/sms_messages`
- **Method**: POST
- **Parameters**:
  - `api_token`: Your iProg API token
  - `phone_number`: Recipient number (639xxxxxxxxx format)
  - `message`: SMS content

### SMS Service Module
All SMS functionality is centralized in `core/sms_service.py`:
```python
from core.sms_service import send_sms

# Send SMS
result = send_sms('09123456789', 'Your message here')
if result['success']:
    print('SMS sent successfully')
else:
    print(f'Error: {result["message"]}')
```

## Security Notes
- Phone numbers are stored securely in the database
- Only admin users can configure SMS settings
- SMS service credentials are stored as environment variables
- No personal data is shared in SMS messages
- API token should never be committed to version control

## Custom Sender ID

### Changing "IPROGSMS" to "STOCKWISE"

By default, SMS messages will show "IPROGSMS" as the sender. To change this to "STOCKWISE":

1. **Register Your Sender ID with iProg**
   - Contact iProg support at: https://sms.iprogtech.com/
   - Request to register "STOCKWISE" as your custom sender ID
   - Wait for approval (usually 1-2 business days)

2. **Already Configured in Your System**
   - The system is already set to use "STOCKWISE" as sender ID
   - Configuration in `stockwise_py/settings.py`:
     ```python
     IPROG_SENDER_ID = 'STOCKWISE'
     ```

3. **After Approval**
   - Once iProg approves your sender ID, all SMS will automatically show "STOCKWISE"
   - No code changes needed - it's already configured!

**Note**: Sender ID must be 11 characters or less, alphanumeric only.

## Troubleshooting

### Common Issues

1. **API Token Not Configured**
   - Error: "iProg API token not configured"
   - Solution: Set `IPROG_API_TOKEN` in environment or settings.py

2. **Invalid Phone Number Format**
   - Error: "Invalid phone number format"
   - Solution: Ensure phone number is a valid Philippine mobile number (10 digits starting with 9)

3. **Invalid API Token or No Load Balance**
   - Error: "Invalid api token or no load balance"
   - Solution: Check your iProg account credits and reload if needed
   - Visit: https://sms.iprogtech.com/ to add load balance

3. **Network/API Errors**
   - Check your internet connection
   - Verify iProg API service status
   - Check server logs for detailed error messages

4. **SMS Not Received**
   - Verify phone number is correct
   - Check iProg account balance/credits
   - Test with different mobile networks (Globe, Smart, TNT, Sun)
   - Check for service notices on iProg platform

5. **Testing Commands**
   ```bash
   # Test SMS functionality
   python manage.py send_daily_sms --test
   
   # Send today's report immediately
   python manage.py send_daily_report
   ```

## Credits and Monitoring

To check your remaining SMS credits (if supported):
```python
from core.sms_service import sms_service

result = sms_service.check_credits()
if result['success']:
    print(result['data'])
```

## Migration from Twilio

If you're migrating from Twilio:
1. The new iProg integration is already set up
2. Remove old Twilio environment variables (optional)
3. Set the new `IPROG_API_TOKEN` environment variable
4. Phone number formats remain compatible
5. All SMS functionality continues to work seamlessly
