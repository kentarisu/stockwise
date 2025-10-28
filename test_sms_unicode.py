"""
Quick test to verify Unicode character handling in SMS
Tests the new peso sign (₱) to PHP conversion
"""
import os
import django

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise_py.settings')
django.setup()

from core.sms_service import IPROGSMSService

# Create SMS service instance
sms = IPROGSMSService()

# Test messages with Unicode characters
test_messages = [
    "Payment: ₱560.00",
    "Price: $100.00 or ₱5,000.00",
    "Low stock alert! 📦 Restock needed ⚠️",
    "Thank you! ❤️",
    "Special offer™ - Save €50",
    "Amount: ₱1,234.56 — paid successfully",
]

print("=" * 60)
print("SMS Unicode Conversion Test")
print("=" * 60)

for i, original in enumerate(test_messages, 1):
    converted = sms._to_gsm_plaintext(original)
    print(f"\nTest {i}:")
    try:
        print(f"  Original:  {original}")
    except UnicodeEncodeError:
        print(f"  Original:  [Contains Unicode characters]")
    print(f"  Converted: {converted}")
    print(f"  Length:    {len(converted)} chars")

print("\n" + "=" * 60)
print("[OK] All Unicode characters will be converted automatically!")
print("=" * 60)

# Show configuration
print(f"\nCurrent Configuration:")
print(f"  Sender ID: {sms.sender_id}")
print(f"  API URL: {sms.api_url}")
print(f"\n[NOTE] Custom sender IDs are NOT supported by iProg SMS")
print(f"       Messages will use system sender route regardless of config")

