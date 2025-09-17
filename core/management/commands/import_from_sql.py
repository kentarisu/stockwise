from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Product, Inventory, StockAddition, AppUser, Sale, SaleItem, ReceiptPrint
from pathlib import Path
import re

class Command(BaseCommand):
	help = 'Import initial data from stockwise.sql into SQLite'

	def add_arguments(self, parser):
		parser.add_argument('--sql', type=str, default='stockwise.sql')

	def handle(self, *args, **options):
		path = Path(options['sql'])
		if not path.exists():
			self.stderr.write(f'File not found: {path}')
			return
		text = path.read_text(encoding='utf-8')

		def extract_inserts(table_name: str):
			pattern = re.compile(rf"INSERT INTO `?{table_name}`? \((.*?)\) VALUES\s*(.*?);", re.S)
			matches = pattern.findall(text)
			rows = []
			for cols_str, values_blob in matches:
				cols = [c.strip(' `') for c in cols_str.split(',')]
				for tup in re.finditer(r"\((.*?)\)\s*,?", values_blob, re.S):
					vals_str = tup.group(1)
					parts = []
					buf = ''
					in_quote = False
					for ch in vals_str:
						if ch == "'":
							in_quote = not in_quote
							buf += ch
						elif ch == ',' and not in_quote:
							parts.append(buf.strip())
							buf = ''
						else:
							buf += ch
					parts.append(buf.strip())
					clean = []
					for p in parts:
						if p.upper() == 'NULL':
							clean.append(None)
						elif p.startswith("'") and p.endswith("'"):
							clean.append(p[1:-1].replace("\\'", "'"))
						else:
							try:
								clean.append(int(p))
							except Exception:
								try:
									clean.append(float(p))
								except Exception:
									clean.append(p)
					rows.append(dict(zip(cols, clean)))
			return rows

		with transaction.atomic():
			for row in extract_inserts('products'):
				Product.objects.update_or_create(
					product_id=row.get('product_id'),
					defaults=dict(
						name=row.get('name', ''),
						size=row.get('size') or '',
						status=row.get('status', 'Active'),
						image=row.get('image'),
						date_added=row.get('date_added') or '2000-01-01',
						price=row.get('price') or 0,
						cost=row.get('cost') or 0,
					)
				)
			for row in extract_inserts('inventory'):
				Inventory.objects.update_or_create(
					inventory_id=row.get('inventory_id'),
					defaults=dict(
						product_id=row.get('product_id'),
						stock=row.get('stock') or 0,
					)
				)
			for row in extract_inserts('stock_additions'):
				StockAddition.objects.update_or_create(
					addition_id=row.get('addition_id'),
					defaults=dict(
						product_id=row.get('product_id'),
						quantity=row.get('quantity') or 0,
						date_added=row.get('date_added') or '2000-01-01',
						remaining_quantity=row.get('remaining_quantity') or 0,
						batch_id=row.get('batch_id') or '',
					)
				)
			for row in extract_inserts('users'):
				AppUser.objects.update_or_create(
					user_id=row.get('user_id'),
					defaults=dict(
						name=row.get('name', ''),
						username=row.get('username', ''),
						phone_number=row.get('phone_number', ''),
						password=row.get('password', ''),
						role=row.get('role', 'user'),
						is_active=bool(row.get('is_active', 1)),
						status=row.get('status', 'enabled'),
						profile_picture=row.get('profile_picture', ''),
						last_login=row.get('last_login') or '2000-01-01 00:00:00',
						last_active=row.get('last_active'),
					)
				)
			for row in extract_inserts('sales'):
				Sale.objects.update_or_create(
					sale_id=row.get('sale_id'),
					defaults=dict(
						or_number=row.get('or_number', ''),
						recorded_at=row.get('recorded_at') or '2000-01-01 00:00:00',
						total=row.get('total') or 0,
						amount_paid=row.get('amount_paid'),
						change_given=row.get('change_given'),
						status=row.get('status', 'Completed'),
						user_id=row.get('user_id'),
						voided_at=row.get('voided_at'),
						stock_restored=bool(row.get('stock_restored', 0)),
					)
				)
			for row in extract_inserts('sale_items'):
				SaleItem.objects.update_or_create(
					sale_item_id=row.get('sale_item_id'),
					defaults=dict(
						sale_id=row.get('sale_id'),
						product_id=row.get('product_id'),
						quantity=row.get('quantity') or 0,
						price=row.get('price') or 0,
					)
				)
			for row in extract_inserts('receipt_prints'):
				ReceiptPrint.objects.update_or_create(
					print_id=row.get('print_id'),
					defaults=dict(
						sale_id=row.get('sale_id'),
						user_id=row.get('user_id'),
					)
				)
		self.stdout.write(self.style.SUCCESS('Import completed.')) 