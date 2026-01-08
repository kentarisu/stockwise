"""
Extend historical sales data backwards by adding 2 months (60 days) of data
before the oldest existing sale, using the same patterns as existing data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta, time
from decimal import Decimal
import random
from core.models import Product, Sale, StockAddition, AppUser
from core.views import generate_batch_id, deduct_stock_fifo


def round_to_5(value):
    """Round to nearest 5 (e.g., 1500, 1505, 1550)"""
    return round(value / 5) * 5


def random_time_for_date(date_obj, time_type='business'):
    """Add a random time to a date object"""
    if time_type == 'business':
        # Business hours: 8 AM - 6 PM
        hour = random.randint(8, 18)
        minute = random.randint(0, 59)
    elif time_type == 'stock':
        # Stock additions: Early morning or late afternoon (6 AM - 10 AM or 3 PM - 7 PM)
        if random.random() > 0.5:
            hour = random.randint(6, 10)  # Morning delivery
        else:
            hour = random.randint(15, 19)  # Afternoon delivery
        minute = random.randint(0, 59)
    else:
        # Any time during the day
        hour = random.randint(6, 22)
        minute = random.randint(0, 59)
    
    return timezone.make_aware(
        datetime.combine(date_obj, time(hour=hour, minute=minute, second=random.randint(0, 59)))
    )


class Command(BaseCommand):
    help = 'Extend historical sales data backwards by 60 days (2 months)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=60,
            help='Number of days to extend backwards (default: 60)',
        )

    def handle(self, *args, **options):
        days = options['days']
        self.stdout.write(self.style.SUCCESS(f'Extending historical data backwards by {days} days...'))
        
        # Get all active products
        products = list(Product.objects.filter(status='active'))
        if not products:
            self.stdout.write(self.style.ERROR('No active products found!'))
            return
        
        self.stdout.write(f'Found {len(products)} products')
        
        # Get admin user for sales
        try:
            admin_user = AppUser.objects.filter(role='Admin').first()
            if not admin_user:
                admin_user = AppUser.objects.first()
        except:
            admin_user = None
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('No users found!'))
            return
        
        # Find the oldest sale date
        oldest_sale = Sale.objects.order_by('recorded_at').first()
        if not oldest_sale:
            self.stdout.write(self.style.ERROR('No existing sales found! Use generate_historical_sales first.'))
            return
        
        # Calculate date range: go backwards from oldest sale
        end_date = oldest_sale.recorded_at - timedelta(days=1)  # Day before oldest sale
        start_date = end_date - timedelta(days=days - 1)  # Go back 'days' days
        
        self.stdout.write(f'Oldest existing sale: {oldest_sale.recorded_at.date()}')
        self.stdout.write(f'New period: {start_date.date()} to {end_date.date()}')
        
        # Store original product values to restore at the end
        original_values = {
            p.product_id: {
                'stock': p.stock,
                'price': p.price,
                'cost': p.cost
            } for p in products
        }
        
        # Store current stock levels (we'll add to them, not reset)
        current_stock = {p.product_id: p.stock for p in products}
        
        total_sales = 0
        total_stock_additions = 0
        
        # First pass: Ensure EVERY product has sales across the entire period
        # Divide the period into weekly chunks and ensure each product appears in each week
        week_duration = 7
        current_date = start_date
        
        while current_date <= end_date:
            # Ensure each product gets at least 1-2 sales this week
            week_end = min(current_date + timedelta(days=week_duration), end_date)
            
            for product in products:
                # Add stock if needed
                if product.stock <= 0:
                    self._add_stock_to_product(current_date, product)
                    total_stock_additions += 1
                
                # Generate 1-2 sales for this product this week
                num_sales = random.randint(1, 2)
                for _ in range(num_sales):
                    # Pick a random day within this week
                    days_offset = random.randint(0, min(week_duration - 1, (week_end - current_date).days))
                    sale_date = current_date + timedelta(days=days_offset)
                    
                    sales = self._generate_sales_for_product(
                        sale_date,
                        product,
                        admin_user,
                        num_items=1  # Single product transaction
                    )
                    total_sales += sales
            
            # Add some stock additions this week
            additions = self._add_stock_randomly(current_date, products)
            total_stock_additions += additions
            
            current_date = week_end + timedelta(days=1)
        
        # Second pass: Add additional random sales for variety
        current_date = start_date
        while current_date <= end_date:
            # Random additional sales
            day_sales = self._generate_day_sales(
                current_date, 
                products, 
                admin_user
            )
            total_sales += day_sales
            
            # Occasional stock additions
            if random.random() < 0.1:
                additions = self._add_stock_randomly(current_date, products)
                total_stock_additions += additions
            
            current_date += timedelta(days=1)
        
        # Restore original product prices and costs, but keep the accumulated stock
        self.stdout.write('Restoring original product prices and costs...')
        for product in products:
            orig = original_values[product.product_id]
            # Keep the stock as is (it was built up during generation)
            product.price = orig['price']
            product.cost = orig['cost']
            product.save(update_fields=['price', 'cost'])
        
        self.stdout.write(self.style.SUCCESS(
            f'[OK] Generated {total_sales} sales and {total_stock_additions} stock additions '
            f'for {days} days before existing data'
        ))

    def _add_stock_to_product(self, date, product):
        """Add stock to a specific product"""
        is_kg = (product.quantity_unit or '').lower() == 'kg'
        
        if is_kg:
            quantity = Decimal(str(round(random.uniform(20, 60), 2)))
        else:
            quantity = Decimal(str(random.randint(30, 120)))
        
        base_cost = float(product.cost)
        current_price = float(product.price)
        
        # For older dates, prices and costs should be lower (going backwards in time)
        days_from_end = (timezone.now().date() - date.date()).days
        cost_variance = 1.0 - (random.uniform(0.05, 0.15) * (days_from_end / 100))
        stock_cost = max(5.0, round_to_5(base_cost * cost_variance))
        
        price_variance = 1.0 - (random.uniform(0.03, 0.10) * (days_from_end / 100))
        stock_price = max(5.0, round_to_5(current_price * price_variance))
        
        clean_name = product.name.split('(')[0].strip()
        variant = product.variant or ''
        batch_id = generate_batch_id(product, clean_name, variant)
        
        StockAddition.objects.create(
            product=product,
            quantity=quantity,
            remaining_quantity=quantity,
            cost=Decimal(str(int(stock_cost))),
            price=Decimal(str(int(stock_price))),
            update_product_price=False,
            batch_id=batch_id,
            date_added=random_time_for_date(date, 'stock'),
            supplier='N/A'
        )
        
        product.stock = product.stock + quantity
        product.cost = Decimal(str(int(stock_cost)))
        product.save(update_fields=['stock', 'cost'])

    def _generate_sales_for_product(self, date, product, user, num_items=1, transaction_number=None):
        """Generate sales for a specific product"""
        sales_count = 0
        
        # Check if product has stock
        if product.stock <= 0:
            return 0
        
        customer = 'N/A' if random.random() > 0.3 else ''
        
        # Generate transaction number if not provided
        if not transaction_number:
            transaction_number = f"TXN{random.randint(100000, 999999)}"
        
        # Determine quantity based on product type
        is_kg = (product.quantity_unit or '').lower() == 'kg'
        if is_kg:
            max_qty = min(int(product.stock), random.randint(1, 5))
            quantity = Decimal(str(round(random.uniform(1.0, max(1.0, max_qty)), 2)))
        else:
            max_qty = min(int(product.stock), random.randint(1, 15))
            quantity = Decimal(str(random.randint(1, max_qty)))
        
        if quantity <= 0:
            return 0
        
        # Use varied historical price (earlier = lower price)
        current_price = float(product.price)
        days_from_end = (timezone.now().date() - date.date()).days
        price_variance = 1.0 - (random.uniform(0.03, 0.12) * (days_from_end / 100))
        sale_price = max(5.0, round_to_5(current_price * price_variance))
        
        total = quantity * Decimal(str(int(sale_price)))
        
        # Create sale record
        sale = Sale.objects.create(
            product=product,
            quantity=quantity,
            price=Decimal(str(int(sale_price))),
            total=total,
            amount_paid=total,
            change_given=Decimal('0'),
            customer_name=customer,
            transaction_number=transaction_number,
            user=user,
            recorded_at=random_time_for_date(date, 'business'),
            status='completed'
        )
        
        # Deduct stock using FIFO
        try:
            deduct_stock_fifo(product.product_id, float(quantity))
            product.refresh_from_db(fields=['stock'])
        except Exception as e:
            # Fallback to simple deduction if FIFO fails
            product.stock = max(Decimal('0'), product.stock - quantity)
            product.save(update_fields=['stock'])
        
        return 1

    def _generate_day_sales(self, date, products, user):
        """Generate sales for a single day with seasonal patterns"""
        # Seasonal multiplier based on date
        month = date.month
        day = date.day
        
        # Philippines seasonal patterns
        if month == 12:  # December - Christmas season
            if day < 15:
                seasonal_factor = 1.8  # Building up to Christmas
            elif day <= 25:
                seasonal_factor = 2.5  # Peak Christmas shopping
            else:
                seasonal_factor = 1.3  # Post-Christmas
        elif month == 11:  # November - Pre-Christmas
            seasonal_factor = 1.2
        elif month == 1 and day <= 7:  # New Year week
            seasonal_factor = 1.4
        else:
            seasonal_factor = 1.0
        
        # Weekend boost (Friday-Sunday)
        weekday = date.weekday()
        if weekday >= 4:  # Friday, Saturday, Sunday
            seasonal_factor *= 1.3
        
        # Base number of transactions per day
        base_transactions = random.randint(3, 8)
        num_transactions = int(base_transactions * seasonal_factor)
        
        sales_count = 0
        for _ in range(num_transactions):
            # Customer is always N/A or empty
            customer = 'N/A' if random.random() > 0.3 else ''
            
            # Generate transaction number for this transaction
            transaction_number = f"TXN{random.randint(100000, 999999)}"
            transaction_time = random_time_for_date(date, 'business')
            
            # Pick 1-3 products for this transaction
            num_items = random.choices([1, 2, 3], weights=[50, 35, 15])[0]
            selected_products = random.sample(products, min(num_items, len(products)))
            
            transaction_sales = []
            for product in selected_products:
                # Check if product has stock
                if product.stock <= 0:
                    continue
                
                # Determine quantity based on product type
                is_kg = (product.quantity_unit or '').lower() == 'kg'
                if is_kg:
                    # Kg products: minimum 1kg
                    max_qty = min(int(product.stock), random.randint(1, 5))
                    quantity = Decimal(str(round(random.uniform(1.0, max(1.0, max_qty)), 2)))
                else:
                    # Box products: larger quantities
                    max_qty = min(int(product.stock), random.randint(1, 15))
                    quantity = Decimal(str(random.randint(1, max_qty)))
                
                if quantity <= 0:
                    continue
                
                # Use varied historical price for this sale (earlier = lower price)
                current_price = float(product.price)
                days_from_end = (timezone.now().date() - date.date()).days
                
                # Earlier sales had lower prices (gradual increase over time)
                price_variance = 1.0 - (random.uniform(0.03, 0.12) * (days_from_end / 100))
                sale_price = max(5.0, round_to_5(current_price * price_variance))
                
                # Calculate total
                total = quantity * Decimal(str(int(sale_price)))
                
                # Create sale record WITH price field set
                sale = Sale.objects.create(
                    product=product,
                    quantity=quantity,
                    price=Decimal(str(int(sale_price))),  # Set unit price for graph tracking
                    total=total,
                    amount_paid=total,
                    change_given=Decimal('0'),
                    customer_name=customer,
                    transaction_number=transaction_number,
                    user=user,
                    recorded_at=transaction_time,
                    status='completed'
                )
                
                # Deduct stock using FIFO
                try:
                    deduct_stock_fifo(product.product_id, float(quantity))
                    product.refresh_from_db(fields=['stock'])
                except Exception as e:
                    # Fallback to simple deduction if FIFO fails
                    product.stock = max(Decimal('0'), product.stock - quantity)
                    product.save(update_fields=['stock'])
                
                transaction_sales.append(sale)
                sales_count += 1
        
        return sales_count

    def _add_stock_randomly(self, date, products):
        """Add stock to random products"""
        # Pick 1-5 products to restock
        num_to_restock = random.randint(1, min(5, len(products)))
        restock_products = random.sample(products, num_to_restock)
        
        additions_count = 0
        for product in restock_products:
            is_kg = (product.quantity_unit or '').lower() == 'kg'
            
            if is_kg:
                # Kg products: moderate quantities
                quantity = Decimal(str(round(random.uniform(10, 50), 2)))
            else:
                # Box products: larger batches
                quantity = Decimal(str(random.randint(20, 100)))
            
            # Historical cost with variation
            base_cost = float(product.cost)
            current_price = float(product.price)
            
            # Costs gradually increase over time (earlier = lower cost)
            days_from_end = (timezone.now().date() - date.date()).days
            cost_variance = 1.0 - (random.uniform(0.05, 0.15) * (days_from_end / 100))
            stock_cost = max(5.0, round_to_5(base_cost * cost_variance))
            
            # Price should also vary (earlier = lower price)
            price_variance = 1.0 - (random.uniform(0.03, 0.10) * (days_from_end / 100))
            stock_price = max(5.0, round_to_5(current_price * price_variance))
            
            # Generate batch ID
            clean_name = product.name.split('(')[0].strip()
            variant = product.variant or ''
            batch_id = generate_batch_id(product, clean_name, variant)
            
            # Create stock addition with price tracking
            StockAddition.objects.create(
                product=product,
                quantity=quantity,
                remaining_quantity=quantity,
                cost=Decimal(str(int(stock_cost))),
                price=Decimal(str(int(stock_price))),
                update_product_price=False,  # Don't update product price (preserve current)
                batch_id=batch_id,
                date_added=random_time_for_date(date, 'stock'),
                supplier='N/A'
            )
            
            # Update product stock and cost only (not price)
            product.stock = product.stock + quantity
            product.cost = Decimal(str(int(stock_cost)))
            product.save(update_fields=['stock', 'cost'])
            
            additions_count += 1
        
        return additions_count

