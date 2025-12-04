from django.core.management.base import BaseCommand
from core.models import Product


class Command(BaseCommand):
    help = 'Update all products with quantity_unit "kilo" to "kg"'

    def handle(self, *args, **options):
        # Find all products with "kilo" as quantity_unit
        products_to_update = Product.objects.filter(quantity_unit__iexact='kilo')
        count = products_to_update.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('✓ No products found with "kilo" - all good!'))
            return
        
        # Update them to "kg"
        updated = products_to_update.update(quantity_unit='kg')
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Successfully updated {updated} product(s) from "kilo" to "kg"')
        )
        
        # List the updated products
        self.stdout.write('\nUpdated products:')
        for product in Product.objects.filter(quantity_unit='kg'):
            variant = f' ({product.variant})' if product.variant else ''
            self.stdout.write(f'  - {product.name}{variant} (ID: {product.product_id})')

