"""
Verify that sales data is intact after stock addition cleanup.
"""

from django.core.management.base import BaseCommand
from core.models import Sale, StockAddition, Product
from django.db.models import Sum, Count
from datetime import datetime


class Command(BaseCommand):
    help = 'Verify sales data integrity'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== Sales Data Verification ===\n'))
        
        # Count sales
        total_sales = Sale.objects.count()
        completed_sales = Sale.objects.filter(status='completed').count()
        voided_sales = Sale.objects.filter(status='voided').count()
        
        self.stdout.write(f'Total Sales Records: {total_sales}')
        self.stdout.write(f'  - Completed: {completed_sales}')
        self.stdout.write(f'  - Voided: {voided_sales}')
        
        # Count stock additions
        total_additions = StockAddition.objects.count()
        self.stdout.write(f'\nTotal Stock Addition Records: {total_additions}')
        
        # Check date ranges
        if Sale.objects.exists():
            first_sale = Sale.objects.order_by('recorded_at').first()
            last_sale = Sale.objects.order_by('-recorded_at').first()
            self.stdout.write(f'\nSales Date Range:')
            self.stdout.write(f'  - First Sale: {first_sale.recorded_at}')
            self.stdout.write(f'  - Last Sale: {last_sale.recorded_at}')
        
        # Check sales by product
        self.stdout.write(f'\nSales by Product (Top 10):')
        sales_by_product = Sale.objects.filter(status='completed').values(
            'product__name', 'product__variant'
        ).annotate(
            total_quantity=Sum('quantity'),
            sale_count=Count('sale_id')
        ).order_by('-total_quantity')[:10]
        
        for item in sales_by_product:
            name = item['product__name'] or 'Unknown'
            variant = item['product__variant'] or ''
            qty = item['total_quantity'] or 0
            count = item['sale_count']
            self.stdout.write(f'  - {name} ({variant}): {qty} units in {count} sales')
        
        self.stdout.write(self.style.SUCCESS('\n[OK] Sales data verification complete\n'))
        self.stdout.write(self.style.WARNING(
            'Note: Sales are independent of StockAdditions. '
            'Removing stock additions does NOT affect sales records.'
        ))
