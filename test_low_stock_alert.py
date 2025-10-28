"""
Test script to manually trigger low stock alerts
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise_py.settings')
django.setup()

from core.models import Product, AppUser
from core.signals import send_low_stock_alert

print("=" * 70)
print("STOCKWISE Low Stock Alert Test")
print("=" * 70)

# Get all low stock products (status is case-sensitive: 'Active' not 'active')
low_stock = Product.objects.filter(stock__lte=10, stock__gt=0, status='Active').order_by('stock')
out_of_stock = Product.objects.filter(stock=0, status='Active').order_by('name')

print(f"\nFound {low_stock.count()} low stock products (<=10 boxes)")
print(f"Found {out_of_stock.count()} out of stock products\n")

if not low_stock.exists() and not out_of_stock.exists():
    print("All products have sufficient stock!")
else:
    # Show products
    if out_of_stock.exists():
        print("OUT OF STOCK:")
        for p in out_of_stock:
            print(f"  - {p.name} ({p.size}): {p.stock} boxes")
    
    if low_stock.exists():
        print("\nLOW STOCK (<=10 boxes):")
        for p in low_stock:
            print(f"  - {p.name} ({p.size}): {p.stock} boxes")
    
    # Check admin phone
    print("\n" + "=" * 70)
    admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
    print(f"Found {admins.count()} admin(s) with phone numbers:")
    for admin in admins:
        print(f"  - {admin.username}: {admin.phone_number}")
    
    if not admins.exists():
        print("\nERROR: No admin phone numbers configured!")
        print("   Please add phone number in profile settings.")
    else:
        # Send alerts
        print("\n" + "=" * 70)
        print("Sending low stock alerts...\n")
        
        sent_count = 0
        all_products = list(out_of_stock) + list(low_stock)
        
        for product in all_products[:3]:  # Send top 3 only to avoid spam
            print(f"Sending alert for: {product.name} ({product.size}) - {product.stock} boxes")
            try:
                send_low_stock_alert(product)
                sent_count += 1
                print(f"  Alert sent!\n")
            except Exception as e:
                print(f"  Error: {str(e)}\n")
        
        print("=" * 70)
        print(f"Sent {sent_count} low stock alert(s)!")
        print("Check your phone for SMS messages.")
        print("=" * 70)

