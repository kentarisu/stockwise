"""
Django management command to check and optionally clean up problematic stock additions.

This command helps identify:
- Products with unusually high stock quantities
- Duplicate stock additions
- Stock additions with future dates
- Initial stock additions from data generation scripts

Usage:
    python manage.py check_stock_additions
    python manage.py check_stock_additions --fix-large  # Remove stock additions > 5000
    python manage.py check_stock_additions --fix-duplicates  # Remove duplicate batch IDs
    python manage.py check_stock_additions --fix-future  # Fix future dates
    python manage.py check_stock_additions --fix-all  # Apply all fixes
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from core.models import Product, StockAddition
from django.db.models import Sum, Count
from django.db import transaction


class Command(BaseCommand):
    help = 'Check and optionally fix problematic stock additions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-large',
            action='store_true',
            help='Remove stock additions with quantity > 5000',
        )
        parser.add_argument(
            '--fix-duplicates',
            action='store_true',
            help='Remove duplicate batch IDs for the same product on the same date',
        )
        parser.add_argument(
            '--fix-future',
            action='store_true',
            help='Fix stock additions with future dates (set to today)',
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Apply all fixes',
        )
        parser.add_argument(
            '--threshold',
            type=int,
            default=5000,
            help='Threshold for large stock additions (default: 5000)',
        )

    def handle(self, *args, **options):
        fix_large = options['fix_large'] or options['fix_all']
        fix_duplicates = options['fix_duplicates'] or options['fix_all']
        fix_future = options['fix_future'] or options['fix_all']
        threshold = options['threshold']
        
        self.stdout.write(self.style.WARNING('\n=== Stock Additions Analysis ===\n'))
        
        # 1. Check for products with unusually high total stock
        self.stdout.write(self.style.SUCCESS('1. Checking products with high total stock...'))
        products_with_high_stock = Product.objects.annotate(
            total_added=Sum('stockaddition__quantity')
        ).filter(total_added__gt=threshold).order_by('-total_added')
        
        if products_with_high_stock.exists():
            self.stdout.write(self.style.ERROR(f'   Found {products_with_high_stock.count()} products with total stock > {threshold}:'))
            for product in products_with_high_stock[:10]:  # Show top 10
                total = product.total_added or 0
                self.stdout.write(f'   - {product.name} ({product.variant}) [{product.quantity_unit}]: {total} total added')
        else:
            self.stdout.write(self.style.SUCCESS('   [OK] No products with unusually high stock'))
        
        # 2. Check for large individual stock additions
        self.stdout.write(self.style.SUCCESS('\n2. Checking large individual stock additions...'))
        large_additions = StockAddition.objects.filter(quantity__gt=threshold).order_by('-quantity')
        
        if large_additions.exists():
            self.stdout.write(self.style.ERROR(f'   Found {large_additions.count()} stock additions with quantity > {threshold}:'))
            for addition in large_additions[:10]:  # Show top 10
                self.stdout.write(
                    f'   - {addition.product.name} ({addition.product.variant}): '
                    f'{addition.quantity} boxes on {addition.date_added.date()} '
                    f'(Batch: {addition.batch_id})'
                )
            
            if fix_large:
                self.stdout.write(self.style.WARNING(f'\n   Removing {large_additions.count()} large stock additions...'))
                with transaction.atomic():
                    # Update product stock by subtracting these large additions
                    for addition in large_additions:
                        product = addition.product
                        # Only subtract if remaining_quantity is still high
                        if addition.remaining_quantity and addition.remaining_quantity > threshold:
                            product.stock = max(Decimal('0'), product.stock - addition.remaining_quantity)
                            product.save()
                    
                    deleted_count = large_additions.delete()[0]
                    self.stdout.write(self.style.SUCCESS(f'   [OK] Removed {deleted_count} large stock additions'))
        else:
            self.stdout.write(self.style.SUCCESS('   [OK] No large individual stock additions found'))
        
        # 3. Check for duplicate batch IDs
        self.stdout.write(self.style.SUCCESS('\n3. Checking for duplicate batch IDs...'))
        from django.db.models import Count
        duplicates = StockAddition.objects.values('product', 'batch_id', 'date_added').annotate(
            count=Count('addition_id')
        ).filter(count__gt=1)
        
        if duplicates.exists():
            self.stdout.write(self.style.ERROR(f'   Found {duplicates.count()} duplicate batch ID groups:'))
            for dup in duplicates[:10]:
                product = Product.objects.get(product_id=dup['product'])
                additions = StockAddition.objects.filter(
                    product_id=dup['product'],
                    batch_id=dup['batch_id'],
                    date_added=dup['date_added']
                )
                self.stdout.write(
                    f'   - {product.name} ({product.variant}): '
                    f'Batch {dup["batch_id"]} on {dup["date_added"]} '
                    f'({additions.count()} duplicates)'
                )
            
            if fix_duplicates:
                self.stdout.write(self.style.WARNING('\n   Removing duplicate stock additions...'))
                with transaction.atomic():
                    deleted_count = 0
                    for dup in duplicates:
                        additions = list(StockAddition.objects.filter(
                            product_id=dup['product'],
                            batch_id=dup['batch_id'],
                            date_added=dup['date_added']
                        ).order_by('addition_id'))
                        
                        # Keep the first one, delete the rest
                        if len(additions) > 1:
                            to_delete = additions[1:]
                            for addition in to_delete:
                                # Update product stock
                                product = addition.product
                                if addition.remaining_quantity:
                                    product.stock = max(Decimal('0'), product.stock - addition.remaining_quantity)
                                    product.save()
                            
                            # Delete each one individually
                            for addition in to_delete:
                                addition.delete()
                                deleted_count += 1
                    
                    self.stdout.write(self.style.SUCCESS(f'   [OK] Removed {deleted_count} duplicate stock additions'))
        else:
            self.stdout.write(self.style.SUCCESS('   [OK] No duplicate batch IDs found'))
        
        # 4. Check for future dates
        self.stdout.write(self.style.SUCCESS('\n4. Checking for stock additions with future dates...'))
        today = timezone.now().date()
        future_additions = StockAddition.objects.filter(date_added__date__gt=today)
        
        if future_additions.exists():
            self.stdout.write(self.style.ERROR(f'   Found {future_additions.count()} stock additions with future dates:'))
            for addition in future_additions[:10]:
                self.stdout.write(
                    f'   - {addition.product.name} ({addition.product.variant}): '
                    f'{addition.quantity} boxes on {addition.date_added.date()} '
                    f'(should be {today})'
                )
            
            if fix_future:
                self.stdout.write(self.style.WARNING('\n   Fixing future dates...'))
                with transaction.atomic():
                    updated_count = future_additions.update(date_added=timezone.now())
                    self.stdout.write(self.style.SUCCESS(f'   [OK] Fixed {updated_count} stock additions with future dates'))
        else:
            self.stdout.write(self.style.SUCCESS('   [OK] No stock additions with future dates'))
        
        # 5. Check for INIT batch IDs (from data generation)
        self.stdout.write(self.style.SUCCESS('\n5. Checking for INIT batch IDs (from data generation)...'))
        init_additions = StockAddition.objects.filter(batch_id__startswith='INIT')
        
        if init_additions.exists():
            self.stdout.write(self.style.WARNING(f'   Found {init_additions.count()} stock additions with INIT batch IDs'))
            total_init_quantity = sum(float(a.quantity) for a in init_additions)
            self.stdout.write(f'   Total quantity from INIT additions: {total_init_quantity}')
            
            if fix_large:
                self.stdout.write(self.style.WARNING('\n   These INIT additions are likely from data generation scripts.'))
                self.stdout.write(self.style.WARNING('   Consider reviewing and removing them if they are test data.'))
        
        self.stdout.write(self.style.SUCCESS('\n=== Analysis Complete ===\n'))
        
        if not (fix_large or fix_duplicates or fix_future):
            self.stdout.write(self.style.WARNING(
                'No fixes applied. Use --fix-large, --fix-duplicates, --fix-future, or --fix-all to apply fixes.'
            ))
