# iProg SMS Updated Configuration

**Date**: October 21, 2025  
**Status**: Updated to comply with iProg SMS requirements

---

## 🔧 Changes Made

### 1. Sender ID Updated
- **Old**: `STOCKWISE`
- **New**: `PHILSMS`
- **Location**: `stockwise_py/settings.py` and `core/sms_service.py`

⚠️ **IMPORTANT NOTE**: iProg SMS currently **does NOT support custom sender IDs**. All messages will use iProg's system sender route regardless of the configured sender ID. This setting is kept for future use when custom sender IDs are supported.

### 2. Admin Phone Number Updated
- **Old**: Various test numbers
- **New**: `09777111604`
- **Location**: `stockwise_py/settings.py`

### 3. Unicode Character Handling Enhanced
All SMS messages now automatically convert Unicode characters to plain text to avoid telco delivery issues:

#### Currency Symbols
- `₱` → `PHP`
- `€` → `EUR`
- `£` → `GBP`
- `$` → `USD`

#### Smart Quotes and Punctuation
- `"` `"` → `"`
- `'` `'` → `'`
- `—` `–` → `-`
- `…` → `...`

#### Emojis and Special Characters
- All emojis removed or replaced with text equivalents
- `™`, `®`, `©` removed
- Any non-ASCII characters replaced with spaces

---

## 📋 Configuration Details

### Settings in `stockwise_py/settings.py`

```python
# SMS Configuration for IPROG SMS API
IPROG_SENDER_ID = 'PHILSMS'  # Will be supported in future
IPROG_SMS_ADMIN_PHONE = '09777111604'  # Admin phone for SMS notifications
```

### How to Set Your API Token

**Option 1: Environment Variable (Recommended)**
```bash
set IPROG_API_TOKEN=your_token_here
```

**Option 2: In settings.py (Not recommended for production)**
```python
IPROG_API_TOKEN = 'your_actual_token_from_iprog'
```

---

## ✅ SMS Message Format Guidelines

Based on iProg's recommendations, follow these rules:

### ❌ **DON'T USE:**
```
Payment Confirmation
Amount: ₱560.00    ❌ (Peso sign)
Thank you! ❤️      ❌ (Emoji)
Price: $50.00      ❌ (Dollar sign might be rejected)
Special offer™     ❌ (Trademark symbol)
```

### ✅ **DO USE:**
```
Payment Confirmation
Amount: PHP 560.00  ✅ (Plain text)
Thank you!          ✅ (No emoji)
Price: PHP 50.00    ✅ (Plain text)
Special offer       ✅ (No symbols)
```

---

## 🔍 How Unicode Conversion Works

The `_to_gsm_plaintext()` function in `core/sms_service.py` automatically handles conversion:

### Example 1: Payment Notification
**Before conversion:**
```
UZHA Payment Confirmation

Dear Bernard Sondia,

Your payment has been recorded successfully:
Amount: ₱560.00
Type: Monthly dues
Date: Oct 21, 2025

Thank you for your payment!

UZHA Management
```

**After conversion (automatically):**
```
UZHA Payment Confirmation

Dear Bernard Sondia,

Your payment has been recorded successfully:
Amount: PHP 560.00
Type: Monthly dues
Date: Oct 21, 2025

Thank you for your payment!

UZHA Management
```

### Example 2: Stock Alert
**Before:**
```
⚠️ Low Stock Alert!
Product: Apple 🍎
Stock: 5 boxes
Price: ₱100.00/kg
```

**After:**
```
Alert Low Stock Alert!
Product: Apple
Stock: 5 boxes
Price: PHP 100.00/kg
```

---

## 🚀 How to Use

### Sending SMS (Automatic Conversion)

```python
from core.sms_service import send_sms

# Example with Unicode characters (will be auto-converted)
message = """
StockWise Alert!

Low Stock: Banana 🍌
Current: 3 boxes
Price: ₱150.00/kg

Restock needed!
"""

# Send SMS (Unicode characters automatically removed)
result = send_sms(
    phone_number='09777111604',  # Your admin phone
    message=message
)

if result['success']:
    print('SMS sent successfully!')
else:
    print(f'Failed: {result["message"]}')
```

