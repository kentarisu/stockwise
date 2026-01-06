"""
Add sales for today's date with realistic data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, time
from decimal import Decimal
import random
from core.models import Product, Sale, AppUser
from core.views import deduct_stock_fifo


def round_to_5(value):
    """Round to nearest 5"""
    return round(value / 5) * 5


def random_time_today():
    """Generate a random time for today during business hours"""
    today = timezone.now().date()
    hour = random.randint(8, 18)  # Business hours 8 AM - 6 PM
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return timezone.make_aware(
        datetime.combine(today, time(hour=hour, minute=minute, second=second))
    )


class Command(BaseCommand):
    help = 'Add sales for today with realistic data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of sales to generate (default: 20)',
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(self.style.SUCCESS(f'Adding {count} sales for today...'))
        
        # Get all active products with stock
        products = list(Product.objects.filter(status='active', stock__gt=0))
        if not products:
            self.stdout.write(self.style.ERROR('No products with stock found!'))
            return
        
        # Get admin user
        try:
            admin_user = AppUser.objects.filter(role='Admin').first()
            if not admin_user:
                admin_user = AppUser.objects.first()
        except:
            admin_user = None
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('No users found!'))
            return
        
        sales_created = 0
        
        for _ in range(count):
            # Pick a random product with stock
            available_products = [p for p in products if p.stock > 0]
            if not available_products:
                break
            
            product = random.choice(available_products)
            
            # Generate transaction number
            transaction_number = f"TXN{random.randint(100000, 999999)}"
            
            # Random customer
            customer = 'N/A' if random.random() > 0.3 else ''
            
            # Determine quantity
            is_kg = (product.quantity_unit or '').lower() == 'kg'
            if is_kg:
                max_qty = min(int(product.stock), random.randint(1, 5))
                quantity = round(random.uniform(1.0, max(1.0, max_qty)), 2)
            else:
                max_qty = min(int(product.stock), random.randint(1, 15))
                quantity = random.randint(1, max_qty)
            
            if quantity <= 0:
                continue
            
            # Use current price (rounded to 5)
            current_price = float(product.price)
            sale_price = max(5.0, round_to_5(current_price))
            
            # Calculate total
            total = Decimal(str(quantity)) * Decimal(str(int(sale_price)))
            
            try:
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
                    user=admin_user,
                    recorded_at=random_time_today(),
                    status='completed'
                )
                
                # Deduct stock using FIFO
                try:
                    deduct_stock_fifo(product.product_id, quantity)
                    product.refresh_from_db(fields=['stock'])
                except Exception as e:
                    # Fallback to simple deduction
                    product.stock = max(Decimal('0'), product.stock - Decimal(str(quantity)))
                    product.save(update_fields=['stock'])
                
                sales_created += 1
                
            except Exception as e:
                self.stdout.write(f'Error creating sale: {str(e)}')
                continue
        
        self.stdout.write(self.style.SUCCESS(
            f'[OK] Created {sales_created} sales for today!'
        ))

