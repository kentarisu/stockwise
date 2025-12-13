from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from core.models import Product


class Command(BaseCommand):
    help = 'Add new Apple product variants to inventory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing products if they already exist',
        )

    def handle(self, *args, **options):
        # Product specifications to add
        products_to_add = [
            # Apple (Fuji) sizes
            {'name': 'Apple', 'variant': 'Fuji', 'quantity_unit': '50', 'base_price': 45.00, 'base_cost': 30.00},
            {'name': 'Apple', 'variant': 'Fuji', 'quantity_unit': '68', 'base_price': 55.00, 'base_cost': 38.00},
            {'name': 'Apple', 'variant': 'Fuji', 'quantity_unit': '72', 'base_price': 58.00, 'base_cost': 40.00},
            # Apple (Gala) sizes
            {'name': 'Apple', 'variant': 'Gala', 'quantity_unit': '42', 'base_price': 40.00, 'base_cost': 28.00},
            {'name': 'Apple', 'variant': 'Gala', 'quantity_unit': '50', 'base_price': 48.00, 'base_cost': 32.00},
            {'name': 'Apple', 'variant': 'Gala', 'quantity_unit': '60', 'base_price': 52.00, 'base_cost': 35.00},
            # Apple (Red Delicious) sizes
            {'name': 'Apple', 'variant': 'Red Delicious', 'quantity_unit': '95', 'base_price': 65.00, 'base_cost': 45.00},
            {'name': 'Apple', 'variant': 'Red Delicious', 'quantity_unit': '100', 'base_price': 68.00, 'base_cost': 47.00},
            {'name': 'Apple', 'variant': 'Red Delicious', 'quantity_unit': '113', 'base_price': 72.00, 'base_cost': 50.00},
        ]

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for product_spec in products_to_add:
            try:
                # Try to get existing product
                product = Product.objects.get(
                    name=product_spec['name'],
                    variant=product_spec['variant'],
                    quantity_unit=product_spec['quantity_unit']
                )
                
                # Product exists
                if options['update_existing']:
                    # Update existing product
                    product.price = Decimal(str(product_spec['base_price']))
                    product.cost = Decimal(str(product_spec['base_cost']))
                    product.status = 'active'
                    if product.stock == 0:
                        product.stock = Decimal('1000')  # Set initial stock if zero
                    product.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Updated: {product.name} ({product.variant}) ({product.quantity_unit})'
                        )
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        f'Skipped (exists): {product.name} ({product.variant}) ({product.quantity_unit})'
                    )
                    
            except Product.DoesNotExist:
                # Create new product
                product = Product.objects.create(
                    name=product_spec['name'],
                    variant=product_spec['variant'],
                    quantity_unit=product_spec['quantity_unit'],
                    price=Decimal(str(product_spec['base_price'])),
                    cost=Decimal(str(product_spec['base_cost'])),
                    stock=Decimal('1000'),
                    status='active',
                    low_stock_threshold=10,
                    date_added=timezone.now().date(),
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created: {product.name} ({product.variant}) ({product.quantity_unit}) - '
                        f'Price: ₱{product.price}, Cost: ₱{product.cost}, Stock: {product.stock}'
                    )
                )
            except Product.MultipleObjectsReturned:
                # Multiple products exist - use first active one
                product = Product.objects.filter(
                    name=product_spec['name'],
                    variant=product_spec['variant'],
                    quantity_unit=product_spec['quantity_unit'],
                    status='active'
                ).first()
                
                if product:
                    if options['update_existing']:
                        product.price = Decimal(str(product_spec['base_price']))
                        product.cost = Decimal(str(product_spec['base_cost']))
                        product.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'Updated (multiple found): {product.name} ({product.variant}) ({product.quantity_unit})'
                            )
                        )
                    else:
                        skipped_count += 1
                        self.stdout.write(
                            f'Skipped (multiple exist): {product.name} ({product.variant}) ({product.quantity_unit})'
                        )
                else:
                    # No active product found, create new one
                    product = Product.objects.create(
                        name=product_spec['name'],
                        variant=product_spec['variant'],
                        quantity_unit=product_spec['quantity_unit'],
                        price=Decimal(str(product_spec['base_price'])),
                        cost=Decimal(str(product_spec['base_cost'])),
                        stock=Decimal('1000'),
                        status='active',
                        low_stock_threshold=10,
                        date_added=timezone.now().date(),
                    )
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created (after multiple check): {product.name} ({product.variant}) ({product.quantity_unit})'
                        )
                    )

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(self.style.SUCCESS(f'  Created: {created_count} products'))
        if options['update_existing']:
            self.stdout.write(self.style.WARNING(f'  Updated: {updated_count} products'))
        if skipped_count > 0:
            self.stdout.write(f'  Skipped: {skipped_count} products (already exist)')
        self.stdout.write(self.style.SUCCESS('='*60))
