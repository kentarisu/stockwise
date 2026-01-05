"""
Django management command to recalculate product stock based on stock additions and sales.

This command recalculates product.stock by:
1. Summing all remaining_quantity from StockAddition records
2. This gives the actual available stock

Usage:
    python manage.py recalculate_product_stock
    python manage.py recalculate_product_stock --product-id 313  # For specific product
"""

from django.core.management.base import BaseCommand
from decimal import Decimal
from core.models import Product, StockAddition
from django.db.models import Sum
from django.db import transaction


class Command(BaseCommand):
    help = 'Recalculate product stock based on stock additions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-id',
            type=int,
            help='Recalculate stock for a specific product ID',
        )

    def handle(self, *args, **options):
        product_id = options.get('product_id')
        
        if product_id:
            products = Product.objects.filter(product_id=product_id)
            if not products.exists():
                self.stdout.write(self.style.ERROR(f'Product {product_id} not found'))
                return
        else:
            products = Product.objects.all()
        
        self.stdout.write(self.style.SUCCESS('\n=== Recalculating Product Stock ===\n'))
        
        updated_count = 0
        with transaction.atomic():
            for product in products:
                # Calculate actual stock from remaining quantities in stock additions
                stock_additions = StockAddition.objects.filter(product=product)
                total_remaining = stock_additions.aggregate(
                    total=Sum('remaining_quantity')
                )['total'] or Decimal('0')
                
                old_stock = product.stock
                product.stock = total_remaining
                product.save()
                
                if old_stock != total_remaining:
                    self.stdout.write(
                        f'  {product.name} ({product.variant}) [{product.quantity_unit}]: '
                        f'{old_stock} -> {total_remaining}'
                    )
                    updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n[OK] Updated stock for {updated_count} product(s)\n'))
