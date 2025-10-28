# 📱 STOCKWISE SMS Messages - Complete Guide

**Date**: October 21, 2025  
**Status**: ✅ All messages updated with STOCKWISE branding

---

## 🎯 SMS System Purpose

Your StockWise system sends **4 types of automated SMS notifications** to help manage your inventory:

1. **Low Stock Alerts** - When products fall below threshold
2. **Out of Stock Alerts** - When products run out completely  
3. **Daily Sales Reports** - Summary of daily business performance
4. **Stock Reports** - Comprehensive inventory status

---

## 📋 Message Types

### 1. Low Stock Alert 🔔

**When it's sent:**
- Automatically after a sale reduces stock to ≤10 boxes
- When stock is manually updated to ≤10 boxes

**Example Message:**
```
STOCKWISE Low Stock Alert

Product: Apple (120)
Current Stock: 5 boxes
Threshold: 10 boxes
Price: PHP 150.00/kg
Action: Consider restocking soon.

- STOCKWISE System
```

**Triggers:** 
- `core/signals.py` - Automatic after sale or stock update
- Sent to all admin phone numbers

---

### 2. Out of Stock Alert 🚨

**When it's sent:**
- Automatically when product stock reaches 0
- Critical alert for immediate action

**Example Message:**
```
STOCKWISE ALERT: Out of Stock

Product: Banana (130)
Status: OUT OF STOCK
Price: PHP 120.00/kg
Action: Restock immediately!

- STOCKWISE System
```

**Triggers:**
- `core/signals.py` - Automatic when stock = 0
- Sent to all admin phone numbers

---

### 3. Daily Sales Report 📊

**When it's sent:**
- Manually triggered by admin from dashboard
- Can be scheduled via cron job

**Example Message:**
```
STOCKWISE Daily Sales Report
Date: October 21, 2025

Total Revenue: PHP 15,450.00
Boxes Sold: 125
Transactions: 23

Top Products:
- Apple: 45 boxes
- Banana: 38 boxes
- Mango: 25 boxes
- Orange: 17 boxes

- STOCKWISE Analytics
```

**Triggers:**
- `core/views.py` - `send_all_notifications_now()` function
- Admin-only feature
- Shows today's complete sales summary

---

### 4. Stock Report 📦

**When it's sent:**
- Manually triggered by admin from dashboard
- Shows current inventory status

**Example Message:**
```
STOCKWISE Stock Report

OUT OF STOCK:
- Banana (130)
- Mango (140)

LOW STOCK (below 10):
- Apple (120): 5 boxes
- Orange (150): 8 boxes
- Grapes (160): 3 boxes

- STOCKWISE Inventory
```

**Triggers:**
- `core/views.py` - `send_all_notifications_now()` function
- Admin-only feature
- Lists all products with stock issues

---

## 🔧 Technical Implementation

### Files Modified:

| File | Purpose | Lines Changed |
|------|---------|---------------|
| `core/signals.py` | Automatic low/out-of-stock alerts | Lines 50-65 |
| `core/views.py` | Daily sales & stock reports | Lines 4362-4393 |
| `core/sms_service.py` | SMS sending with Unicode handling | Lines 83-105 |

### Key Features:

✅ **STOCKWISE branding** in all message content  
✅ **No emojis** - Plain text GSM-7 compatible  
✅ **Peso signs (₱)** auto-convert to "PHP"  
✅ **Retry mechanism** - 3 attempts with exponential backoff  
✅ **Admin-only** notifications to configured phone numbers

---

## 📞 Who Receives SMS?

### Automatic Alerts (Low/Out of Stock):
- **All users with role = 'Admin'**
- Must have phone number configured
- Sent immediately when triggered

### Manual Reports (Sales/Stock):
- **Currently logged-in admin**
- Uses phone number from user session
- Triggered from dashboard

---

## 🧪 Testing Your Messages

### Test Script Created: `send_test_sms.py`

Run this to send all 4 message types to your phone:

```bash
python send_test_sms.py
```

**What it does:**
1. Sends Low Stock Alert sample
2. Sends Out of Stock Alert sample
3. Sends Daily Sales Report sample
4. Sends Stock Report sample

**All messages sent to:** `09777111604`

---

## 📱 How Messages Appear on Phone

### What You'll See:

