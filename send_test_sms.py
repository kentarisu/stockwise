"""
Send test SMS with actual STOCKWISE system messages
This shows the real messages your system will send
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise_py.settings')
django.setup()

from core.sms_service import send_sms
from core.models import Product, AppUser
from django.utils import timezone

print("=" * 70)
print("STOCKWISE SMS Test - Send Real System Messages")
print("=" * 70)

# Admin phone number
ADMIN_PHONE = '09777111604'

# Test Message 1: Low Stock Alert
print("\n1. Testing Low Stock Alert...")
low_stock_msg = """STOCKWISE Low Stock Alert

Product: Apple (120)
Current Stock: 5 boxes
Threshold: 10 boxes
Price: PHP 150.00/kg
Action: Consider restocking soon.

- STOCKWISE System"""

result1 = send_sms(ADMIN_PHONE, low_stock_msg)
print(f"   Status: {'SUCCESS' if result1['success'] else 'FAILED'}")
print(f"   Message: {result1['message']}")
if result1.get('attempts'):
    print(f"   Attempts: {result1['attempts']}")

# Test Message 2: Out of Stock Alert
print("\n2. Testing Out of Stock Alert...")
out_of_stock_msg = """STOCKWISE ALERT: Out of Stock

Product: Banana (130)
Status: OUT OF STOCK
Price: PHP 120.00/kg
Action: Restock immediately!

- STOCKWISE System"""

result2 = send_sms(ADMIN_PHONE, out_of_stock_msg)
print(f"   Status: {'SUCCESS' if result2['success'] else 'FAILED'}")
print(f"   Message: {result2['message']}")
if result2.get('attempts'):
    print(f"   Attempts: {result2['attempts']}")

# Test Message 3: Daily Sales Report
print("\n3. Testing Daily Sales Report...")
today = timezone.now().strftime('%B %d, %Y')
sales_msg = f"""STOCKWISE Daily Sales Report
Date: {today}

Total Revenue: PHP 15,450.00
Boxes Sold: 125
Transactions: 23

Top Products:
- Apple: 45 boxes
- Banana: 38 boxes
- Mango: 25 boxes
- Orange: 17 boxes

- STOCKWISE Analytics"""

result3 = send_sms(ADMIN_PHONE, sales_msg, allow_multipart=True)
print(f"   Status: {'SUCCESS' if result3['success'] else 'FAILED'}")
print(f"   Message: {result3['message']}")
if result3.get('attempts'):
    print(f"   Attempts: {result3['attempts']}")

# Test Message 4: Stock Report
print("\n4. Testing Stock Report...")
stock_report_msg = """STOCKWISE Stock Report

OUT OF STOCK:
- Banana (130)
- Mango (140)

LOW STOCK (below 10):
- Apple (120): 5 boxes
- Orange (150): 8 boxes
- Grapes (160): 3 boxes

- STOCKWISE Inventory"""

result4 = send_sms(ADMIN_PHONE, stock_report_msg, allow_multipart=True)
print(f"   Status: {'SUCCESS' if result4['success'] else 'FAILED'}")
print(f"   Message: {result4['message']}")
if result4.get('attempts'):
    print(f"   Attempts: {result4['attempts']}")

# Summary
print("\n" + "=" * 70)
print("Test Summary")
print("=" * 70)
results = [result1, result2, result3, result4]
success_count = sum(1 for r in results if r['success'])
print(f"Messages Sent: {success_count}/{len(results)}")
print(f"Phone Number: {ADMIN_PHONE}")
print(f"Sender ID (API): PHILSMS")
print(f"App Branding: STOCKWISE (in message content)")
print("\nCheck your phone for the messages!")
print("=" * 70)

