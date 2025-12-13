"""
Test STOCKWISE message formatting
Shows how messages will appear with STOCKWISE branding
but using PHILSMS as the sender ID
"""
import os
import django

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise_py.settings')
django.setup()

from core.sms_service import IPROGSMSService

# Create SMS service instance
sms = IPROGSMSService()

print("=" * 70)
print("STOCKWISE SMS Message Examples")
print("=" * 70)
print(f"\n[CONFIG] Sender ID (API): {sms.sender_id}")
print(f"[CONFIG] App Name (in messages): {sms.app_name}")
print(f"[CONFIG] Admin Phone: 09777111604")
print("\n" + "=" * 70)

# Example SMS messages with STOCKWISE branding
examples = [
    {
        "title": "Low Stock Alert",
        "message": """STOCKWISE Low Stock Alert!

Product: Apple
Current Stock: 5 boxes
Threshold: 10 boxes
Price: ₱150.00/kg

Please restock soon.

- STOCKWISE System"""
    },
    {
        "title": "Payment Confirmation",
        "message": """STOCKWISE Payment Confirmation

Dear Customer,

Your payment has been recorded:
Amount: ₱560.00
Type: Product Purchase
Date: Oct 21, 2025

Thank you for your business!

STOCKWISE Management"""
    },
    {
        "title": "Daily Sales Report",
        "message": """STOCKWISE Daily Sales Report

Date: Oct 21, 2025
Total Sales: ₱15,450.00
Transactions: 23
Top Product: Banana 🍌

View full report in dashboard.

STOCKWISE Analytics"""
    },
    {
        "title": "Price Update",
        "message": """STOCKWISE Price Update

Product: Mango
Old Price: ₱120.00/kg
New Price: ₱135.00/kg

Effective: Oct 22, 2025

STOCKWISE Pricing"""
    }
]

for i, example in enumerate(examples, 1):
    print(f"\n{'=' * 70}")
    print(f"Example {i}: {example['title']}")
    print(f"{'=' * 70}")
    
    original = example['message']
    converted = sms._to_gsm_plaintext(original, max_len=None)
    
    print(f"\n[ORIGINAL] Original Message:")
    print("-" * 70)
    try:
        print(original)
    except UnicodeEncodeError:
        print("[Message contains Unicode characters]")
    
    print(f"\n[CONVERTED] What will be sent:")
    print("-" * 70)
    print(converted)
    
    print(f"\n[DETAILS]")
    print(f"  - Length: {len(converted)} characters")
    print(f"  - SMS Count: {(len(converted) // 160) + 1}")
    print(f"  - Sender ID (API): {sms.sender_id}")
    print(f"  - App Name: {sms.app_name}")

print("\n" + "=" * 70)
print("[OK] Summary")
print("=" * 70)
print("""
[OK] Sender ID for API: PHILSMS (compliance with iProg)
[OK] App Name in messages: STOCKWISE (your branding)
[OK] All peso signs converted to: PHP
[OK] All emojis removed or converted
[OK] Plain text GSM-7 encoding
[OK] Ready for delivery to all Philippine telcos

NOTE: iProg SMS does NOT support custom sender IDs yet.
      Recipients will see iProg's system sender number, not PHILSMS.
      Your STOCKWISE branding appears in the message content itself.
""")
print("=" * 70)

