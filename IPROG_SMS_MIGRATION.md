# iProg SMS API Migration Guide

## Migration Summary

Your StockWise system has been successfully migrated from Twilio to iProg SMS API. This document provides a summary of all changes made.

## What Changed

### 1. New SMS Service Module
**File**: `core/sms_service.py`
- Created a centralized SMS service module
- Handles all SMS sending functionality
- Automatic phone number normalization for Philippine numbers
- Supports multiple phone number formats (09xxxxxxxxx, +639xxxxxxxxx, etc.)

### 2. Updated Settings
**File**: `stockwise_py/settings.py`
- Removed Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_PHONE)
- Added iProg API token configuration: `IPROG_API_TOKEN`

### 3. Updated Management Commands
All management commands now use the new iProg SMS service:
- `core/management/commands/send_daily_sms.py` - Daily sales summaries
- `core/management/commands/send_daily_report.py` - Daily reports
- `core/management/commands/generate_pricing_recommendations.py` - Pricing alerts

### 4. Updated Views
**File**: `core/views.py`
- Updated error messages to reference iProg instead of Twilio
- Improved error hints for Philippine phone number formats

### 5. Updated Documentation
**File**: `SMS_SETUP.md`
- Complete rewrite for iProg SMS API setup
- Detailed phone number format guidelines
- Troubleshooting section for common issues
- Migration notes from Twilio

## Required Configuration

### Environment Variable (Recommended)
```bash
IPROG_API_TOKEN=your_api_token_here
```

### Or Direct in Settings
In `stockwise_py/settings.py`:
```python
IPROG_API_TOKEN = 'your_api_token_here'
```

## Getting Your iProg API Token

1. Visit [iProg SMS API](https://sms.iprogtech.com/)
2. Register for an account
3. Navigate to your profile
4. Copy your unique API token
5. Set it in your environment or settings.py

## Phone Number Format

iProg SMS API uses Philippine phone number format: `639xxxxxxxxx`

The system automatically converts from:
- `09123456789` → `639123456789`
- `+639123456789` → `639123456789`
- `9123456789` → `639123456789`

## Testing the Migration

### Test SMS Command
```bash
python manage.py send_daily_sms --test
```

### Test from Django Shell
```python
from core.sms_service import send_sms

# Test sending SMS
result = send_sms('09123456789', 'Test message from StockWise')
print(result)
```

### Check SMS Service Status
```python
from core.sms_service import sms_service

# Check if configured
result = sms_service.send_sms('09123456789', 'Test')
if result['success']:
    print('SMS service is working!')
else:
    print(f'Error: {result["message"]}')
```

## Features

### Automatic Phone Number Normalization
- Handles various input formats
- Validates Philippine mobile numbers
- Clear error messages for invalid formats

### Centralized Service
- Single point of SMS functionality
- Easy to maintain and update
- Consistent behavior across all features

### Error Handling
- Detailed error messages
- Network error detection
- API response validation
- Helpful troubleshooting hints

## Dependencies

### Required Package
```bash
pip install requests
```

### Optional (for development)
No additional packages required. The `requests` library is standard for HTTP requests.

## API Details

### Endpoint
```
POST https://sms.iprogtech.com/api/v1/sms_messages
```

### Parameters
- `api_token`: Your iProg API token
- `phone_number`: Recipient number (639xxxxxxxxx format)
- `message`: SMS content

### Response Format
```json
{
  "status": "success",
  "message": "SMS sent successfully"
}
```

## Benefits of iProg SMS API

1. **Philippine-Focused**: Optimized for Philippine mobile networks (Globe, Smart, TNT, Sun)
2. **Cost-Effective**: Generally more affordable for Philippine SMS
3. **Simple API**: Easy-to-use REST API
4. **No Phone Number**: No need for a sender phone number (unlike Twilio)
5. **Local Support**: Better support for Philippine businesses

## Backward Compatibility

All existing functionality remains the same:
- Daily sales SMS notifications
- Test SMS functionality
- Admin phone number configuration
- Scheduled tasks continue to work
- No database changes required

## Troubleshooting

### Common Issues

1. **"iProg API token not configured"**
   - Solution: Set `IPROG_API_TOKEN` environment variable

2. **"Invalid phone number format"**
   - Solution: Use Philippine mobile format (09xxxxxxxxx)

3. **"Network error"**
   - Solution: Check internet connection and iProg service status

4. **SMS not received**
   - Check phone number is correct
   - Verify iProg account has sufficient credits
   - Try different mobile network

### Getting Help

- Check `SMS_SETUP.md` for detailed setup instructions
- Review server logs for detailed error messages
- Contact iProg support for API issues

## Next Steps

1. **Set up your iProg API token**
   - Get token from iProg website
   - Set environment variable or update settings.py

2. **Test the integration**
   - Run test command: `python manage.py send_daily_sms --test`
   - Verify SMS is received

3. **Configure admin phone numbers**
   - Log in as admin
   - Go to SMS Settings
   - Enter your phone number
   - Test notifications

4. **Remove old Twilio dependencies (optional)**
   - Uninstall: `pip uninstall twilio`
   - Remove environment variables: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_PHONE`

## Support

For issues or questions:
- Check documentation: `SMS_SETUP.md`
- Review this migration guide
- Test with the provided commands
- Check iProg API documentation: https://sms.iprogtech.com/

---

**Migration completed**: All SMS functionality has been successfully migrated to iProg SMS API.

