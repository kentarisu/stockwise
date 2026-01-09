"""
Django management command to record sales for orphaned stock batches.

This command finds stock batches that have remaining stock but are older than newer
batches that are sold out (violating FIFO), and creates sales records with dates
that match the batch dates to fix the FIFO violation.

Usage:
    python manage.py record_orphaned_stock_sales
    python manage.py record_orphaned_stock_sales --product-id 309
    python manage.py record_orphaned_stock_sales --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random
from core.models import Product, Sale, AppUser, StockAddition
from core.views import deduct_stock_fifo, calculate_fifo_pricing
from django.db.models import Min, Max, Q


def random_time_for_date(date_obj):
    """Generate a random time for a specific date during business hours"""
    hour = random.randint(8, 18)  # Business hours 8 AM - 6 PM
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return timezone.make_aware(
        datetime.combine(date_obj, datetime.min.time().replace(hour=hour, minute=minute, second=second))
    )


class Command(BaseCommand):
    help = 'Record sales for orphaned stock batches with dates matching batch dates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-id',
            type=int,
            default=None,
            help='Process only a specific product ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes',
        )

    def handle(self, *args, **options):
        product_id = options.get('product_id')
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made\n'))
        
        # Get admin user for sales
        try:
            admin_user = AppUser.objects.filter(role__iexact='Admin').first()
            if not admin_user:
                admin_user = AppUser.objects.first()
        except:
            admin_user = None
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('No users found!'))
            return
        
        # Find products with orphaned batches (batches with remaining stock that are older than newer sold-out batches)
        orphaned_batches = []
        
        if product_id:
            products = Product.objects.filter(product_id=product_id, status='active')
        else:
            products = Product.objects.filter(status='active')
        
        self.stdout.write(f'Checking {products.count()} product(s) for orphaned stock batches...\n')
        
        for product in products:
            # Get all batches for this product ordered by date_added (oldest first)
            all_batches = StockAddition.objects.filter(
                product_id=product.product_id
            ).order_by('date_added', 'addition_id')
            
            if not all_batches.exists():
                continue
            
            # Find batches with remaining stock
            batches_with_stock = [b for b in all_batches if b.remaining_quantity > 0]
            batches_sold_out = [b for b in all_batches if b.remaining_quantity == 0]
            
            # Check for FIFO violations: if a batch with stock has a newer sold-out batch before it
            for batch in batches_with_stock:
                # Check if there are any newer batches (by date_added) that are sold out
                newer_sold_out = [b for b in batches_sold_out 
                                if (b.date_added > batch.date_added) or 
                                   (b.date_added == batch.date_added and b.addition_id > batch.addition_id)]
                
                if newer_sold_out:
                    # This batch is orphaned - it has stock but newer batches are sold out
                    orphaned_batches.append({
                        'product': product,
                        'batch': batch,
                        'remaining_qty': batch.remaining_quantity,
                        'batch_date': batch.date_added
                    })
                    
                    # Also check if this is the oldest batch with stock
                    older_batches = [b for b in all_batches 
                                   if (b.date_added < batch.date_added) or 
                                      (b.date_added == batch.date_added and b.addition_id < batch.addition_id)]
                    older_with_stock = [b for b in older_batches if b.remaining_quantity > 0]
                    
                    if not older_with_stock:
                        # This is the oldest batch with stock - should have been sold first
                        orphaned_batches[-1]['is_oldest'] = True
        
        if not orphaned_batches:
            self.stdout.write(self.style.SUCCESS('[OK] No orphaned stock batches found!'))
            return
        
        # Sort orphaned batches by date_added (oldest first) to process in FIFO order
        orphaned_batches.sort(key=lambda x: (x['batch'].date_added, x['batch'].addition_id))
        
        self.stdout.write(self.style.WARNING(f'\n[WARNING] Found {len(orphaned_batches)} orphaned stock batches:\n'))
        
        # Display orphaned batches
        for item in orphaned_batches:
            product = item['product']
            batch = item['batch']
            variant_str = f" ({product.variant})" if product.variant else ""
            unit_str = f" ({product.quantity_unit})" if product.quantity_unit else ""
            oldest_flag = " [OLDEST - Should be sold first]" if item.get('is_oldest') else ""
            
            # Format date_added safely (could be date or datetime)
            date_str = batch.date_added.strftime('%Y-%m-%d %H:%M:%S') if isinstance(batch.date_added, datetime) else str(batch.date_added)
            self.stdout.write(
                f"  • Product ID {product.product_id}: {product.name}{variant_str}{unit_str}\n"
                f"    Batch ID: {batch.batch_id}, Date: {date_str}, "
                f"Remaining: {item['remaining_qty']}{oldest_flag}"
            )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN: Would create sales for the above batches'))
            return
        
        # Confirm before proceeding
        self.stdout.write(self.style.WARNING('\n[WARNING] This will create sales records for the above batches.'))
        confirm = input('Do you want to proceed? (yes/no): ')
        
        if confirm.lower() not in ['yes', 'y']:
            self.stdout.write(self.style.ERROR('Aborted by user.'))
            return
        
        # Create sales for orphaned batches
        sales_created = 0
        failed_count = 0
        total_qty_sold = Decimal('0')
        
        with transaction.atomic():
            for item in orphaned_batches:
                product = item['product']
                batch = item['batch']
                remaining_qty = Decimal(str(item['remaining_qty']))
                batch_date = item['batch_date']
                
                try:
                    # Convert batch_date to datetime if needed
                    if isinstance(batch_date, datetime):
                        batch_dt = batch_date
                    elif hasattr(batch_date, 'date'):  # datetime.date
                        batch_dt = timezone.make_aware(datetime.combine(batch_date, datetime.min.time()))
                    else:
                        try:
                            batch_dt = timezone.make_aware(datetime.strptime(str(batch_date), '%Y-%m-%d'))
                        except:
                            batch_dt = timezone.now()
                    
                    # Determine appropriate sale date - should be after batch date but before next batch if exists
                    # Get next newer batch date (compare directly with batch.date_added)
                    next_batch = StockAddition.objects.filter(
                        product_id=product.product_id
                    ).filter(
                        Q(date_added__gt=batch.date_added) |
                        (Q(date_added=batch.date_added) & Q(addition_id__gt=batch.addition_id))
                    ).order_by('date_added', 'addition_id').first()
                    
                    # Start with batch date + 1 day to ensure it's after the batch was added
                    if isinstance(batch_dt, datetime):
                        base_sale_date = batch_dt + timedelta(days=1)
                        base_sale_date = base_sale_date.replace(hour=random.randint(8, 18), minute=random.randint(0, 59))
                    else:
                        # If it's a date, convert to datetime
                        batch_date_only = batch_dt.date() if hasattr(batch_dt, 'date') else batch_dt
                        base_sale_date = timezone.make_aware(datetime.combine(
                            batch_date_only + timedelta(days=1), 
                            datetime.min.time().replace(hour=random.randint(8, 18), minute=random.randint(0, 59))
                        ))
                    
                    if next_batch:
                        # Sale date should be between batch_date and next_batch.date_added
                        if isinstance(next_batch.date_added, datetime):
                            next_date = next_batch.date_added
                        else:
                            next_date = timezone.make_aware(datetime.combine(next_batch.date_added, datetime.min.time()))
                        
                        # Ensure sale date is before next batch
                        if base_sale_date >= next_date:
                            # Use a date 1 day before next batch
                            sale_date = next_date - timedelta(days=1)
                            sale_date = sale_date.replace(hour=random.randint(8, 18), minute=random.randint(0, 59))
                        else:
                            # Use a random date between batch_date + 1 day and next_date - 1 day
                            time_diff = (next_date - base_sale_date).total_seconds()
                            if time_diff > 86400:  # More than 1 day apart
                                days_range = int(time_diff / 86400)
                                days_after = random.randint(0, max(0, days_range - 1))
                                sale_date = base_sale_date + timedelta(days=days_after)
                                sale_date = sale_date.replace(hour=random.randint(8, 18), minute=random.randint(0, 59))
                            else:
                                sale_date = base_sale_date
                    else:
                        # No next batch - use batch date + 1 day
                        sale_date = base_sale_date
                    
                    # Use batch price if available, otherwise product price
                    sale_price = batch.price if (batch.price and batch.price > 0) else product.price
                    
                    # Split large quantities into multiple smaller transactions for realism
                    is_kg = (product.quantity_unit or '').lower() == 'kg'
                    max_per_sale = Decimal('15') if not is_kg else Decimal('5')
                    
                    remaining_to_sell = remaining_qty
                    
                    while remaining_to_sell > 0:
                        # Determine quantity for this sale
                        if remaining_to_sell <= max_per_sale:
                            sale_qty = remaining_to_sell
                        else:
                            if is_kg:
                                sale_qty = Decimal(str(round(random.uniform(1.0, min(5.0, float(remaining_to_sell))), 2)))
                            else:
                                sale_qty = Decimal(str(random.randint(1, min(15, int(remaining_to_sell)))))
                        
                        if sale_qty <= 0:
                            break
                        
                        # Generate transaction number
                        transaction_number = f"TXN{random.randint(100000, 999999)}"
                        
                        # Calculate total
                        total = sale_qty * Decimal(str(float(sale_price)))
                        
                        # Create sale record with batch date
                        sale = Sale.objects.create(
                            product=product,
                            quantity=sale_qty,
                            price=Decimal(str(float(sale_price))),
                            total=total,
                            amount_paid=total,
                            change_given=Decimal('0'),
                            customer_name='N/A',
                            transaction_number=transaction_number,
                            user=admin_user,
                            recorded_at=sale_date,
                            status='completed'
                        )
                        
                        # Deduct stock using FIFO (this should consume from the orphaned batch)
                        # Since we're processing oldest batches first, FIFO should naturally consume from this batch
                        # Convert to Decimal for proper type handling
                        try:
                            deduct_stock_fifo(product.product_id, Decimal(str(sale_qty)))
                            product.refresh_from_db(fields=['stock'])
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'[ERROR] Failed to deduct stock for Product ID {product.product_id}, Batch {batch.batch_id}: {str(e)}'
                                )
                            )
                            sale.delete()  # Rollback the sale
                            failed_count += 1
                            break
                        
                        sales_created += 1
                        total_qty_sold += sale_qty
                        remaining_to_sell -= sale_qty
                        
                        # Move sale date forward slightly for next transaction (same day, different time)
                        if remaining_to_sell > 0:
                            sale_date = sale_date + timedelta(hours=random.randint(1, 3))
                    
                    if remaining_to_sell == 0:
                        variant_str = f" ({product.variant})" if product.variant else ""
                        unit_str = f" ({product.quantity_unit})" if product.quantity_unit else ""
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'[OK] Created sales for Product ID {product.product_id}: {product.name}{variant_str}{unit_str} - '
                                f'Batch {batch.batch_id} ({remaining_qty} units sold on {sale_date.strftime("%Y-%m-%d")})'
                            )
                        )
                
                except Exception as e:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'[ERROR] Failed to create sales for Product ID {product.product_id}, Batch {batch.batch_id}: {str(e)}'
                        )
                    )
                    import traceback
                    traceback.print_exc()
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(self.style.SUCCESS(f'  [OK] Sales created: {sales_created}'))
        self.stdout.write(self.style.SUCCESS(f'  Total quantity sold: {total_qty_sold}'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'  [ERROR] Failed: {failed_count} batches'))
        self.stdout.write(self.style.SUCCESS('='*60))
