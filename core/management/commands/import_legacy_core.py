import json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Product, StockAddition, Sale, AppUser


class Command(BaseCommand):
    help = "Import legacy core data JSON (fixture-like) into current schema. Users are skipped."

    def add_arguments(self, parser):
        parser.add_argument('json_path', help='Path to backups/core_YYYYMMDD_HHMMSS.json')

    def handle(self, *args, **options):
        path = options['json_path']
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Group by model
        by_model = {}
        for obj in data:
            by_model.setdefault(obj['model'], []).append(obj)

        imported_counts = {'products': 0, 'stock_additions': 0, 'sales': 0}

        with transaction.atomic():
            # Products
            for obj in by_model.get('core.product', []):
                fields = obj['fields']
                # Map to new schema
                product, _ = Product.objects.update_or_create(
                    product_id=obj['pk'],
                    defaults={
                        'name': fields.get('name', ''),
                        'status': (fields.get('status') or 'Active').lower(),
                        'image': fields.get('image') or '',
                        'date_added': fields.get('date_added') or timezone.now().date(),
                        'price': fields.get('price') or 0,
                        'cost': fields.get('cost') or 0,
                        'size': fields.get('size') or '',
                        'low_stock_threshold': 10,
                        'stock': 0,
                        'qr_code': b''
                    }
                )
                imported_counts['products'] += 1

            # Stock additions
            for obj in by_model.get('core.stockaddition', []):
                fields = obj['fields']
                try:
                    product_id = fields.get('product')
                    if not Product.objects.filter(product_id=product_id).exists():
                        continue
                    StockAddition.objects.update_or_create(
                        addition_id=obj['pk'],
                        defaults={
                            'product_id': product_id,
                            'quantity': fields.get('quantity') or 0,
                            'date_added': fields.get('date_added') or timezone.now(),
                            'remaining_quantity': fields.get('remaining_quantity') or 0,
                            'cost': 0,
                            'batch_id': (fields.get('batch_id') or '')[:10],
                        }
                    )
                    imported_counts['stock_additions'] += 1
                except Exception:
                    continue

            # Sales and sale items (legacy models)
            legacy_sales = {obj['pk']: obj for obj in by_model.get('core.sale', [])}
            legacy_items = by_model.get('core.saleitem', [])
            for item in legacy_items:
                f = item['fields']
                sale_pk = f.get('sale')
                sale_obj = legacy_sales.get(sale_pk)
                if not sale_obj:
                    continue
                sf = sale_obj['fields']
                product_id = f.get('product')
                if not Product.objects.filter(product_id=product_id).exists():
                    continue
                # Map to one-row-per-line sale
                Sale.objects.update_or_create(
                    sale_id=item['pk'],
                    defaults={
                        'product_id': product_id,
                        'quantity': f.get('quantity') or 0,
                        'price': Product.objects.get(product_id=product_id).price,
                        'or_number': sf.get('or_number') or '',
                        'customer_name': '',
                        'address': '',
                        'contact_number': 0,
                        'recorded_at': sf.get('recorded_at') or timezone.now(),
                        'total': (Product.objects.get(product_id=product_id).price or 0) * (f.get('quantity') or 0),
                        'amount_paid': sf.get('amount_paid'),
                        'change_given': sf.get('change_given'),
                        'status': (sf.get('status') or 'Completed').lower(),
                        'user': None,
                        'voided_at': sf.get('voided_at'),
                        'stock_restored': sf.get('stock_restored') or False,
                    }
                )
                imported_counts['sales'] += 1

        self.stdout.write(self.style.SUCCESS(f"Imported: products={imported_counts['products']}, stock_additions={imported_counts['stock_additions']}, sales={imported_counts['sales']}"))