The message received will be:
```
StockWise Alert!

Low Stock: Banana
Current: 3 boxes
Price: PHP 150.00/kg

Restock needed!
```

---

## 🛡️ Retry Mechanism

The SMS service includes automatic retry with exponential backoff:

- **Max Retries**: 3 attempts
- **Retry Delay**: 2 seconds (exponential backoff)
- **Wait Times**: 0s, 2s, 4s
- **Total Max Wait**: 6 seconds

```python
result = send_sms(
    phone_number='09777111604',
    message='Test message',
    max_retries=3,      # Optional: default is 3
    retry_delay=2.0     # Optional: default is 2.0 seconds
)

print(f"Attempts made: {result.get('attempts')}")
```

---

## 📱 Testing Your Configuration

### Test 1: Send a Simple SMS
```python
from core.sms_service import send_sms

result = send_sms(
    phone_number='09777111604',
    message='StockWise test: This is a plain text message. Amount: PHP 100.00'
)

print(result)
```

### Test 2: Send with Unicode (Auto-conversion)
```python
from core.sms_service import send_sms

result = send_sms(
    phone_number='09777111604',
    message='Test with peso sign: ₱500.00 and emoji 📱'
)

print(result)
# Message delivered will be: "Test with peso sign: PHP 500.00 and emoji StockWise"
```

---

## 🔧 Troubleshooting

### Issue 1: Messages Not Delivered
**Possible Causes:**
1. ❌ Unicode characters (should be auto-handled now)
2. ❌ Invalid API token
3. ❌ Phone number format incorrect
4. ❌ Insufficient SMS credits

**Solution:**
- Check that API token is set correctly
- Verify phone number is in format: `639XXXXXXXXX` (auto-normalized)
- Check credits at https://sms.iprogtech.com

### Issue 2: Custom Sender ID Not Showing
**Expected Behavior**: This is normal! iProg SMS **does not support custom sender IDs yet**.

**What to Expect:**
- Messages will show iProg's system sender number
- Your configured sender ID (`PHILSMS`) is ignored
- iProg will announce when custom sender IDs are available

### Issue 3: Special Characters Still Causing Issues
**Solution:**
- The `_to_gsm_plaintext()` function should handle this automatically
- If issues persist, check the message manually before sending
- Ensure you're using the latest version of `core/sms_service.py`

---

## 📊 Message Length Limits

- **Single SMS**: 160 characters (GSM-7 encoding)
- **Long Messages**: Can be sent but may be split into multiple SMS
- **Unicode Mode**: AVOIDED (causes delivery issues)

**Tip**: Keep messages under 160 characters for best delivery rates.

---

## 🎯 Best Practices

1. ✅ **Use plain text only** - no special characters
2. ✅ **Replace ₱ with PHP** - better compatibility
3. ✅ **Avoid emojis** - they're auto-removed but better to not use
4. ✅ **Test first** - send to your own number before production
5. ✅ **Monitor deliverability** - check iProg dashboard
6. ✅ **Keep messages short** - under 160 characters when possible

---

## 📞 Support

**iProg SMS Support:**
- Website: https://sms.iprogtech.com
- Check for sender ID updates on their Facebook page
- Contact support for custom sender ID availability

**StockWise SMS Configuration:**
- Settings file: `stockwise_py/settings.py`
- Service file: `core/sms_service.py`
- Admin phone: `09777111604`

---

## 📝 Summary

✅ Sender ID changed to `PHILSMS` (future use)  
✅ Admin phone updated to `09777111604`  
✅ Unicode character handling enhanced  
✅ Peso sign (₱) auto-converts to "PHP"  
✅ All emojis and special characters removed  
✅ GSM-7 encoding enforced  
✅ Retry mechanism with 3 attempts  
✅ Messages guaranteed to be plain text only  

**Your SMS service is now fully compliant with iProg SMS requirements!** 🎉

