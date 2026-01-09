import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise_py.settings')
django.setup()

from core.models import Product, StockAddition
from django.db.models import Sum

products = Product.objects.filter(status='active')
print(f"{'ID':<6} | {'Name':<30} | {'P.Stock':<10} | {'BatchSum':<10} | {'Diff':<10}")
print("-" * 75)
for p in products:
    batch_sum = StockAddition.objects.filter(product_id=p.product_id).aggregate(s=Sum("remaining_quantity"))["s"] or 0
    diff = p.stock - batch_sum
    if diff != 0:
        print(f"{p.product_id:<6} | {p.name[:30]:<30} | {p.stock:<10} | {batch_sum:<10} | {diff:<10}")