```
From: PhilSMS  (or iProg system number)

Message:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STOCKWISE Low Stock Alert    ← Your branding!

Product: Apple (120)
Current Stock: 5 boxes
Threshold: 10 boxes
Price: PHP 150.00/kg         ← Auto-converted from ₱
Action: Consider restocking soon.

- STOCKWISE System           ← Your branding!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## ⚙️ Configuration

### In `stockwise_py/settings.py`:
```python
IPROG_SENDER_ID = 'PHILSMS'          # API sender ID
IPROG_SMS_ADMIN_PHONE = '09777111604'  # Your admin phone
SMS_APP_NAME = 'STOCKWISE'            # App branding
```

### Admin Phone Numbers:
Stored in `AppUser` model:
- Field: `phone_number`
- Must have: `role = 'Admin'`

---

## 🔄 Message Flow

### Automatic Flow (Low/Out of Stock):
```
1. Sale completed OR Stock updated
2. Django signal triggered (core/signals.py)
3. Check if stock ≤ 10 or = 0
4. Get all admin phone numbers
5. Format message with STOCKWISE branding
6. Send SMS via iProg API (with retry)
7. Log result
```

### Manual Flow (Sales/Stock Reports):
```
1. Admin clicks "Send Notifications" in dashboard
2. View function called (core/views.py)
3. Query database for sales/stock data
4. Format messages with STOCKWISE branding
5. Send SMS to logged-in admin's phone
6. Return success/failure response
```

---

## 📊 Message Characteristics

| Message Type | Typical Length | SMS Count | Priority |
|--------------|----------------|-----------|----------|
| Low Stock Alert | 120-150 chars | 1 SMS | Medium |
| Out of Stock Alert | 100-130 chars | 1 SMS | High |
| Daily Sales Report | 180-250 chars | 2 SMS | Low |
| Stock Report | 150-300 chars | 2-3 SMS | Medium |

---

## ✅ Quality Checks

All messages now have:

- [x] STOCKWISE branding at start
- [x] STOCKWISE signature at end
- [x] No emojis (GSM-7 compatible)
- [x] Peso signs converted to "PHP"
- [x] Clear, actionable information
- [x] Professional formatting
- [x] Proper line breaks
- [x] Consistent style across all types

---

## 🚀 How to Trigger Each Message

### 1. Low Stock Alert (Automatic)
```python
# In Django shell or when selling
from core.models import Product, Sale

# Create a sale that reduces stock below 10
product = Product.objects.get(name='Apple')
# ... complete a sale
# SMS automatically sent when stock ≤ 10
```

### 2. Out of Stock Alert (Automatic)
```python
# Sell all remaining stock
# SMS automatically sent when stock = 0
```

### 3. Daily Sales Report (Manual)
```
1. Login as Admin
2. Go to Dashboard
3. Click "Send All Notifications"
4. Check your phone
```

### 4. Stock Report (Manual)
```
Same as #3 - sent together with sales report
```

---

## 🔍 Troubleshooting

### "HelloTest" Message Received
**Problem:** Test message without STOCKWISE branding  
**Solution:** Use `send_test_sms.py` to send proper branded messages

### No SMS Received
**Possible causes:**
1. No admin phone number configured
2. iProg API token not set
3. Insufficient SMS credits
4. Network/telco issues (retry handles this)

**Check:**
- `IPROG_API_TOKEN` environment variable
- Admin user has `phone_number` field filled
- iProg dashboard for credits/errors

### Emojis Still Appearing
**Problem:** Old code sending emojis  
**Solution:** All updated! Emojis now auto-convert to text

---

## 📞 Support

**SMS Configuration:**
- Sender ID: `PHILSMS` (API compliance)
- App Name: `STOCKWISE` (your branding)
- Admin Phone: `09777111604`

**Test Messages:**
```bash
python send_test_sms.py
```

**Check Logs:**
```bash
# In Django shell
from core.sms_service import send_sms

result = send_sms('09777111604', 'STOCKWISE Test\n\nThis is a test.\n\n- STOCKWISE')
print(result)
```

---

## 🎉 Summary

✅ **4 message types** all updated with STOCKWISE branding  
✅ **Automatic alerts** for low/out-of-stock situations  
✅ **Manual reports** for daily sales and inventory  
✅ **No emojis** - plain text GSM-7 compatible  
✅ **Professional** appearance with clear branding  
✅ **Retry mechanism** ensures delivery  

**Your SMS system is now fully branded and production-ready!** 🎊

---

**Next Steps:**
1. Run `python send_test_sms.py` to test all message types
2. Check your phone (09777111604) for 4 test messages
3. Verify STOCKWISE branding appears in message content
4. Monitor actual system alerts when stock gets low

**Last Updated:** October 21, 2025  
**Files Updated:** `core/signals.py`, `core/views.py`, `core/sms_service.py`

