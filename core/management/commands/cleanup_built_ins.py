import os
import csv
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Product


class Command(BaseCommand):
    help = (
        "Mark existing Product rows that match the built-in CSV as built-ins (is_built_in=True) "
        "and not inventory (is_inventory=False). Optionally delete them with --delete."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete', action='store_true', help='Delete matched built-in rows instead of marking')
        parser.add_argument(
            '--csv', type=str, default='fruit_master_full.csv', help='Path to CSV relative to BASE_DIR')

    def handle(self, *args, **options):
        csv_rel = options['csv']
        delete_rows = options['delete']
        csv_path = os.path.join(settings.BASE_DIR, csv_rel)
        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f'CSV not found: {csv_path}'))
            return

        # Collect base names from CSV
        base_names = set()
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_l = {k.lower(): (v or '').strip() for k, v in row.items()}
                base = row_l.get('name') or row_l.get('fruit') or row_l.get('product') or ''
                if not base:
                    continue
                if '(' in base and ')' in base:
                    try:
                        base = base.split('(')[0].strip()
                    except Exception:
                        pass
                base_names.add(base.lower())

        if not base_names:
            self.stdout.write(self.style.WARNING('No names found in CSV. Nothing to do.'))
            self.stdout.write('Cleanup completed')
            return

        matched = Product.objects.filter(name__isnull=False)
        will_update = []
        for p in matched:
            base = p.name
            if '(' in base and ')' in base:
                try:
                    base = base.split('(')[0].strip()
                except Exception:
                    pass
            if base.lower() in base_names:
                will_update.append(p.product_id)

        if not will_update:
            self.stdout.write(self.style.SUCCESS('No matching rows found.'))
            self.stdout.write('Cleanup completed')
            return

        if delete_rows:
            deleted_count, _ = Product.objects.filter(product_id__in=will_update).delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} built-in rows.'))
        else:
            # Mark as built-in and not inventory
            updated = Product.objects.filter(product_id__in=will_update).update(
                is_built_in=True,
                **({'is_inventory': False} if hasattr(Product, 'is_inventory') else {})
            )
            self.stdout.write(self.style.SUCCESS(f'Updated {updated} rows as built-in.'))

        # Generic completion line for assertions
        self.stdout.write('Cleanup completed')


