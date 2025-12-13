from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random
from core.models import Product, Sale, AppUser, StockAddition
from django.db import transaction


class Command(BaseCommand):
    help = 'Generate one year of sales data for specified products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing sales data for these products before generating new data',
        )

    def handle(self, *args, **options):
        # Product specifications from user
        products_to_generate = [
            # Original products
            {'name': 'Apple', 'variant': 'Fuji', 'quantity_unit': '130'},
            {'name': 'Apple', 'variant': 'Gala', 'quantity_unit': '100'},
            {'name': 'Apple', 'variant': 'Red Delicious', 'quantity_unit': '200'},
            {'name': 'Grapes', 'variant': 'Seedless', 'quantity_unit': 'kg'},
            {'name': 'Grapes', 'variant': 'Thompson Seedless', 'quantity_unit': 'kg'},
            {'name': 'Orange', 'variant': 'Valencia', 'quantity_unit': '72'},
            {'name': 'Orange', 'variant': 'Kiat-Kiat', 'quantity_unit': '10'},
            {'name': 'Watermelon', 'variant': 'Sugar Baby', 'quantity_unit': 'kg'},
            {'name': 'Watermelon', 'variant': 'Sweet Gold', 'quantity_unit': 'kg'},
            {'name': 'Strawberry', 'variant': 'Sweet Charlie', 'quantity_unit': 'kg'},
            # Additional Apple (Fuji) sizes
            {'name': 'Apple', 'variant': 'Fuji', 'quantity_unit': '50'},
            {'name': 'Apple', 'variant': 'Fuji', 'quantity_unit': '68'},
            {'name': 'Apple', 'variant': 'Fuji', 'quantity_unit': '72'},
            # Additional Apple (Gala) sizes
            {'name': 'Apple', 'variant': 'Gala', 'quantity_unit': '42'},
            {'name': 'Apple', 'variant': 'Gala', 'quantity_unit': '50'},
            {'name': 'Apple', 'variant': 'Gala', 'quantity_unit': '60'},
            # Additional Apple (Red Delicious) sizes
            {'name': 'Apple', 'variant': 'Red Delicious', 'quantity_unit': '95'},
            {'name': 'Apple', 'variant': 'Red Delicious', 'quantity_unit': '100'},
            {'name': 'Apple', 'variant': 'Red Delicious', 'quantity_unit': '113'},
        ]

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

        # Start date: November 1, 2024
        # End date: November 30, 2025 (one full year)
        start_date = datetime(2024, 11, 1)
        end_date = datetime(2025, 11, 30)

        with transaction.atomic():
            # Clear existing sales if requested
            if options['clear_existing']:
                for product_spec in products_to_generate:
                    products = Product.objects.filter(
                        name=product_spec['name'],
                        variant=product_spec['variant']
                    )
                    for product in products:
                        Sale.objects.filter(product=product).delete()
                        self.stdout.write(f'Cleared existing sales for {product.name} ({product.variant})')

            # Process each product
            for product_spec in products_to_generate:
                # Find or create product - include quantity_unit in lookup to avoid duplicates
                try:
                    product = Product.objects.get(
                        name=product_spec['name'],
                        variant=product_spec['variant'],
                        quantity_unit=product_spec['quantity_unit'],
                        status='active'
                    )
                    created = False
                except Product.DoesNotExist:
                    # Create new product if it doesn't exist
                    product = Product.objects.create(
                        name=product_spec['name'],
                        variant=product_spec['variant'],
                        quantity_unit=product_spec['quantity_unit'],
                        price=Decimal(str(random.uniform(50, 200))),
                        cost=Decimal(str(random.uniform(30, 150))),
                        stock=Decimal('1000'),
                        status='active',
                    )
                    created = True
                except Product.MultipleObjectsReturned:
                    # If multiple exist, use the first active one
                    product = Product.objects.filter(
                        name=product_spec['name'],
                        variant=product_spec['variant'],
                        quantity_unit=product_spec['quantity_unit'],
                        status='active'
                    ).first()
                    if product is None:
                        # If no active one, create new
                        product = Product.objects.create(
                            name=product_spec['name'],
                            variant=product_spec['variant'],
                            quantity_unit=product_spec['quantity_unit'],
                            price=Decimal(str(random.uniform(50, 200))),
                            cost=Decimal(str(random.uniform(30, 150))),
                            stock=Decimal('1000'),
                            status='active',
                        )
                        created = True
                    else:
                        created = False

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created product: {product.name} ({product.variant})'))
                else:
                    self.stdout.write(f'Found existing product: {product.name} ({product.variant})')

                # Generate sales data for one year
                current_date = start_date
                sales_count = 0
                transaction_counter = 1

                # Base daily sales rate (varies by product type)
                base_daily_sales = {
                    'Apple': {'min': 2, 'max': 8},
                    'Grapes': {'min': 1, 'max': 5},
                    'Orange': {'min': 3, 'max': 10},
                    'Watermelon': {'min': 1, 'max': 4},
                    'Strawberry': {'min': 1, 'max': 6},
                }

                # Seasonal multipliers (higher in summer, lower in winter)
                def seasonal_multiplier(date):
                    month = date.month
                    # Summer months (May-August): 1.2-1.5x
                    # Winter months (Nov-Feb): 0.7-0.9x
                    if month in [5, 6, 7, 8]:
                        return random.uniform(1.2, 1.5)
                    elif month in [11, 12, 1, 2]:
                        return random.uniform(0.7, 0.9)
                    else:
                        return random.uniform(0.9, 1.1)

                # Price variation over time (simulate market changes)
                base_price = float(product.price)
                price_history = []

                while current_date <= end_date:
                    # Calculate daily sales with seasonality
                    base_range = base_daily_sales.get(product.name, {'min': 1, 'max': 5})
                    seasonal = seasonal_multiplier(current_date)
                    daily_sales = max(0, int(random.uniform(
                        base_range['min'] * seasonal,
                        base_range['max'] * seasonal
                    )))

                    # Simulate price changes (gradual changes over time)
                    if len(price_history) == 0:
                        current_price = base_price
                    else:
                        # Price can change by up to 5% per month
                        price_change = random.uniform(-0.05, 0.05)
                        current_price = price_history[-1] * (1 + price_change)
                        # Ensure price doesn't go below cost
                        current_price = max(float(product.cost) * 1.1, current_price)

                    price_history.append(current_price)

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

                        # Price with small variations (customer negotiations, discounts)
                        sale_price = Decimal(str(round(current_price * random.uniform(0.95, 1.05), 2)))
                        total = sale_price * quantity

                        # Create sale record
                        Sale.objects.create(
                            product=product,
                            quantity=quantity,
                            price=sale_price,
                            transaction_number=f'TXN{transaction_counter:06d}',
                            or_number=f'OR{transaction_counter:06d}',
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
                        sales_count += 1
                        transaction_counter += 1

                    # Move to next day
                    current_date += timedelta(days=1)

                # Update product stock based on sales
                from django.db.models import Sum
                total_sold = Sale.objects.filter(
                    product=product,
                    status='completed'
                ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')

                # Add initial stock addition if needed
                if not StockAddition.objects.filter(product=product).exists():
                    StockAddition.objects.create(
                        product=product,
                        quantity=Decimal('10000'),
                        cost=product.cost,
                        batch_id='INIT001',
                        remaining_quantity=Decimal('10000') - total_sold,
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Generated {sales_count} sales for {product.name} ({product.variant}) '
                        f'from {start_date.date()} to {end_date.date()}'
                    )
                )

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Successfully generated sales data from November 1, 2024 to November 30, 2025!'
        ))
