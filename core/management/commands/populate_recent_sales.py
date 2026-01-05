"""
Django management command to populate recent sales data to ensure demand ratio is not 0.00x.

This command adds sales data for the last 30 days to ensure the demand ratio calculation
has sufficient data in both the recent (7-day) and older (23-day) periods.

Usage:
    python manage.py populate_recent_sales
    python manage.py populate_recent_sales --days 30
    python manage.py populate_recent_sales --clear-recent
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random
from core.models import Product, Sale, AppUser
from django.db import transaction


class Command(BaseCommand):
    help = 'Populate recent sales data to ensure demand ratio calculation has data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of recent days to populate (default: 30)',
        )
        parser.add_argument(
            '--clear-recent',
            action='store_true',
            help='Clear existing sales in the recent period before populating',
        )
        parser.add_argument(
            '--min-daily',
            type=int,
            default=1,
            help='Minimum sales per day (default: 1)',
        )

    def handle(self, *args, **options):
        days = options['days']
        clear_recent = options['clear_recent']
        min_daily = options['min_daily']
        
        # Get or create admin user
        admin_user = AppUser.objects.filter(role='Admin').first()
        if not admin_user:
            admin_user = AppUser.objects.create(
                username='admin',
                password='admin123',
                phone_number='000',
                role='Admin'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user for sales data'))

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all active products
        products = Product.objects.filter(status='active')
        
        if not products.exists():
            self.stdout.write(self.style.ERROR('No active products found'))
            return
        
        # Base daily sales rate (varies by product type)
        base_daily_sales = {
            'Apple': {'min': 2, 'max': 8},
            'Grapes': {'min': 1, 'max': 5},
            'Orange': {'min': 3, 'max': 10},
            'Watermelon': {'min': 1, 'max': 4},
            'Strawberry': {'min': 1, 'max': 6},
        }
        
        # Seasonal multipliers
        def seasonal_multiplier(date):
            month = date.month
            if month in [5, 6, 7, 8]:
                return random.uniform(1.2, 1.5)
            elif month in [11, 12, 1, 2]:
                return random.uniform(0.7, 0.9)
            else:
                return random.uniform(0.9, 1.1)
        
        total_sales_added = 0
        
        with transaction.atomic():
            for product in products:
                # Clear recent sales if requested
                if clear_recent:
                    deleted = Sale.objects.filter(
                        product=product,
                        recorded_at__gte=start_date,
                        recorded_at__lte=end_date
                    ).delete()
                    if deleted[0] > 0:
                        self.stdout.write(f'Cleared {deleted[0]} existing sales for {product.name} ({product.variant})')
                
                # Generate sales for each day
                current_date = start_date
                transaction_counter = 1
                product_sales_count = 0
                
                # Get existing transaction numbers to avoid duplicates
                existing_txns = set(
                    Sale.objects.values_list('transaction_number', flat=True)
                )
                
                while current_date <= end_date:
                    # Calculate daily sales with seasonality
                    base_range = base_daily_sales.get(product.name, {'min': 1, 'max': 5})
                    seasonal = seasonal_multiplier(current_date)
                    
                    # Calculate base daily sales
                    daily_sales = max(0, int(random.uniform(
                        base_range['min'] * seasonal,
                        base_range['max'] * seasonal
                    )))
                    
                    # Ensure minimum sales for recent days
                    days_from_end = (end_date.date() - current_date.date()).days
                    if days_from_end <= 7:
                        # Last 7 days: ensure at least min_daily sales
                        daily_sales = max(min_daily, daily_sales)
                    elif days_from_end <= 30:
                        # Days 8-30: ensure at least 1 sale (50% chance if calculated as 0)
                        if daily_sales == 0 and random.random() < 0.5:
                            daily_sales = 1
                    
                    # Generate sales for this day
                    for sale_num in range(daily_sales):
                        # Random time during business hours (8 AM - 8 PM)
                        hour = random.randint(8, 20)
                        minute = random.randint(0, 59)
                        sale_time = current_date.replace(hour=hour, minute=minute)
                        
                        # Quantity varies by product type
                        if product.quantity_unit == 'kg':
                            quantity = Decimal(str(round(random.uniform(0.5, 5.0), 2)))
                        else:
                            quantity = Decimal(str(random.randint(1, 3)))
                        
                        # Price with small variations
                        base_price = float(product.price)
                        sale_price = Decimal(str(round(base_price * random.uniform(0.95, 1.05), 2)))
                        total = sale_price * quantity
                        
                        # Generate unique transaction number
                        while True:
                            txn_num = f'TXN{transaction_counter:06d}'
                            if txn_num not in existing_txns:
                                existing_txns.add(txn_num)
                                break
                            transaction_counter += 1
                        
                        or_num = f'OR{transaction_counter:06d}'
                        
                        # Create sale record
                        Sale.objects.create(
                            product=product,
                            quantity=quantity,
                            price=sale_price,
                            transaction_number=txn_num,
                            or_number=or_num,
                            customer_name=f'Customer{random.randint(1, 100)}',
                            address='',
                            contact_number='',
                            recorded_at=sale_time,
                            total=total,
                            amount_paid=total,
                            change_given=Decimal('0'),
                            status='completed',
                            user=admin_user,
                        )
                        product_sales_count += 1
                        transaction_counter += 1
                    
                    # Move to next day
                    current_date += timedelta(days=1)
                
                total_sales_added += product_sales_count
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Added {product_sales_count} sales for {product.name} ({product.variant}) '
                        f'from {start_date.date()} to {end_date.date()}'
                    )
                )
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Successfully added {total_sales_added} sales records for recent {days} days!'
        ))
        self.stdout.write(
            self.style.WARNING(
                f'\nNote: Recent 7 days have minimum {min_daily} sales per day to ensure demand ratio is not 0.00x'
            )
        )

