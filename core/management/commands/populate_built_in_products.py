from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Product
import csv
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Populate built-in products from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='fruit_master_full.csv',
            help='Path to CSV file containing built-in products'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing built-in products before populating'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        clear_existing = options['clear_existing']
        
        # If no path provided, look in project root
        if not os.path.isabs(csv_file):
            csv_file = os.path.join(settings.BASE_DIR, csv_file)
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
            return
        
        try:
            with transaction.atomic():
                if clear_existing:
                    # Clear existing built-in products
                    deleted_count = Product.objects.filter(is_built_in=True).count()
                    Product.objects.filter(is_built_in=True).delete()
                    self.stdout.write(
                        self.style.WARNING(f'Deleted {deleted_count} existing built-in products')
                    )
                
                created_count = 0
                updated_count = 0
                
                with open(csv_file, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    
                    for row in reader:
                        name = row['name'].strip()
                        variant = row['variant'].strip() if row['variant'] else ''
                        size = row['size'].strip()
                        
                        # Create full product name with variant
                        full_name = f"{name} ({variant})" if variant else name
                        
                        # Check if product already exists (built-in products only)
                        existing_products = Product.objects.filter(
                            name=full_name,
                            size=size,
                            is_built_in=True
                        )
                        
                        if existing_products.exists():
                            product = existing_products.first()
                            created = False
                        else:
                            product = Product.objects.create(
                                name=full_name,
                                variant=variant,
                                size=size,
                                is_built_in=True,
                                status='active',
                                price=0,  # Will be set when added to inventory
                                cost=0,   # Will be set when added to inventory
                                stock=0,  # Built-in products have no stock
                            )
                            created = True
                        
                        if created:
                            created_count += 1
                        else:
                            # Update existing product to mark as built-in if not already
                            if not product.is_built_in:
                                product.is_built_in = True
                                product.save()
                                updated_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully processed built-in products:\n'
                        f'  - Created: {created_count}\n'
                        f'  - Updated: {updated_count}\n'
                        f'  - Total built-in products: {Product.objects.filter(is_built_in=True).count()}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error populating built-in products: {str(e)}')
            )
