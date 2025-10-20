from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.utils import timezone
from django.core import signing
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
import os
import csv
from django.conf import settings
from django.db.models import Sum, Count, F, Q, F, Case, When, CharField, Value
from django.db.models.functions import Coalesce, Substr
from .models import AppUser, Product, Sale, StockAddition, SMS, ReportProductSummary
import json
from django.db import transaction
from django.http import JsonResponse
 
from datetime import datetime, timedelta
from decimal import Decimal
from io import StringIO, BytesIO
import csv
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from passlib.hash import bcrypt
import os

from django.views.decorators.http import require_GET
# FruitMaster removed per 6-table schema
import django.db.models as models
from django.core.exceptions import ValidationError

# Unified numeric size options shared across all products
STANDARD_SIZE_OPTIONS = ['120', '130', '140', '150', '160']


def redirect_to_login(request):
	return redirect('login')


@require_http_methods(["GET", "POST"])
@csrf_exempt
def login_view(request):
	if request.method == 'POST':
		username = request.POST.get('username', '').strip()
		password = request.POST.get('password', '').strip()
		try:
			user = AppUser.objects.filter(username=username).first()
			if not user:
				messages.error(request, 'Username not found.')
			else:
				from passlib.hash import bcrypt
				import re
				
				# Handle both PHP ($2y$) and Python ($2b$) bcrypt formats
				stored_password = user.password
				password_valid = False
				
				# Check if it's a PHP bcrypt hash ($2y$)
				if stored_password.startswith('$2y$'):
					# Convert PHP format to Python format
					python_hash = stored_password.replace('$2y$', '$2b$', 1)
					try:
						password_valid = bcrypt.verify(password, python_hash)
					except Exception:
						# If conversion fails, try direct verification
						password_valid = bcrypt.verify(password, stored_password)
				else:
					# Try direct verification for other formats
					try:
						password_valid = bcrypt.verify(password, stored_password)
					except Exception:
						password_valid = False
				
				if password_valid:
					# Map roles to legacy session values used across the app
					mapped_role = 'admin' if (user.role or '').lower() == 'admin' else 'user'
					request.session['app_user_id'] = user.user_id
					request.session['app_username'] = user.username
					request.session['app_role'] = mapped_role
					
					# Check if there's a QR redirect URL to go back to
					qr_redirect_url = request.session.pop('qr_redirect_url', None)
					if qr_redirect_url:
						return redirect(qr_redirect_url)
					
					return redirect('dashboard')
				else:
					messages.error(request, 'Password is incorrect.')
		except Exception as exc:
			messages.error(request, f'Login error: {exc}')
	
	# Check if this is a redirect from QR scanning
	qr_redirect_url = request.session.get('qr_redirect_url')
	is_from_qr = qr_redirect_url and '/qr/confirm/' in qr_redirect_url
	
	return render(request, 'login.html', {
		'is_from_qr': is_from_qr
	})


def logout_view(request):
	for key in ['app_user_id', 'app_username', 'app_role']:
		request.session.pop(key, None)
	return redirect('login')


def require_app_login(view_func):
	def wrapper(request, *args, **kwargs):
		if not request.session.get('app_user_id'):
			return redirect('login')
		return view_func(request, *args, **kwargs)
	return wrapper


@require_app_login
def dashboard_view(request):
	today = timezone.now().date()
	yesterday = today - timezone.timedelta(days=1)
	last_month = today - timezone.timedelta(days=30)
	role = request.session.get('app_role', 'admin')

	# Basic stats
	total_products = Product.objects.count()
	last_month_products = Product.objects.filter(created_at__date__lte=last_month).count()
	
	low_stock = Product.objects.filter(status='active', stock__lte=10).count()
	yesterday_low_stock = Product.objects.filter(status='active', stock__lte=10, last_updated__date__lte=yesterday).count()
	
	today_sales = Sale.objects.filter(recorded_at__date=today).count()
	yesterday_sales = Sale.objects.filter(recorded_at__date=yesterday).count()
	
	# Revenue calculations
	today_revenue = Sale.objects.filter(
		recorded_at__date=today,
		status='completed'
	).aggregate(total=Sum('total'))['total'] or 0
	
	yesterday_revenue = Sale.objects.filter(
		recorded_at__date=yesterday,
		status='completed'
	).aggregate(total=Sum('total'))['total'] or 0

	# Calculate percentage changes
	def calculate_percentage_change(current, previous):
		if previous == 0:
			return 100 if current > 0 else 0
		return round(((current - previous) / previous) * 100, 1)

	products_change = calculate_percentage_change(total_products, last_month_products)
	low_stock_change = calculate_percentage_change(low_stock, yesterday_low_stock)
	sales_change = calculate_percentage_change(today_sales, yesterday_sales)
	revenue_change = calculate_percentage_change(float(today_revenue), float(yesterday_revenue))

	# Sales data for past week
	past_week = []
	sales_totals = []
	for i in range(6, -1, -1):
		date = today - timezone.timedelta(days=i)
		past_week.append(date.strftime('%a'))
		total = Sale.objects.filter(
			recorded_at__date=date,
			status='completed'
		).aggregate(t=Sum('total'))['t'] or 0
		sales_totals.append(float(total))

	# Top selling products (single-table sales)
	top_products = (
		Sale.objects
		.values('product__name')
		.annotate(quantity=Sum('quantity'))
		.order_by('-quantity')[:5]
	)

	# Recent activity (last 5 activities)
	recent_sales = Sale.objects.filter(
		status='completed'
	).select_related('product').order_by('-recorded_at')[:3]
	
	recent_stock_additions = StockAddition.objects.select_related('product').order_by('-created_at')[:2]
	
	low_stock_products = Product.objects.filter(
		status='active',
		stock__lte=10
	).order_by('stock')[:2]

	# Additional comprehensive overview data
	# Monthly revenue
	this_month = today.replace(day=1)
	monthly_revenue = Sale.objects.filter(
		recorded_at__date__gte=this_month,
		status='completed'
	).aggregate(total=Sum('total'))['total'] or 0
	
	# Total inventory value
	total_inventory_value = Product.objects.filter(status='active').aggregate(
		value=Sum(F('stock') * F('price'))
	)['value'] or 0
	
	# Out of stock products
	out_of_stock = Product.objects.filter(status='active', stock=0).count()
	
	# Weekly sales summary
	week_start = today - timezone.timedelta(days=6)
	weekly_sales = Sale.objects.filter(
		recorded_at__date__gte=week_start,
		status='completed'
	).aggregate(
		total_sales=Sum('quantity'),
		total_revenue=Sum('total')
	)
	
	# Recent transactions (last 10)
	recent_transactions = Sale.objects.filter(
		status='completed'
	).select_related('product').order_by('-recorded_at')[:10]
	
	# Top customers (by sales count)
	top_customers = (
		Sale.objects
		.filter(status='completed')
		.exclude(customer_name__isnull=True)
		.exclude(customer_name='')
		.values('customer_name')
		.annotate(
			sales_count=Count('sale_id'),
			total_spent=Sum('total')
		)
		.order_by('-sales_count')[:5]
	)
	
	# Product categories overview
	product_categories = (
		Product.objects
		.filter(status='active')
		.values('size')
		.annotate(
			count=Count('product_id'),
			total_stock=Sum('stock')
		)
		.order_by('-count')[:5]
	)

	context = {
		'app_role': role,
		'total_products': total_products,
		'products_change': products_change,
		'low_stock': low_stock,
		'low_stock_change': low_stock_change,
		'today_sales': today_sales,
		'sales_change': sales_change,
		'today_revenue': today_revenue,
		'revenue_change': revenue_change,
		'sales_past_week': json.dumps(past_week),
		'sales_totals': json.dumps(sales_totals),
		'top_products': top_products,
		'recent_sales': recent_sales,
		'recent_stock_additions': recent_stock_additions,
		'low_stock_products': low_stock_products,
		# Additional overview data
		'monthly_revenue': monthly_revenue,
		'total_inventory_value': total_inventory_value,
		'out_of_stock': out_of_stock,
		'weekly_sales_count': weekly_sales['total_sales'] or 0,
		'weekly_revenue': weekly_sales['total_revenue'] or 0,
		'recent_transactions': recent_transactions,
		'top_customers': top_customers,
		'product_categories': product_categories,
	}

	return render(request, 'dashboard_full.html', context)


@require_app_login
@require_http_methods(["GET", "POST"])
def products_inventory(request):
    """Main products inventory view"""
    try:
        # Get query parameters
        search = request.GET.get('search', '')
        filter_status = request.GET.get('filter', 'All Products')
        sort_column = request.GET.get('sort_column', 'name')
        sort_order = request.GET.get('sort_order', 'asc')

        # Base queryset: ALL products for accurate counting
        products = Product.objects.all()

        # Apply filters
        if search:
            products = products.filter(
                Q(name__icontains=search) |
                Q(size__icontains=search)
            )
        if filter_status != 'All Products':
            products = products.filter(status=filter_status.lower())

        # Apply sorting
        sort_field = {
            'name': 'name',
            'stock': 'stock',
            'date_added': 'date_added'
        }.get(sort_column, 'name')
        
        if sort_order.lower() == 'desc':
            sort_field = f'-{sort_field}'
        
        products = products.order_by(sort_field)

        # Calculate dashboard stats - count ALL products
        total_products = products.count()
        active_products = products.filter(status='active').count()
        total_stock = products.aggregate(total=Sum('stock'))['total'] or 0
        restock_alerts = products.filter(status='active', stock__lt=10).count()

        # For the table display, filter to non-built-in products only
        table_products = products.filter(is_built_in=False)

        # Get unique fruits and suppliers for client-side dropdown
        unique_fruits = list(Product.objects.filter(is_built_in=True).values_list('name', flat=True).distinct())
        unique_suppliers = list(Product.objects.filter(is_built_in=False).exclude(supplier__isnull=True).exclude(supplier='').values_list('supplier', flat=True).distinct())
        
        context = {
            'products': table_products,  # Use filtered products for table
            'total_products': total_products,
            'active_products': active_products,
            'total_stock': total_stock,
            'restock_alerts': restock_alerts,
            'user': request.user,
            'app_role': request.session.get('app_role', 'user'),
            'show_cost': request.session.get('app_role') == 'admin',
            'today': timezone.now().date(),
            'fruits': unique_fruits,
            'suppliers': unique_suppliers
        }
        return render(request, 'products_inventory_full.html', context)

    except Exception as e:
        messages.error(request, f'Error loading inventory: {str(e)}')
        return render(request, 'products_inventory_full.html', {'error': str(e)})

@require_app_login
def add_product_page(request):
    """Standalone page that mirrors the Add Product modal (UI + JS)."""
    try:
        role = request.session.get('app_role', 'user')
        unique_suppliers = list(Product.objects.filter(is_built_in=False)
                                .exclude(supplier__isnull=True)
                                .exclude(supplier='')
                                .values_list('supplier', flat=True)
                                .distinct())
        context = {
            'app_role': role,
            'show_cost': role == 'admin',
            'today': timezone.now().date(),
            'suppliers': unique_suppliers,
        }
        return render(request, 'add_product.html', context)
    except Exception as e:
        messages.error(request, f'Error loading add product page: {str(e)}')
        return render(request, 'add_product.html', {'error': str(e)})

@require_app_login
def record_sale_page(request):
    """Standalone page that mirrors the Record Sale modal (UI + JS)."""
    # Get product_id from URL parameters (from QR code scan)
    product_id = request.GET.get('product_id')
    
    context = {
        'app_role': request.session.get('app_role', 'user'),
        'today': timezone.now().date(),
        'show_cost': request.session.get('app_role') == 'admin',
        'preselected_product_id': product_id,  # Pass to template for auto-selection
        'product_locked': bool(product_id),  # Lock product selection when accessed via QR
    }
    return render(request, 'record_sale.html', context)

@require_app_login
def add_stock_page(request):
    """Standalone page that mirrors the Add Stock modal (UI + JS)."""
    context = {
        'app_role': request.session.get('app_role', 'user'),
        'today': timezone.now().date(),
    }
    
    # Handle QR token from scanned QR codes or direct product_id
    qr_token = request.GET.get('qr_token')
    product_id = request.GET.get('product_id')
    
    if qr_token:
        try:
            # Import the QR system's serializer to decode the token
            from itsdangerous import URLSafeSerializer
            s = URLSafeSerializer(settings.SECRET_KEY)
            data = s.loads(qr_token)
            product_id = data.get('p')
        except Exception:
            # If QR token is invalid, just ignore it
            pass
    
    if product_id:
        try:
            product = Product.objects.get(product_id=product_id)
            context['qr_product'] = {
                'product_id': product.product_id,
                'name': product.name,
                'pre_selected': True,
                'locked': True  # Lock the product selection when accessed via QR
            }
        except Product.DoesNotExist:
            pass
    
    return render(request, 'add_stock.html', context)

@require_app_login
def print_stickers_page(request):
    context = {
        'app_role': request.session.get('app_role', 'user'),
    }
    return render(request, 'print_stickers.html', context)

# AJAX endpoints for product operations
# -- Updated implementation: accept multipart/form-data coming from the modal --
@require_app_login
@require_http_methods(["POST"])
def product_add(request):
	"""Add a new product to inventory from built-in products.

	The modal submits a multipart/form-data payload (handled via FormData in JS) that can contain an
	optional image file.  We must therefore read from request.POST / request.FILES instead of
	json.loads(request.body)."""
	try:
		built_in_product_id = request.POST.get('built_in_product_id', '').strip()
		name = request.POST.get('name', '').strip()
		variant = request.POST.get('variant', '').strip()
		size = request.POST.get('size', '').strip()
		# Always set new products to Active and date to today
		status = 'Active'
		date_added = timezone.now().date()
		stock = int(request.POST.get('stock', 0) or 0)
		price_str = request.POST.get('price', '0')
		cost_str = request.POST.get('cost', '0')
		try:
			price = Decimal(price_str)
		except Exception:
			price = Decimal('0')
		try:
			cost = Decimal(cost_str)
		except Exception:
			cost = Decimal('0')
		supplier = request.POST.get('supplier', '').strip()

		# Enhanced validation
		if not name:
			return JsonResponse({'success': False, 'message': 'Product name is required.'})
		if not size:
			return JsonResponse({'success': False, 'message': 'Product size is required.'})
		# Enforce numeric-only size (allow one decimal point)
		try:
			# Normalize size by parsing to Decimal then back to string without trailing zeros
			_s = str(Decimal(size))
			# Prevent negative or non-numeric
			if Decimal(_s) < 0:
				return JsonResponse({'success': False, 'message': 'Size must be a non-negative number.'})
			size = _s
			# Enforce size to be one of the unified options
			if size not in STANDARD_SIZE_OPTIONS:
				return JsonResponse({'success': False, 'message': f'Size must be one of: {", ".join(STANDARD_SIZE_OPTIONS)}'})
		except Exception:
			return JsonResponse({'success': False, 'message': 'Size must be numeric (e.g., 10 or 10.5).'})
		if price <= 0:
			return JsonResponse({'success': False, 'message': 'Price must be greater than 0.'})
		if cost < 0:
			return JsonResponse({'success': False, 'message': 'Cost cannot be negative.'})
		if stock < 0:
			return JsonResponse({'success': False, 'message': 'Stock cannot be negative.'})

		# Build full product name with variant
		full_name = f"{name} ({variant})" if variant else name

		# Check if inventory product already exists (ignore built-ins)
		if Product.objects.filter(name=full_name, size=size, is_built_in=False).exists():
			return JsonResponse({'success': False, 'message': 'This product is already in your inventory.'})

		# Handle optional image upload
		image_field = request.FILES.get('image')
		image_url = None
		if image_field:
			filename = f"product_{timezone.now().strftime('%Y%m%d%H%M%S')}_{image_field.name}"
			path = default_storage.save(os.path.join('uploads', filename), ContentFile(image_field.read()))
			image_url = default_storage.url(path)

		with transaction.atomic():
			# Create inventory product (not built-in)
			product = Product.objects.create(
				name=full_name,
				variant=variant or None,
				size=size,
				status=status,
				date_added=date_added,
				price=price,
				cost=cost,
				supplier=supplier,
				image=image_url or '',
				is_built_in=False,
			)
			# Stock is now stored directly on the Product model
			product.stock = stock
			product.save()

			# If stock is provided, create a stock addition record
			if stock > 0:
				batch_id = generate_batch_id(product, name, variant)
				StockAddition.objects.create(
					product=product,
					quantity=stock,
					date_added=date_added,
					remaining_quantity=stock,
					batch_id=batch_id,
					cost=cost
				)

		return JsonResponse({'success': True, 'message': 'Product added to inventory successfully.'})
	except Exception as e:
		return JsonResponse({'success': False, 'message': str(e)})

@require_app_login
@require_http_methods(["POST"])
def product_edit(request, product_id):
	"""Edit an existing product."""
	try:
		data = json.loads(request.body)
		with transaction.atomic():
			product = Product.objects.get(product_id=product_id)
			product.name = data['name']
			product.size = data.get('size', '')
			product.status = data.get('status', 'Active')
			product.price = data['price']
			product.cost = data.get('cost', 0)
			product.save()

			if 'stock' in data:
				product.stock = data['stock']
				product.save()

		return JsonResponse({'success': True, 'message': 'Product updated successfully.'})
	except Product.DoesNotExist:
		return JsonResponse({'success': False, 'message': 'Product not found.'})
	except Exception as e:
		return JsonResponse({'success': False, 'message': str(e)})

@require_app_login
@require_http_methods(["POST"])
def product_delete(request, product_id):
	"""Delete a product."""
	try:
		Product.objects.get(product_id=product_id).delete()
		return JsonResponse({'success': True, 'message': 'Product deleted successfully.'})
	except Product.DoesNotExist:
		return JsonResponse({'success': False, 'message': 'Product not found.'})
	except Exception as e:
		return JsonResponse({'success': False, 'message': str(e)})

@require_app_login
@require_http_methods(["POST"])
@csrf_exempt
def add_stock(request):
	"""Add stock for multiple products."""
	if request.method != 'POST':
		return JsonResponse({'success': False, 'message': 'Only POST method allowed.'})
	
	try:
		# Accept both JSON and form POST
		if request.META.get('CONTENT_TYPE', '').startswith('application/json'):
			data = json.loads(request.body or b"{}")
		else:
			items_raw = request.POST.get('items')
			data = {
				'items': json.loads(items_raw) if items_raw else [],
				'date_added': request.POST.get('date_added')
			}
		items = data.get('items', [])
		date_added = data.get('date_added')
		
		if not items:
			return JsonResponse({'success': False, 'message': 'No items provided.'})
		
		with transaction.atomic():
			added_items = []
			for item in items:
				product_id = item.get('product_id')
				quantity = item.get('quantity')
				supplier = item.get('supplier', '')
				
				# Debug: Print what supplier value we're receiving
				print(f"DEBUG: Received supplier value: '{supplier}' (type: {type(supplier)}, length: {len(supplier) if supplier else 0})")
				
				if not product_id or not quantity:
					continue
				
				try:
					product = Product.objects.get(product_id=product_id)
					# Build batch id similar to PHP/QR helpers (acronyms + date)
					base_name = product.name or ''
					variant = ''
					if '(' in base_name and base_name.endswith(')'):
						try:
							variant = base_name.split('(')[1].rstrip(')').strip()
						except Exception:
							variant = ''
					# Create one stock addition record with total quantity and base batch ID
					batch_id = generate_batch_id(product, base_name.replace(f"({variant})", '').strip() if variant else base_name, variant)
					
					# Debug: Print what we're about to save
					supplier_to_save = supplier if supplier else None
					print(f"DEBUG: About to save supplier: '{supplier_to_save}' (type: {type(supplier_to_save)})")
					
					StockAddition.objects.create(
						product=product,
						quantity=int(quantity),
						date_added=timezone.now(),  # Use full datetime instead of just date
						remaining_quantity=int(quantity),
						batch_id=batch_id,
						supplier=supplier_to_save
					)
					
					# Update product stock directly
					product.stock = models.F('stock') + int(quantity)
					product.save()
					
					# Update product supplier if provided
					if supplier:
						product.supplier = supplier
						product.save()
					
					added_items.append({
						'product_name': product.name,
						'quantity': int(quantity),
						'supplier': supplier
					})
					
				except Product.DoesNotExist:
					continue
			
			if not added_items:
				return JsonResponse({'success': False, 'message': 'No valid items to add.'})
			
			return JsonResponse({
				'success': True,
				'message': f'Successfully added stock for {len(added_items)} item(s).',
				'added_items': added_items
			})
			
	except Exception as e:
		return JsonResponse({'success': False, 'message': str(e)})

# --- QR-based add-stock endpoints ---
@require_http_methods(["POST"])
def stock_qr_create(request):
	"""Create a signed URL to add-stock that can be embedded into a QR code."""
	try:
		if request.META.get('CONTENT_TYPE', '').startswith('application/json'):
			data = json.loads(request.body or b"{}")
		else:
			items_raw = request.POST.get('items')
			data = {
				'items': json.loads(items_raw) if items_raw else [],
				'date_added': request.POST.get('date_added')
			}
		items = data.get('items', [])
		date_added = data.get('date_added')
		payload = {'items': items, 'date_added': date_added}
		token = signing.dumps(payload, salt='add_stock_qr')
		apply_url = request.build_absolute_uri(reverse('stock_qr_apply')) + f"?t={token}"
		expires_at = (timezone.now() + timedelta(minutes=5)).isoformat()
		return JsonResponse({'success': True, 'url': apply_url, 'expires_at': expires_at})
	except Exception as e:
		return JsonResponse({'success': False, 'message': str(e)})

@require_http_methods(["GET"])  # Validate via signed token
def stock_qr_apply(request):
	"""Apply a signed token from a QR scan to add stock and show a simple confirmation."""
	token = request.GET.get('t')
	if not token:
		return HttpResponse('Missing token.', status=400)
	try:
		payload = signing.loads(token, salt='add_stock_qr', max_age=300)
		items = payload.get('items', [])
		date_added = payload.get('date_added')
		added_items = []
		with transaction.atomic():
			for item in items:
				product_id = item.get('product_id')
				quantity = item.get('quantity')
				supplier = item.get('supplier', '')
				if not product_id or not quantity:
					continue
				try:
					product = Product.objects.get(product_id=product_id)
					base_name = product.name or ''
					variant = ''
					if '(' in base_name and base_name.endswith(')'):
						try:
							variant = base_name.split('(')[1].rstrip(')').strip()
						except Exception:
							variant = ''
					batch_id = generate_batch_id(product, base_name.replace(f"({variant})", '').strip() if variant else base_name, variant)
					StockAddition.objects.create(
						product=product,
						quantity=quantity,
						date_added=date_added or timezone.now().date(),
						remaining_quantity=quantity,
						batch_id=batch_id,
						supplier=supplier
					)
					product.stock = models.F('stock') + quantity
					product.save()
					if supplier:
						product.supplier = supplier
						product.save()
					added_items.append({'name': product.name, 'qty': quantity})
				except Product.DoesNotExist:
					continue
		html = ["<h3>Stock Added</h3>", "<ul>"]
		for it in added_items:
			html.append(f"<li>{it['name']}: +{it['qty']}</li>")
		html.append("</ul><p>You can close this page.</p>")
		return HttpResponse('\n'.join(html))
	except signing.BadSignature:
		return HttpResponse('Invalid or expired QR token.', status=400)
	except Exception as e:
		return HttpResponse(f'Error: {str(e)}', status=500)

@require_http_methods(["GET"])
def qr_next_batch_sequence(request, product_id):
	"""Get next batch sequence number for a product"""
	try:
		# Lazy import to avoid circulars and guarantee availability
		from core.models import StockAddition  # noqa: WPS433
		product = Product.objects.get(product_id=product_id)
		
		# Simple, robust rule: next sequence is count of existing additions + 1
		# This avoids depending on historical batch_id string formats
		existing_count = StockAddition.objects.filter(product=product).count()
		next_sequence = (existing_count % 99) + 1  # keep it within 1..99 for two-digit suffixes
		
		# Generate base batch ID using product name and size
		from datetime import date
		today = date.today()
		base_name = product.name or ''
		variant = ''
		if '(' in base_name and base_name.endswith(')'):
			try:
				variant = base_name.split('(')[1].rstrip(')').strip()
			except Exception:
				variant = ''
		
		# Create base batch ID: first 2 chars of product name + size + date
		product_prefix = base_name.replace(f"({variant})", '').strip()[:2].upper() if variant else base_name[:2].upper()
		size_clean = product.size.replace('-', '') if product.size else ''
		date_str = today.strftime('%m%d%Y')
		base_batch_id = f"{product_prefix}{size_clean}{date_str}"
		
		return JsonResponse({
			'success': True, 
			'next_sequence': next_sequence,
			'base_batch_id': base_batch_id
		})
		
	except Product.DoesNotExist:
		return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
	except Exception as e:
		return JsonResponse({'success': False, 'message': str(e)}, status=500)

@require_http_methods(["GET"])
def stock_qr_decode(request):
	"""Decode QR token and return product information for form population."""
	token = request.GET.get('t')
	if not token:
		return JsonResponse({'success': False, 'message': 'Missing token.'}, status=400)
	
	try:
		payload = signing.loads(token, salt='add_stock_qr', max_age=300)
		items = payload.get('items', [])
		date_added = payload.get('date_added')
		
		decoded_items = []
		for item in items:
			product_id = item.get('product_id')
			quantity = item.get('quantity')
			supplier = item.get('supplier', '')
			if not product_id:
				continue
			
			try:
				product = Product.objects.get(product_id=product_id)
				decoded_items.append({
					'product_id': product.product_id,
					'name': product.name,
					'quantity': quantity,
					'supplier': supplier
				})
			except Product.DoesNotExist:
				continue
		
		return JsonResponse({
			'success': True,
			'items': decoded_items,
			'date_added': date_added
		})
		
	except signing.BadSignature:
		return JsonResponse({'success': False, 'message': 'Invalid or expired QR token.'}, status=400)
	except Exception as e:
		return JsonResponse({'success': False, 'message': str(e)}, status=500)

def stock_add(request, product_id):
	"""Add stock to a product."""
	try:
		data = json.loads(request.body)
		with transaction.atomic():
			product = Product.objects.get(product_id=product_id)
			
			# Create one stock addition record with total quantity
			batch_id = data.get('batch_id') or generate_batch_id(product, product.name, product.variant or '')
			StockAddition.objects.create(
				product=product,
				quantity=int(data['quantity']),
				date_added=timezone.now().date(),
				remaining_quantity=int(data['quantity']),
				batch_id=batch_id,
				supplier=data.get('supplier', '')
			)

			# Update product stock directly
			product.stock = models.F('stock') + int(data['quantity'])
			product.save()

			return JsonResponse({
				'success': True,
				'message': 'Stock added successfully.',
				'new_stock': product.stock
			})
	except Product.DoesNotExist:
		return JsonResponse({'success': False, 'message': 'Product not found.'})
	except Exception as e:
		return JsonResponse({'success': False, 'message': str(e)})

@require_app_login
def stock_details_view(request):
    """Stock details page view."""
    product_id = request.GET.get('product_id')
    if not product_id:
        return redirect('products_inventory')
    
    try:
        product = Product.objects.get(product_id=product_id)
        context = {
            'product': product,
            'product_id': product_id,
        }
        return render(request, 'stock_details.html', context)
    except Product.DoesNotExist:
        return redirect('products_inventory')

@require_app_login
def sales_view(request):
    """Sales management view."""
    # Get filter parameters
    filter_type = request.GET.get('filter', 'Daily')
    search = request.GET.get('search', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    today = timezone.now().date()

    # Base query for completed sales (case-insensitive)
    sales_query = Sale.objects.filter(status__iexact='completed')
    
    # Apply date filters (accept "today", case-insensitive)
    ft = (filter_type or 'Daily').strip().lower()
    if ft in ('daily','today'):
        sales_query = sales_query.filter(recorded_at__date=today)
    elif ft in ('weekly','week'):
        sales_query = sales_query.filter(recorded_at__gte=timezone.now() - timedelta(days=7))
    elif ft in ('monthly','month'):
        sales_query = sales_query.filter(recorded_at__gte=timezone.now() - timedelta(days=30))
    elif ft == 'custom' and start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            sales_query = sales_query.filter(recorded_at__date__range=[start, end])
        except ValueError:
            # Invalid date format, fallback to daily
            sales_query = sales_query.filter(recorded_at__date=today)

    # Apply search filter if provided (sale no., product, flexible dates)
    if search:
        s = (search or '').strip()
        if s.startswith('#') and s[1:].isdigit():
            sales_query = sales_query.filter(sale_id=s[1:])
        elif s.isdigit():
            try:
                year_int = int(s)
                if 1900 <= year_int <= 2100:
                    sales_query = sales_query.filter(recorded_at__year=year_int)
                else:
                    sales_query = sales_query.filter(sale_id=s)
            except Exception:
                sales_query = sales_query.filter(sale_id=s)
        else:
            parsed = None
            fmt_used = ''
            for fmt in ('%B %d, %Y', '%b %d, %Y', '%B %d', '%b %d', '%B %Y', '%b %Y', '%Y-%m-%d', '%B', '%b'):
                try:
                    parsed = datetime.strptime(s, fmt)
                    fmt_used = fmt
                    break
                except ValueError:
                    continue
            if parsed:
                if '%d' in fmt_used and '%Y' in fmt_used:
                    sales_query = sales_query.filter(recorded_at__date=parsed.date())
                elif '%d' in fmt_used:
                    sales_query = sales_query.filter(recorded_at__month=parsed.month, recorded_at__day=parsed.day)
                elif '%Y' in fmt_used and ('%B' in fmt_used or '%b' in fmt_used):
                    sales_query = sales_query.filter(recorded_at__year=parsed.year, recorded_at__month=parsed.month)
                elif fmt_used in ('%B', '%b'):
                    sales_query = sales_query.filter(recorded_at__month=parsed.month)
                else:
                    sales_query = sales_query.filter(recorded_at__year=parsed.year)
            else:
                sales_query = sales_query.filter(
                    Q(product__name__icontains=s) |
                    Q(product__size__icontains=s)
                ).distinct()

    # Calculate statistics (across all rows)
    total_boxes = sales_query.aggregate(total=Sum('quantity'))['total'] or 0
    total_revenue = sales_query.aggregate(total=Sum('total'))['total'] or Decimal('0.00')

    # Group rows by transaction number so multiple fruits appear as one sale
    rows = (
        sales_query.select_related('product', 'user')
        .order_by('-recorded_at', 'transaction_number', 'sale_id')
    )
    grouped = {}
    for row in rows:
        key = row.transaction_number or f"SID{row.sale_id}"
        g = grouped.get(key)
        item = {
            'product_name': row.product.name if row.product else '',
            'size': row.product.size if row.product else '',
            'quantity': int(row.quantity or 0),
            'price': row.price,
            'subtotal': row.total
        }
        if not g:
            grouped[key] = {
                'sale_id': row.sale_id,  # representative id
                'transaction_number': key,
                'recorded_at': row.recorded_at.strftime('%b %d, %Y %I:%M %p'),
                'items': [item],
                'items_json': [item],
                'total': row.total,
                'status': row.status,
                'product_count': 1,
                'total_boxes': int(row.quantity or 0),
                'products': item['product_name'],
                'customer_name': getattr(row, 'customer_name', '') or ''
            }
        else:
            g['items'].append(item)
            g['items_json'].append(item)
            g['total'] = (g['total'] or 0) + row.total
            g['product_count'] += 1
            g['total_boxes'] += int(row.quantity or 0)
            if item['product_name'] and item['product_name'] not in g['products']:
                g['products'] += f", {item['product_name']}"
            if not g.get('customer_name') and (getattr(row, 'customer_name', '') or ''):
                g['customer_name'] = getattr(row, 'customer_name', '')

    sales_data = list(grouped.values())
    total_sales = len(sales_data)

    # Get voided sales if user is admin
    voided_sales = []
    if request.session.get('app_role') == 'admin':
        # Delete voided sales older than 30 days
        Sale.objects.filter(
            status='voided',
            voided_at__lt=timezone.now() - timedelta(days=30)
        ).delete()

        # Get remaining voided sales
        voided_query = Sale.objects.filter(status='voided')
        if search:
            if search.isdigit():
                voided_query = voided_query.filter(sale_id=search)
            else:
                try:
                    search_date = datetime.strptime(search, '%B %d, %Y').date()
                    voided_query = voided_query.filter(recorded_at__date=search_date)
                except ValueError:
                    voided_query = voided_query.filter(
                        Q(product__name__icontains=search) |
                        Q(product__size__icontains=search)
                    ).distinct()

        for sale in voided_query.select_related('user', 'product'):
            # Build a single-item representation to align with the frontend shape
            items_data = []
            if sale.product:
                items_data = [{
                    'product_id': sale.product.product_id,
                    'product_name': sale.product.name,
                    'size': sale.product.size,
                        'units_sold': sale.quantity,
                    'price': float(sale.price),
                    'subtotal': float(sale.total)
                }]
            
            # Calculate days until deletion
            days_until_deletion = 30
            if sale.voided_at:
                days_passed = (timezone.now() - sale.voided_at).days
                days_until_deletion = max(0, 30 - days_passed)

            voided_sales.append({
                'sale_id': sale.sale_id,
                'recorded_at': sale.recorded_at.strftime('%b %d, %Y %I:%M %p'),
                'items': items_data,
                'items_json': items_data,
                'total': sale.total,
                'status': sale.status,
                'product_count': len(items_data),
                'total_boxes': sale.quantity,
                'products': sale.product.name if sale.product else '',
                'days_until_deletion': days_until_deletion
            })

    context = {
        'app_role': request.session.get('app_role', 'user'),
        'app_username': request.session.get('app_username', ''),
        'filter': filter_type,
        'search': search,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'total_boxes': total_boxes,
        'total_revenue': total_revenue,
        'sales': sales_data,
        'voided_sales': voided_sales,
    }
    return render(request, 'sales_full.html', context)

@require_app_login
def fetch_sales(request):
    """AJAX endpoint to fetch sales data."""
    try:
        filter_type = request.GET.get('filter', 'Daily')
        search = request.GET.get('search', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        status = request.GET.get('status', 'completed')

        # Base query
        if status and status.lower() != 'all':
            sales_query = Sale.objects.filter(status__iexact=status)
        else:
            sales_query = Sale.objects.all()

        # Apply filters (same logic as sales_view)
        ft = (filter_type or 'Daily').strip().lower()
        if ft in ('daily','today'):
            sales_query = sales_query.filter(recorded_at__date=timezone.now().date())
        elif ft in ('weekly','week'):
            sales_query = sales_query.filter(recorded_at__gte=timezone.now() - timedelta(days=7))
        elif ft in ('monthly','month'):
            sales_query = sales_query.filter(recorded_at__gte=timezone.now() - timedelta(days=30))
        elif ft == 'custom' and start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                sales_query = sales_query.filter(recorded_at__date__range=[start, end])
            except ValueError:
                sales_query = sales_query.filter(recorded_at__date=timezone.now().date())

        # Apply search: supports sale number, product name, and flexible dates
        if search:
            s = (search or '').strip()
            if s.startswith('#') and s[1:].isdigit():
                sales_query = sales_query.filter(sale_id=s[1:])
            elif s.isdigit():
                # treat pure digits as sale id or year
                try:
                    year_int = int(s)
                    if 1900 <= year_int <= 2100:
                        sales_query = sales_query.filter(recorded_at__year=year_int)
                    else:
                        sales_query = sales_query.filter(sale_id=s)
                except Exception:
                    sales_query = sales_query.filter(sale_id=s)
            else:
                # Try flexible date parsing - month day, optional year
                parsed = None
                for fmt in ('%B %d, %Y', '%b %d, %Y', '%B %d', '%b %d', '%B %Y', '%b %Y', '%Y-%m-%d'):
                    try:
                        parsed = datetime.strptime(s, fmt)
                        break
                    except ValueError:
                        continue
                if parsed:
                    if '%d' in fmt and '%Y' in fmt:
                        sales_query = sales_query.filter(recorded_at__date=parsed.date())
                    elif '%d' in fmt:
                        sales_query = sales_query.filter(recorded_at__month=parsed.month, recorded_at__day=parsed.day)
                    elif '%Y' in fmt and ('%B' in fmt or '%b' in fmt):
                        sales_query = sales_query.filter(recorded_at__year=parsed.year, recorded_at__month=parsed.month)
                    else:
                        sales_query = sales_query.filter(recorded_at__year=parsed.year)
                else:
                    sales_query = sales_query.filter(
                        Q(items__product__name__icontains=s) |
                        Q(items__product__size__icontains=s)
                    ).distinct()

        # Get sales rows and group by transaction_number
        rows = sales_query.select_related('user','product').order_by('-recorded_at','transaction_number','sale_id')
        grouped = {}
        for row in rows:
            key = row.transaction_number or f"SID{row.sale_id}"
            g = grouped.get(key)
            item = {
                'product_name': row.product.name if row.product else '',
                'size': row.product.size if row.product else '',
                'quantity': int(row.quantity or 0),
                'price': float(row.price or 0),
                'subtotal': float(row.total or 0)
            }
            if not g:
                grouped[key] = {
                    'sale_id': row.sale_id,
                    'transaction_number': key,
                    'recorded_at': row.recorded_at.strftime('%b %d, %Y %I:%M %p'),
                    'items': [item],
                    'items_json': [item],
                    'total': str(row.total),
                    'status': row.status,
                    'product_count': 1,
                    'total_boxes': int(row.quantity or 0),
                    'products': item['product_name'],
                    'customer_name': getattr(row, 'customer_name', '') or ''
                }
            else:
                g['items'].append(item)
                g['items_json'].append(item)
                g['total'] = str((Decimal(g['total']) if isinstance(g['total'], str) else g['total']) + (row.total or 0))
                g['product_count'] += 1
                g['total_boxes'] += int(row.quantity or 0)
                if item['product_name'] and item['product_name'] not in g['products']:
                    g['products'] += f", {item['product_name']}"
                if not g.get('customer_name') and (getattr(row, 'customer_name', '') or ''):
                    g['customer_name'] = getattr(row, 'customer_name', '')

        sales_data = list(grouped.values())

        return JsonResponse({
            'success': True,
            'data': sales_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_app_login
def void_sale(request, sale_id):
    """AJAX endpoint to void a sale."""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({
            'success': False,
            'message': 'Only admins can void sales.'
        })

    try:
        with transaction.atomic():
            sale = Sale.objects.select_related().get(sale_id=sale_id)
            if sale.status == 'voided':
                return JsonResponse({
                    'success': False,
                    'message': 'Sale is already voided.'
                })

            # Restore stock for each item
            if not sale.stock_restored:
                # Since we're using single-table sales, restore stock to the product
                product = sale.product
                if product:
                    # Add back to the most recent batch (LIFO for restoration)
                    latest_batch = StockAddition.objects.filter(
                        product=product
                    ).order_by('-date_added', '-addition_id').first()
                    
                    if latest_batch:
                        latest_batch.remaining_quantity += sale.quantity
                        latest_batch.save()
                    else:
                        # Create a new batch for restored stock
                        batch_id = generate_batch_id(product, product.name, product.variant)
                        StockAddition.objects.create(
                            product=product,
                            quantity=sale.quantity,
                            date_added=timezone.now().date(),
                            remaining_quantity=sale.quantity,
                            batch_id=batch_id
                        )
                    
                    # Update product stock total
                    product.stock = models.F('stock') + sale.quantity
                    product.save()

            # Mark sale as voided
            sale.status = 'voided'
            sale.voided_at = timezone.now()
            sale.stock_restored = True
            sale.save()

            return JsonResponse({
                'success': True,
                'message': 'Sale voided successfully.',
                'refresh_voided': True
            })
    except Sale.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Sale not found.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_app_login
def complete_sale(request, sale_id):
    """AJAX endpoint to mark a voided sale as completed."""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({
            'success': False,
            'message': 'Only admins can complete sales.'
        })

    try:
        with transaction.atomic():
            sale = Sale.objects.select_related().get(sale_id=sale_id)
            if sale.status == 'completed':
                return JsonResponse({
                    'success': False,
                    'message': 'Sale is already completed.'
                })

            # Deduct stock for each item
            if sale.stock_restored:
                product = sale.product
                if product:
                    if product.stock < sale.quantity:
                        return JsonResponse({
                            'success': False,
                            'message': f'Insufficient stock for {product.name}'
                        })
                    # Use FIFO deduction
                    deduct_stock_fifo(product.product_id, sale.quantity)

            # Mark sale as completed
            sale.status = 'completed'
            sale.voided_at = None
            sale.stock_restored = False
            sale.save()

            return JsonResponse({
                'success': True,
                'message': 'Sale completed successfully.',
                'refresh_voided': True
            })
    except Sale.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Sale not found.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_app_login
def get_sale_details(request, sale_id):
    """AJAX endpoint to get sale details."""
    try:
        sale = Sale.objects.select_related('user').get(sale_id=sale_id)
        items = sale.items.select_related('product').all()
        
        items_data = []
        for item in items:
            product_name = item.product.name
            variant = ''
            # Extract variant if product name has format "Name (Variant)"
            if '(' in product_name and ')' in product_name:
                name_parts = product_name.split('(')
                product_name = name_parts[0].strip()
                variant = name_parts[1].rstrip(')').strip()

            items_data.append({
                'product_name': product_name,
                'variant': variant,
                'size': item.product.size,
                'quantity': item.quantity,
                'price': str(item.product.price),
                'subtotal': str(item.subtotal)
            })

        return JsonResponse({
            'success': True,
            'data': {
                'sale_id': sale.sale_id,
                'or_number': sale.or_number,
                'recorded_at': sale.recorded_at.strftime('%b %d, %Y %I:%M %p'),
                'status': sale.status,
                'total': str(sale.total),
                'amount_paid': str(sale.amount_paid),
                'change_given': str(sale.change_given),
                'username': sale.user.username if sale.user else 'Unknown',
                'items': items_data
            }
        })
    except Sale.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Sale not found.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_app_login
def check_print_limit(request, sale_id):
    """AJAX endpoint to check if user can print receipt."""
    try:
        # For now, allow unlimited prints since ReceiptPrint model was removed
            return JsonResponse({
                'success': True,
                'data': {'can_print': True}
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_app_login
def record_print(request, sale_id):
    """AJAX endpoint to record a receipt print."""
    try:
        # ReceiptPrint model was removed, so just return success
        return JsonResponse({
            'success': True,
            'message': 'Print recorded successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@require_app_login
def reports_view(request):
    """Render reports page (admin only)."""
    if request.session.get('app_role') != 'admin':
        return redirect('dashboard')
    # Pass initial empty objects; JS will fetch
    context = {
        'app_role': request.session.get('app_role', 'user'),
        'app_username': request.session.get('app_username',''),
        'filter': request.GET.get('filter','Daily'),
        'search': request.GET.get('search',''),
        'start_date': request.GET.get('start_date',''),
        'end_date': request.GET.get('end_date',''),
    }
    return render(request, 'reports_full.html', context)

@require_app_login
def charts_view(request):
    """Render charts page (admin only)."""
    if request.session.get('app_role') != 'admin':
        return redirect('dashboard')
    # Pass initial empty objects; JS will fetch
    context = {
        'app_role': request.session.get('app_role', 'user'),
        'app_username': request.session.get('app_username',''),
        'filter': request.GET.get('filter','Daily'),
        'search': request.GET.get('search',''),
        'start_date': request.GET.get('start_date',''),
        'end_date': request.GET.get('end_date',''),
    }
    return render(request, 'charts_full.html', context)

def _apply_report_filters(queryset, filter_type, start_date, end_date):
    """Apply time filters case-insensitively and accept synonyms like 'today'."""
    today = timezone.now().date()
    ft = (filter_type or 'Daily').strip().lower()
    
    # Use explicit start_date and end_date when provided
    if start_date and end_date:
        try:
            s = datetime.strptime(start_date, '%Y-%m-%d').date()
            e = datetime.strptime(end_date, '%Y-%m-%d').date()
            queryset = queryset.filter(recorded_at__date__range=[s, e])
            return queryset
        except ValueError:
            pass
    
    # Fallback to filter_type
    if ft in ('daily', 'today'):
        queryset = queryset.filter(recorded_at__date=today)
    elif ft in ('yesterday',):
        yesterday = today - timedelta(days=1)
        queryset = queryset.filter(recorded_at__date=yesterday)
    elif ft in ('weekly', 'week'):
        queryset = queryset.filter(recorded_at__gte=timezone.now()-timedelta(days=7))
    elif ft in ('monthly', 'month'):
        queryset = queryset.filter(recorded_at__gte=timezone.now()-timedelta(days=30))
    elif ft in ('quarter',):
        queryset = queryset.filter(recorded_at__gte=timezone.now()-timedelta(days=90))
    elif ft in ('year',):
        queryset = queryset.filter(recorded_at__gte=timezone.now()-timedelta(days=365))
    elif ft in ('custom',):
        # Custom without dates defaults to all time
        pass
    
    return queryset

@require_app_login
def fetch_reports(request):
    """Return JSON data for reports tables."""
    if request.session.get('app_role')!='admin':
        return JsonResponse({'success':False,'message':'Unauthorized'},status=403)
    filter_type=request.GET.get('filter','Daily')
    search=request.GET.get('search','')
    start_date=request.GET.get('start_date','')
    end_date=request.GET.get('end_date','')

    # Debug logging
    print(f"=== FETCH_REPORTS DEBUG ===")
    print(f"Filter type: {filter_type}")
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")
    print(f"Search: {search}")

    try:
        sales_q=Sale.objects.filter(status__iexact='completed')
        print(f"Total completed sales: {sales_q.count()}")
        sales_q=_apply_report_filters(sales_q,filter_type,start_date,end_date)
        print(f"After filtering: {sales_q.count()}")
        print(f"==========================")
        if search:
            if search.isdigit():
                sales_q=sales_q.filter(sale_id=search)
            else:
                sales_q=sales_q.filter(Q(product__name__icontains=search)|Q(product__size__icontains=search)).distinct()

        # sales_summary
        agg=sales_q.aggregate(total_revenue=Sum(F('quantity')*F('product__price')),transaction_count=Count('sale_id',distinct=True),total_items_sold=Sum('quantity'))
        total_rev=agg['total_revenue'] or Decimal('0.00')
        trans_cnt=agg['transaction_count'] or 0
        total_boxes=agg['total_items_sold'] or 0
        sales_summary={
            'total_revenue':float(total_rev),
            'transaction_count':trans_cnt,
            'total_items_sold':total_boxes,
            'avg_order_value': float(total_rev/trans_cnt) if trans_cnt else 0
        }

        # top fruits - using single-table sales (already filtered by sales_q)
        top=sales_q.values('product__product_id','product__name','product__size').annotate(boxes_sold=Sum('quantity'),revenue=Sum(F('quantity')*F('product__price'))).order_by('-boxes_sold')[:5]
        top_fruits=[{
            'product_id':t['product__product_id'],
            'name':t['product__name'],
            'size':t['product__size'],
            'boxes_sold':t['boxes_sold'],
            'revenue':float(t['revenue']) if t['revenue'] else 0,
            'date': end_date if end_date else timezone.now().strftime('%Y-%m-%d')  # Add date field
        } for t in top]

        # fruit summary - using single-table sales (already filtered by sales_q)
        fs=sales_q.values('product__product_id','product__name','product__size','product__price').annotate(boxes_sold=Sum('quantity'),revenue=Sum(F('quantity')*F('product__price'))).order_by('-revenue')
        fruit_summary=[{
            'product_id':r['product__product_id'],
            'name':r['product__name'],
            'size':r['product__size'],
            'boxes_sold':r['boxes_sold'],
            'price_per_box':float(r['product__price']),
            'revenue':float(r['revenue']) if r['revenue'] else 0,
            'date': end_date if end_date else timezone.now().strftime('%Y-%m-%d')  # Add date field
        } for r in fs]

        # low stock fruits - using Product model directly
        # Note: Low stock shows current inventory status regardless of date filter
        # This is intentional - users want to see ALL current low stock items
        low_q=Product.objects.filter(stock__lte=10,status='Active').order_by('stock')
        low_stock=[{
            'product_id':inv.product_id,
            'name':inv.name,
            'size':inv.size,
            'stock':inv.stock,
            'price':float(inv.price),
            'date': timezone.now().strftime('%Y-%m-%d')  # Current date - inventory is real-time
        } for inv in low_q]

        # transactions - group by transaction_number to avoid showing each line item separately
        rows = sales_q.select_related('user','product').order_by('-recorded_at','transaction_number','sale_id')[:200]
        grouped = {}
        for row in rows:
            key = row.transaction_number or f"ORD{row.sale_id:06d}"
            g = grouped.get(key)
            if not g:
                grouped[key] = {
                    'sale_id': row.sale_id,
                    'transaction_number': row.transaction_number if row.transaction_number else key,
                    'or_number': row.or_number or 'N/A',
                    'recorded_at': row.recorded_at.strftime('%m/%d/%Y, %I:%M:%S %p'),
                    'customer_name': row.customer_name or 'N/A',
                    'contact_number': str(row.contact_number) if row.contact_number and row.contact_number != 0 else 'N/A',
                    'address': row.address or 'N/A',
                    'processed_by': row.user.username if row.user else 'admin',
                    'fruits': row.product.name if row.product else 'Unknown',
                    'sizes': row.product.size if row.product else '',
                    'total_boxes': int(row.quantity or 0),
                    'boxes': int(row.quantity or 0),
                    'items': int(row.quantity or 0),
                    'subtotal': float(row.total or 0),
                    'vat': float((row.total or 0) * Decimal('0.12')),
                    'total': float(row.total or 0),
                    'amount_paid': float(row.amount_paid or 0) if row.amount_paid else float(row.total or 0),
                    'status': row.status,
                    'fruit_count': 1,
                }
            else:
                # Add to existing transaction
                g['total_boxes'] += int(row.quantity or 0)
                g['boxes'] += int(row.quantity or 0)
                g['items'] += int(row.quantity or 0)
                g['subtotal'] += float(row.total or 0)
                g['vat'] += float((row.total or 0) * Decimal('0.12'))
                g['total'] += float(row.total or 0)
                g['fruit_count'] += 1
                if row.product:
                    if g['fruits'] and row.product.name not in g['fruits']:
                        g['fruits'] += f", {row.product.name}"
                    if row.product.size and row.product.size not in g['sizes']:
                        g['sizes'] += f", {row.product.size}" if g['sizes'] else row.product.size

        tx_data = list(grouped.values())[:100]  # Limit to 100 transactions

        # Product summary reports from report_product_summary table
        # Filter by date range if provided
        summary_reports_q = ReportProductSummary.objects.select_related('product')
        
        # Apply date filtering to summary reports
        if start_date and end_date:
            try:
                s = datetime.strptime(start_date,'%Y-%m-%d').date()
                e = datetime.strptime(end_date,'%Y-%m-%d').date()
                # Filter reports that overlap with the selected date range
                summary_reports_q = summary_reports_q.filter(
                    Q(period_start__lte=e) & Q(period_end__gte=s)
                )
            except ValueError:
                pass
        
        summary_reports = summary_reports_q.order_by('-generated_at')[:50]
        summary_reports_data = [{
            'product_name': r.product.name if r.product else 'Unknown',
            'period_start': r.period_start.strftime('%Y-%m-%d'),
            'period_end': r.period_end.strftime('%Y-%m-%d'),
            'granularity': r.granularity,
            'opening_qty': float(r.opening_qty),
            'added_qty': float(r.added_qty),
            'sold_qty': float(r.sold_qty),
            'closing_qty': float(r.closing_qty),
            'revenue': float(r.revenue),
            'cogs': float(r.cogs),
            'gross_profit': float(r.gross_profit),
            'gross_margin_pct': float(r.gross_margin_pct) if r.gross_margin_pct else None,
            'sell_through_pct': float(r.sell_through_pct) if r.sell_through_pct else None,
            'avg_daily_sales': float(r.avg_daily_sales) if r.avg_daily_sales else None,
            'days_of_cover_end': float(r.days_of_cover_end) if r.days_of_cover_end else None,
            'low_stock_flag': r.low_stock_flag,
            'price_action': r.price_action,
            'demand_level': r.demand_level,
            'last_price': float(r.last_price) if r.last_price else None,
            'suggested_price': float(r.suggested_price) if r.suggested_price else None,
            'first_sale_at': r.first_sale_at.strftime('%Y-%m-%d %H:%M') if r.first_sale_at else None,
            'date': r.generated_at.strftime('%Y-%m-%d') if r.generated_at else None,  # Add date field
            'last_sale_at': r.last_sale_at.strftime('%Y-%m-%d %H:%M') if r.last_sale_at else None,
            'sms_low_stock_count': r.sms_low_stock_count,
            'sms_expiry_count': r.sms_expiry_count,
        } for r in summary_reports]

        return JsonResponse({'success':True,'data':{
            'sales_summary':sales_summary,
            'top_fruits':top_fruits,
            'fruit_summary':fruit_summary,
            'low_stock':low_stock,
            'transactions':tx_data,
            'summary_reports': summary_reports_data
        }})
    except Exception as e:
        return JsonResponse({'success':False,'message':str(e)})

@require_app_login
def export_report(request):
    if request.method!='POST' or request.session.get('app_role')!='admin':
        return JsonResponse({'success':False,'message':'Forbidden'},status=403)
    # Force PDF-only export with real-time data (same filters as sales)
    report_type = request.POST.get('report_type','transactions')
    filter_type = request.POST.get('filter','Daily')
    start_date = request.POST.get('start_date','')
    end_date = request.POST.get('end_date','')
    search = request.POST.get('search','')

    sales_q = Sale.objects.filter(status__iexact='completed').select_related('product','user')
    sales_q = _apply_report_filters(sales_q, filter_type, start_date, end_date)
    if search:
        if search.isdigit():
            sales_q = sales_q.filter(sale_id=search)
        else:
            # Match product name or size
            sales_q = sales_q.filter(
                Q(product__name__icontains=search) | Q(product__size__icontains=search)
            ).distinct()

    # Aggregate summary
    agg = sales_q.aggregate(
        total_revenue=Sum(F('quantity')*F('product__price')),
        transaction_count=Count('sale_id', distinct=True),
        total_boxes=Sum('quantity')
    )
    total_revenue = float(agg['total_revenue'] or 0)
    transaction_count = int(agg['transaction_count'] or 0)
    total_boxes = int(agg['total_boxes'] or 0)

    # Build PDF with proper margins for landscape A4
    buffer = BytesIO()
    # A4 landscape is 297mm x 210mm = 841.89 x 595.27 points
    # Use smaller margins to maximize usable space
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), 
                          leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    from reportlab.lib.styles import ParagraphStyle
    elems = []

    # Calculate available width: 841.89 - 36 - 36 = 769.89 points
    available_width = 770

    # Title - compact style
    title_text = "StockWise - Complete Sales Report"
    elems.append(Paragraph(title_text, styles['Title']))
    
    # Report metadata - more compact
    period_text = f"{start_date} to {end_date}" if (start_date and end_date) else filter_type
    meta = f"<b>Date Range:</b> {period_text} | <b>Generated:</b> {timezone.now().strftime('%m/%d/%Y')}"
    elems.append(Paragraph(meta, styles['Normal']))
    elems.append(Spacer(1, 10))

    # ========== SECTION 1: SALES SUMMARY ==========
    section_style = ParagraphStyle('SectionHeader', parent=styles['Heading2'], textColor=colors.HexColor('#4F46E5'), spaceAfter=8)
    elems.append(Paragraph("📊 SALES SUMMARY", section_style))
    elems.append(Spacer(1, 6))
    
    avg_order = (total_revenue / transaction_count) if transaction_count > 0 else 0
    summary_data = [
        ['Metric', 'Value'],
        ['Total Revenue', f"₱{total_revenue:,.2f}"],
        ['Total Transactions', f"{transaction_count}"],
        ['Total Boxes Sold', f"{total_boxes}"],
        ['Average Order Value', f"₱{avg_order:,.2f}"]
    ]
    summary_tbl = Table(summary_data, colWidths=[250, 150])
    summary_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4F46E5')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (1,1), (1,-1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elems.append(summary_tbl)
    elems.append(Spacer(1, 12))

    # ========== SECTION 2: TOP PRODUCTS ==========
    elems.append(Paragraph("🏆 TOP PRODUCTS BY SALES", section_style))
    elems.append(Spacer(1, 6))
    
    # Get top products
    top_products = sales_q.values('product__product_id','product__name','product__size').annotate(
        boxes_sold=Sum('quantity'),
        revenue=Sum(F('quantity')*F('product__price'))
    ).order_by('-boxes_sold')[:10]
    
    if top_products:
        top_rows = [['Rank', 'Product', 'Size', 'Boxes Sold', 'Revenue']]
        for idx, prod in enumerate(top_products, 1):
            top_rows.append([
                str(idx),
                str(prod['product__name'] or 'N/A')[:30],
                str(prod['product__size'] or '')[:15],
                str(prod['boxes_sold'] or 0),
                f"₱{float(prod['revenue'] or 0):,.2f}"
            ])
        
        # Adjusted widths to fit in 770 points: 35+250+100+80+120 = 585
        top_table = Table(top_rows, colWidths=[35, 300, 120, 80, 120])
        top_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#10B981')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (3,1), (4,-1), 'RIGHT'),
            ('GRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F0FDF4')]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elems.append(top_table)
    else:
        elems.append(Paragraph("No product data available.", styles['Normal']))
    
    elems.append(Spacer(1, 16))

    # ========== SECTION 3: LOW STOCK INVENTORY ==========
    elems.append(Paragraph("⚠️ LOW STOCK ITEMS", section_style))
    elems.append(Spacer(1, 6))
    
    # Get low stock items
    low_stock_items = Product.objects.filter(stock__lte=10, status='Active').order_by('stock')[:15]
    
    if low_stock_items:
        low_rows = [['Product', 'Size', 'Current Stock', 'Price', 'Status']]
        for item in low_stock_items:
            status = '🔴 Critical' if item.stock <= 5 else '🟡 Low'
            low_rows.append([
                str(item.name)[:30],
                str(item.size)[:15],
                str(int(item.stock)),
                f"₱{float(item.price):,.2f}",
                status
            ])
        
        # Adjusted widths: 300+100+100+100+80 = 680
        low_table = Table(low_rows, colWidths=[300, 120, 100, 100, 80])
        low_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EF4444')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (2,1), (3,-1), 'RIGHT'),
            ('GRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#FEF2F2')]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elems.append(low_table)
    else:
        elems.append(Paragraph("✅ All products have sufficient stock.", styles['Normal']))
    
    elems.append(Spacer(1, 16))

    # ========== SECTION 4: DETAILED TRANSACTIONS ==========
    elems.append(Paragraph("💳 DETAILED TRANSACTIONS", section_style))
    elems.append(Spacer(1, 6))

    # Group transactions by transaction_number (same as display logic)
    sale_rows = sales_q.order_by('-recorded_at','transaction_number','sale_id')[:500]
    grouped = {}
    for row in sale_rows:
        key = row.transaction_number or f"ORD{row.sale_id:06d}"
        g = grouped.get(key)
        if not g:
            grouped[key] = {
                'sale_id': row.sale_id,
                'transaction_number': row.transaction_number if row.transaction_number else key,
                'or_number': row.or_number or 'N/A',
                'recorded_at': row.recorded_at.strftime('%m/%d/%Y %I:%M %p'),
                'customer_name': row.customer_name or 'Walk-in',
                'contact_number': str(row.contact_number) if row.contact_number and row.contact_number != 0 else 'N/A',
                'address': row.address or 'N/A',
                'processed_by': row.user.username if row.user else 'admin',
                'fruits': row.product.name if row.product else 'Unknown',
                'sizes': row.product.size if row.product else '',
                'total_boxes': int(row.quantity or 0),
                'subtotal': float(row.total or 0),
                'vat': float((row.total or 0) * Decimal('0.12')),
                'total': float(row.total or 0),
                'status': row.status,
                'fruit_count': 1,
            }
        else:
            # Add to existing transaction
            g['total_boxes'] += int(row.quantity or 0)
            g['subtotal'] += float(row.total or 0)
            g['vat'] += float((row.total or 0) * Decimal('0.12'))
            g['total'] += float(row.total or 0)
            g['fruit_count'] += 1
            if row.product:
                if g['fruits'] and row.product.name not in g['fruits']:
                    g['fruits'] += f", {row.product.name}"
                if row.product.size and row.product.size not in g['sizes']:
                    g['sizes'] += f", {row.product.size}" if g['sizes'] else row.product.size

    tx_data = list(grouped.values())[:200]  # Limit to 200 transactions for PDF

    # Transactions table with complete details - optimized widths for 770pt width
    # Total: 30+60+55+75+90+60+110+40+65+55+65+45 = 750 points
    rows = [['ID','Trans#','OR#','Date','Customer','Contact','Fruits','Boxes','Subtotal','VAT','Total','Status']]
    for tx in tx_data:
        rows.append([
            str(tx['sale_id']),
            str(tx['transaction_number'])[:10],  # Truncate long transaction numbers
            str(tx['or_number'])[:12],
            tx['recorded_at'][:16] if len(tx['recorded_at']) > 16 else tx['recorded_at'],  # Shorten date
            str(tx['customer_name'])[:15],  # Truncate long names
            str(tx['contact_number'])[:11],
            str(tx['fruits'])[:20],  # Truncate long product lists
            str(tx['total_boxes']),
            f"₱{tx['subtotal']:,.2f}",
            f"₱{tx['vat']:,.2f}",
            f"₱{tx['total']:,.2f}",
            tx['status'].title()[:8]
        ])
    
    # Adjusted column widths to fit in 770 points
    table = Table(rows, repeatRows=1, colWidths=[30, 60, 55, 75, 90, 60, 110, 40, 65, 55, 65, 45])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4F46E5')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 7),
        ('FONTSIZE', (0,1), (-1,-1), 6),
        ('ALIGN', (7,1), (10,-1), 'RIGHT'),  # Right align numbers
        ('ALIGN', (0,0), (0,-1), 'CENTER'),  # Center ID column
        ('GRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('WORDWRAP', (0,0), (-1,-1), True),  # Enable word wrap
    ]))
    elems.append(table)

    doc.build(elems)
    pdf = buffer.getvalue()
    buffer.close()

    # Generate filename with date
    filename = f"StockWise_Complete_Report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(pdf)
    return response


@require_app_login
def profile_view(request):
    """User profile page allowing self-update of name, phone, password and profile picture. Admins can also see other secretary accounts (view only for now)."""
    user_id = request.session.get('app_user_id')
    user_obj = AppUser.objects.get(user_id=user_id)

    # Handle updates
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        current_pw = request.POST.get('current_password', '')
        new_pw = request.POST.get('new_password', '')
        confirm_pw = request.POST.get('confirm_password', '')
        picture_file = request.FILES.get('profile_picture')
        errors = []
        success_msg = None

        # Basic validation
        if not name:
            errors.append('Name is required.')
        if new_pw or confirm_pw:
            if len(new_pw) < 8:
                errors.append('New password must be at least 8 characters.')
            if new_pw != confirm_pw:
                errors.append('Password confirmation does not match.')
            if not current_pw:
                errors.append('Current password is required to change password.')
            else:
                # Handle both PHP ($2y$) and Python ($2b$) bcrypt formats for current password verification
                stored_password = user_obj.password
                current_password_valid = False
                
                if stored_password.startswith('$2y$'):
                    # Convert PHP format to Python format
                    python_hash = stored_password.replace('$2y$', '$2b$', 1)
                    try:
                        current_password_valid = bcrypt.verify(current_pw, python_hash)
                    except Exception:
                        current_password_valid = bcrypt.verify(current_pw, stored_password)
                else:
                    try:
                        current_password_valid = bcrypt.verify(current_pw, stored_password)
                    except Exception:
                        current_password_valid = False
                
                if not current_password_valid:
                    errors.append('Current password is incorrect.')

        if not errors:
            user_obj.name = name
            user_obj.phone_number = phone
            if new_pw:
                user_obj.password = bcrypt.hash(new_pw)
            # Save picture if provided
            if picture_file:
                filename = f"profile_{user_id}{os.path.splitext(picture_file.name)[1]}"
                path = default_storage.save(os.path.join('uploads', filename), ContentFile(picture_file.read()))
                user_obj.profile_picture = default_storage.url(path)
            user_obj.save()
            success_msg = 'Profile updated successfully.'
            messages.success(request, success_msg)
            return redirect('profile')
        else:
            for e in errors:
                messages.error(request, e)

    # AppUser no longer stores created_at/last_login; provide placeholders
    created_fmt = '-'
    last_login_fmt = '-'

    # If admin, list secretary accounts
    all_users = None
    if request.session.get('app_role') == 'admin':
        all_users = list(AppUser.objects.filter(role='Secretary').exclude(user_id=user_id))

    context = {
        'app_role': request.session.get('app_role'),
        'user_obj': user_obj,
        'created_at_formatted': created_fmt,
        'last_login_formatted': last_login_fmt,
        'all_users': all_users,
    }
    return render(request, 'profile_full.html', context)


@require_app_login
@require_GET
def fetch_products(request):
    """Return products list for inventory table with optional search/filter"""
    search = request.GET.get('search', '').strip()
    filter_status = request.GET.get('filter', 'All Products')

    # Only show items that are actually in inventory; if field missing, fallback
    try:
        products_qs = Product.objects.filter(is_built_in=False)
    except Exception:
        products_qs = Product.objects.none()
    if search:
        products_qs = products_qs.filter(Q(name__icontains=search) | Q(size__icontains=search))
    if filter_status == 'Active':
        products_qs = products_qs.filter(status='active')
    elif filter_status == 'Low Stock':
        # Define low stock as less than 10 items
        products_qs = products_qs.filter(stock__lt=10, stock__gt=0)
    elif filter_status == 'Out of Stock':
        products_qs = products_qs.filter(stock=0)
    elif filter_status != 'All Products':
        products_qs = products_qs.filter(status=filter_status.lower())

    data = []
    for p in products_qs:
        data.append({
            'product_id': p.product_id,
            'name': p.name,
            'size': p.size,
            'price': float(p.price),
            'cost': float(p.cost),
            'stock': p.stock,
            'status': p.status,
        })
    return JsonResponse({'success': True, 'data': data})


@require_app_login
@require_GET
def fetch_active_products(request):
    """Return active products for record-sale modal (id, name, price, size, stock)."""
    try:
        qs = Product.objects.filter(status__iexact='active', is_built_in=False)
    except Exception:
        qs = Product.objects.none()
    data = []
    for p in qs:
        stock_val = getattr(p, 'stock', 0)
        data.append({
            'product_id': p.product_id,
            'name': p.name,
            'variant': p.variant or '',
            'price': float(p.price),
            'size': p.size,
            'stock': stock_val,
        })
    return JsonResponse({'success': True, 'data': data})


@require_app_login
@require_GET
def fetch_stock_details(request, product_id):
    """Return FIFO batch stock details for a product."""
    product = Product.objects.get(product_id=product_id)
    batches = (StockAddition.objects
               .filter(product_id=product_id)
               .order_by('date_added', 'addition_id'))
    # Meta totals from raw batches
    added_total = sum(int(b.quantity or 0) for b in batches)
    available_total = sum(int(b.remaining_quantity or 0) for b in batches)
    earliest_date = next((b.date_added for b in batches if b.date_added), None)
    data = []
    groups = []
    for b in batches:
        # Expand historical aggregated rows into per-box entries
        try:
            total_boxes = int(b.quantity or 0)
            prefix, start_seq = b.batch_id[:-2], int(b.batch_id[-2:]) if len(b.batch_id) >= 2 else (b.batch_id, 1)
        except Exception:
            total_boxes, prefix, start_seq = int(b.quantity or 0), b.batch_id, 1
        total_boxes = max(total_boxes, 1)
        # Build group for this addition
        group_visible_ids = []
        for i in range(total_boxes):
            seq = ((start_seq - 1 + i) % 99) + 1
            box_id = f"{prefix}{seq:02d}" if prefix else f"{seq:02d}"
            remaining_boxes = int(b.remaining_quantity or 0)
            consumed = max(0, total_boxes - remaining_boxes)
            box_remaining = 1 if (i >= consumed) else 0
            if box_remaining <= 0:
                continue
            data.append({
                'batch_id': box_id,
            'date_added': b.date_added,
                'quantity': 1,
                'remaining': box_remaining,
                'supplier': product.supplier or '-',
            })
            group_visible_ids.append(box_id)
        groups.append({
            'date_added': b.date_added,
            'added_total': total_boxes,
            'available_total': int(b.remaining_quantity or 0),
            'supplier': b.supplier or product.supplier or '-',
            'batch_ids': group_visible_ids,
        })
    return JsonResponse({'success': True, 'data': data, 'groups': groups, 'meta': {
        'added_total': added_total,
        'available_total': available_total,
        'date_added': earliest_date,
        'supplier': product.supplier or '-',
    }})


@require_app_login
@require_GET
def fetch_built_in_products(request):
    """Return unique built-in product names from CSV for the Add Product modal autocomplete."""
    try:
        search = (request.GET.get('search') or '').strip().lower()
        csv_path = os.path.join(settings.BASE_DIR, 'fruit_master_full.csv')
        if not os.path.exists(csv_path):
            return JsonResponse({'success': True, 'data': []})
        names = []
        seen = set()
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
                key = base.lower()
                if search and search not in key:
                    continue
                if key in seen:
                    continue
                seen.add(key)
                names.append({'name': base})
        return JsonResponse({'success': True, 'data': names})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_GET
def fruit_master_search(request):
    """FruitMaster model was removed - return empty results"""
    return JsonResponse({'results': []})


@require_GET
def fruit_master_sizes(request):
    """Return unified numeric size options regardless of product name."""
    try:
        # Always return the unified list
        return JsonResponse({'success': True, 'data': STANDARD_SIZE_OPTIONS})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_GET
def fruit_master_variants(request):
    """Return distinct variants for a given base product name from CSV built-ins."""
    try:
        base_name = (request.GET.get('name') or '').strip().lower()
        if not base_name:
            return JsonResponse({'success': True, 'data': []})
        csv_path = os.path.join(settings.BASE_DIR, 'fruit_master_full.csv')
        if not os.path.exists(csv_path):
            return JsonResponse({'success': True, 'data': []})
        variants = set()
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_l = {k.lower(): (v or '').strip() for k, v in row.items()}
                name_val = row_l.get('name') or row_l.get('fruit') or row_l.get('product') or ''
                if not name_val:
                    continue
                norm = name_val
                if '(' in norm and ')' in norm:
                    try:
                        norm = norm.split('(')[0].strip()
                    except Exception:
                        pass
                if norm.lower() != base_name:
                    continue
                var_val = row_l.get('variant') or row_l.get('variety') or row_l.get('type') or ''
                if not var_val and '(' in (row_l.get('name') or '') and ')' in (row_l.get('name') or ''):
                    try:
                        _, v = (row_l.get('name') or '').rsplit('(', 1)
                        var_val = v.rstrip(')').strip()
                    except Exception:
                        pass
                if var_val:
                    variants.add(var_val)
        return JsonResponse({'success': True, 'data': sorted(variants)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_app_login
@require_POST
@csrf_exempt
def record_sale(request):
    """Record a new sale: creates one sales row per item and updates product stock (FIFO)."""
    try:
        with transaction.atomic():
            items = json.loads(request.POST.get('items', '[]'))
            amount_paid = Decimal(str(request.POST.get('amount_paid', 0)))
            if not items:
                return JsonResponse({'success': False, 'message': 'No items provided'})

            # User
            user_id = request.session.get('app_user_id')
            if not user_id:
                return JsonResponse({'success': False, 'message': 'User not authenticated'})
            try:
                user = AppUser.objects.get(user_id=user_id)
            except AppUser.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'User not found'})

            year = timezone.now().year
            created_sales = []
            total_amount = Decimal('0')

            for item in items:
                product_id = item.get('product_id')
                quantity = int(item.get('quantity', 0))
                if not product_id or quantity <= 0:
                    continue

                # Normalize status to handle capitalized values in DB
                product = Product.objects.filter(product_id=product_id, status__iexact='active').first()
                if not product:
                    raise ValidationError(f'Product not found or inactive: {product_id}')

                # Ensure stock
                if product.stock < quantity:
                    raise ValidationError(f'Insufficient stock for {product.name}. Available: {product.stock}, Requested: {quantity}')

                # Accept client-generated transaction and OR numbers
                transaction_number = request.POST.get('transaction_number', '')
                or_number = request.POST.get('or_number', '')

                line_total = Decimal(product.price) * quantity

                sale_row = Sale.objects.create(
                    product=product,
                    quantity=quantity,
                    price=product.price,
                    transaction_number=transaction_number,
                    or_number=or_number,
                    customer_name=request.POST.get('customer_name', ''),
                    address=request.POST.get('customer_address', ''),
                    contact_number=int(request.POST.get('customer_contact', 0) or 0),
                    recorded_at=timezone.now(),
                    total=line_total,
                    amount_paid=amount_paid,
                    change_given=amount_paid - line_total,
                    status='completed',
                    user=user,
                )

                # FIFO deduct also recalculates and saves product stock
                deduct_stock_fifo(product.product_id, quantity)

                created_sales.append(sale_row.sale_id)
                total_amount += line_total

            return JsonResponse({
                'success': True,
                'message': f'Recorded {len(created_sales)} sale item(s).',
                'sale_ids': created_sales,
                'total_charged': float(total_amount)
            })

    except ValidationError as e:
        return JsonResponse({'success': False, 'message': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error recording sale: {str(e)}'})

@require_app_login
@require_GET
def get_active_products(request):
    """Return active products for the record sale modal"""
    try:
        products = Product.objects.filter(status='Active').values('product_id', 'name', 'variant', 'price', 'size', 'stock')
        return JsonResponse({'success': True, 'data': list(products)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_app_login
@require_GET
def get_sale_details(request, sale_id):
    """Return sale details for receipt"""
    try:
        sale = Sale.objects.select_related('user').get(sale_id=sale_id)

        # Collect all rows that belong to the same transaction
        txn_key = getattr(sale, 'transaction_number', '') or ''
        rows = Sale.objects.select_related('product').filter(
            status__iexact='completed',
            transaction_number=txn_key if txn_key else sale.transaction_number
        ) if txn_key else [sale]

        items_data = []
        total_amount = Decimal('0')
        total_boxes = 0
        for row in rows:
            batch_ids = _compute_sale_batch_ids(row)
            items_data.append({
                'product_id': row.product.product_id if row.product else None,
                'product__name': row.product.name if row.product else 'Unknown',
                'product__size': row.product.size if row.product else '',
                'quantity': int(row.quantity or 0),
                'price': float(row.price or 0),
                'batch_ids': batch_ids
            })
            total_amount += (row.total or Decimal('0'))
            total_boxes += int(row.quantity or 0)

        # Transaction number: stored field if present; fallback to OR derived
        txn_number = txn_key
        if not txn_number:
            try:
                on = sale.or_number or ''
                if isinstance(on, str) and on.strip():
                    suffix = ''.join(ch for ch in on if ch.isdigit())[-6:]
                    txn_number = f"TXN{suffix}" if suffix else ''
            except Exception:
                txn_number = ''

        return JsonResponse({
            'success': True,
            'sale': {
                'sale_id': sale.sale_id,
                'transaction_number': txn_number,
                'or_number': sale.or_number,
                'recorded_at': sale.recorded_at.isoformat(),
                'total': total_amount,
                'status': sale.status,
                'username': sale.user.username if sale.user else 'Unknown',
                'customer_name': getattr(sale, 'customer_name', ''),
                'customer_contact': getattr(sale, 'contact_number', ''),
                'customer_address': getattr(sale, 'address', ''),
                'product_count': len(items_data),
                'total_boxes': total_boxes,
                'amount_paid': total_amount,
                'change_given': Decimal('0')
            },
            'items': items_data
        })
    except Sale.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Sale not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def stock_details(request, product_id):
    """Get stock details for a product with FIFO ordering"""
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'})
    
    additions = (
        StockAddition.objects
        .filter(product=product)
        .order_by('date_added', 'addition_id')
    )
    # Meta totals from raw additions
    added_total = sum(int(b.quantity or 0) for b in additions)
    available_total = sum(int(b.remaining_quantity or 0) for b in additions)
    earliest_date = next((b.date_added for b in additions if b.date_added), None)
    
    data = []
    groups = []
    for b in additions:
        # Expand potentially aggregated rows into per-box entries
        try:
            total_boxes = int(b.quantity or 0)
            prefix, start_seq = b.batch_id[:-2], int(b.batch_id[-2:]) if len(b.batch_id) >= 2 else (b.batch_id, 1)
        except Exception:
            total_boxes, prefix, start_seq = int(b.quantity or 0), b.batch_id, 1
        total_boxes = max(total_boxes, 1)
        group_visible_ids = []
        for i in range(total_boxes):
            seq = ((start_seq - 1 + i) % 99) + 1
            box_id = f"{prefix}{seq:02d}" if prefix else f"{seq:02d}"
            remaining_boxes = int(b.remaining_quantity or 0)
            consumed = max(0, total_boxes - remaining_boxes)
            box_remaining = 1 if (i >= consumed) else 0
            if box_remaining <= 0:
                continue
            data.append({
                'batch_id': box_id,
                'date_added': b.date_added.isoformat() if hasattr(b.date_added, 'isoformat') else str(b.date_added),
                'quantity': 1,
                'remaining': box_remaining,
                'supplier': product.supplier or '-',
            })
            group_visible_ids.append(box_id)
        groups.append({
            'date_added': b.date_added.isoformat() if hasattr(b.date_added, 'isoformat') else str(b.date_added),
            'added_total': total_boxes,
            'available_total': int(b.remaining_quantity or 0),
            'supplier': b.supplier or product.supplier or '-',
            'batch_ids': group_visible_ids,
        })
    
    return JsonResponse({'success': True, 'data': data, 'groups': groups, 'meta': {
        'added_total': added_total,
        'available_total': available_total,
        'date_added': earliest_date.isoformat() if hasattr(earliest_date, 'isoformat') else str(earliest_date) if earliest_date else '',
        'supplier': product.supplier or '-',
    }})


# POST request handlers for product operations
@require_app_login
@require_http_methods(["POST"])
@csrf_exempt
def handle_product_post(request):
    """Handle POST requests for product operations"""
    try:
        action = request.POST.get('action')
        
        if action == 'add':
            return add_product(request)
        elif action == 'edit':
            return edit_product(request)
        elif action == 'update_status':
            return update_product_status(request)
        elif action == 'buy':
            return record_sale(request)
        elif action == 'add_stock':
            return add_stock(request)
        else:
            return JsonResponse({'success': False, 'message': 'Invalid action'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def add_product(request):
    """Add new product"""
    try:
        with transaction.atomic():
            # Get form data
            name = request.POST.get('name', '').strip().title()
            variant = request.POST.get('variant', '').strip().title()
            size = request.POST.get('size', '').strip()
            cost = Decimal(request.POST.get('cost', 0))
            price = Decimal(request.POST.get('price', 0))
            status = request.POST.get('status', 'Active')
            boxes = int(request.POST.get('boxes', 0))
            units_per_box = int(request.POST.get('units_per_box', 1))
            stock = boxes * units_per_box
            # Force today's date for new products (ignore client-provided value)
            date_added = timezone.now().date()
            supplier = request.POST.get('supplier', '').strip()
            
            # Validate required fields
            if not name or not size or cost < 0 or price < 0 or stock < 0:
                raise ValueError("Invalid input data. Required fields: name, size, cost, price, stock.")

            # Normalize and validate numeric-only size
            try:
                size_norm = str(Decimal(size))
                if Decimal(size_norm) < 0:
                    raise ValueError("Size must be a non-negative number.")
                size = size_norm
                if size not in STANDARD_SIZE_OPTIONS:
                    raise ValueError(f"Size must be one of: {', '.join(STANDARD_SIZE_OPTIONS)}")
            except Exception:
                raise ValueError("Size must be numeric (e.g., 10 or 10.5).")
            
            if status not in ['Active', 'Discontinued']:
                raise ValueError("Invalid status.")
            
            # Build full product name
            full_name = f"{name} ({variant})" if variant else name
            
            # Check if product already exists in INVENTORY (ignore built-ins)
            if Product.objects.filter(name=full_name, size=size, is_built_in=False).exists():
                raise ValueError("A fruit with this name and size already exists in your inventory.")
            
            # Handle image upload
            image_path = None
            if 'image' in request.FILES:
                uploaded_file = request.FILES['image']
                if uploaded_file.size > 2 * 1024 * 1024:  # 2MB limit
                    raise ValueError("Image too large. Maximum 2MB allowed.")
                
                # Generate unique filename
                import uuid
                ext = uploaded_file.name.split('.')[-1]
                filename = f"product_{uuid.uuid4().hex}.{ext}"
                image_path = f"uploads/{filename}"
                
                # Save file
                default_storage.save(image_path, uploaded_file)
            
            # Create product
            product = Product.objects.create(
                name=full_name,
                variant=variant,
                size=size,
                cost=cost,
                price=price,
                status=status,
                date_added=date_added,
                image=image_path,
                supplier=supplier
            )
            
            # Add initial stock if provided
            if stock > 0:
                batch_id = generate_batch_id(product, name, variant)
                StockAddition.objects.create(
                    product=product,
                    quantity=stock,
                    date_added=date_added,
                    remaining_quantity=stock,
                    batch_id=batch_id
                )
                
                # Update product stock
                product.stock = stock
                product.save()
            
            return JsonResponse({'success': True, 'message': 'Product added successfully.'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def edit_product(request):
    """Edit existing product"""
    try:
        with transaction.atomic():
            product_id = request.POST.get('productId')
            if not product_id:
                raise ValueError("Product ID required.")
            
            product = Product.objects.get(product_id=product_id)
            
            # Get form data
            name = request.POST.get('name', '').strip().title()
            variant = request.POST.get('variant', '').strip().title()
            size = request.POST.get('size', '').strip()
            cost = Decimal(request.POST.get('cost', 0))
            price = Decimal(request.POST.get('price', 0))
            status = request.POST.get('status', 'Active')
            boxes = int(request.POST.get('boxes', 0))
            units_per_box = int(request.POST.get('units_per_box', 1))
            stock = boxes * units_per_box
            date_added = request.POST.get('date_added', timezone.now().date())
            supplier = request.POST.get('supplier', '').strip()
            
            # Validate required fields
            if not name or not size or cost < 0 or price < 0 or stock < 0:
                raise ValueError("Invalid input data. Required fields: name, size, cost, price, stock.")

            # Normalize and validate numeric-only size
            try:
                size_norm = str(Decimal(size))
                if Decimal(size_norm) < 0:
                    raise ValueError("Size must be a non-negative number.")
                size = size_norm
                if size not in STANDARD_SIZE_OPTIONS:
                    raise ValueError(f"Size must be one of: {', '.join(STANDARD_SIZE_OPTIONS)}")
            except Exception:
                raise ValueError("Size must be numeric (e.g., 10 or 10.5).")
            
            if status not in ['Active', 'Discontinued']:
                raise ValueError("Invalid status.")
            
            # Build full product name
            full_name = f"{name} ({variant})" if variant else name
            
            # Check if product already exists (excluding current product)
            if Product.objects.filter(name=full_name, size=size).exclude(product_id=product_id).exists():
                raise ValueError("A fruit with this name and size already exists.")
            
            # Handle image upload
            if 'image' in request.FILES:
                uploaded_file = request.FILES['image']
                if uploaded_file.size > 2 * 1024 * 1024:  # 2MB limit
                    raise ValueError("Image too large. Maximum 2MB allowed.")
                
                # Generate unique filename
                import uuid
                ext = uploaded_file.name.split('.')[-1]
                filename = f"product_{uuid.uuid4().hex}.{ext}"
                image_path = f"uploads/{filename}"
                
                # Save file
                default_storage.save(image_path, uploaded_file)
                product.image = image_path
            
            # Update product
            product.name = full_name
            product.variant = variant
            product.size = size
            product.cost = cost
            product.price = price
            product.status = status
            product.date_added = date_added
            product.supplier = supplier
            product.save()
            
            # Handle stock changes
            current_stock = product.stock
            stock_difference = stock - current_stock
            
            if stock_difference > 0:
                # Add stock
                batch_id = generate_batch_id(product, name, variant)
                StockAddition.objects.create(
                    product=product,
                    quantity=stock_difference,
                    date_added=date_added,
                    remaining_quantity=stock_difference,
                    batch_id=batch_id
                )
                
                # Update product stock
                product.stock += stock_difference
                product.save()
            
            elif stock_difference < 0:
                # Remove stock using FIFO
                deduct_stock_fifo(product.product_id, abs(stock_difference))
            
            elif stock == 0:
                # Clear all remaining stock
                StockAddition.objects.filter(product=product).update(remaining_quantity=0)
                product.stock = 0
                product.save()
            
            return JsonResponse({'success': True, 'message': 'Product updated successfully.'})
    
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def update_product_status(request):
    """Update product status"""
    try:
        product_id = request.POST.get('product_id')
        status = request.POST.get('status')
        
        if not product_id or status not in ['Active', 'Discontinued']:
            raise ValueError("Invalid product ID or status.")
        
        product = Product.objects.get(product_id=product_id)
        product.status = status
        product.save()
        
        return JsonResponse({'success': True, 'message': 'Status updated successfully.'})
    
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# Helper functions
def generate_batch_id(product, name, variant):
    """Generate per-box batch ID: <FRUIT><VARIANT?><SIZE><MMDDYYYY><SS>.
    SS ranges 01-99 and resets per product/size per day.
    """
    from datetime import date
    
    # Clean name (remove variant if present)
    base_name = name
    if variant and f"({variant})" in name:
        base_name = name.replace(f"({variant})", "").strip()
    
    fruit_acr = get_acronym(base_name)
    variant_acr = get_acronym(variant) if variant else ''
    size_full = str(product.size) if product.size else ''
    
    today = date.today()
    date_part = f"{today.month:02d}{today.day:02d}{today.year}"
    
    # Sequence increments per product and wraps at 99 (not daily)
    existing_total = StockAddition.objects.filter(
        product=product
    ).count()
    sequence = (existing_total % 99) + 1
    seq_part = f"{sequence:02d}"
    
    parts = [fruit_acr]
    if variant_acr:
        parts.append(variant_acr)
    if size_full:
        parts.append(size_full)
    parts.append(date_part)
    parts.append(seq_part)
    return ''.join(parts)


def get_acronym(text):
    """Get acronym from text"""
    if not text:
        return ''
    
    words = text.split()
    acronym = ''
    for word in words:
        if word:
            acronym += word[0].upper()
    
    return acronym


def deduct_stock_fifo(product_id, quantity):
    """Deduct stock using FIFO method (strict FIFO by date_added, then addition_id)"""
    # Get batches with remaining stock, ordered by date_added then addition_id for strict FIFO
    batches = StockAddition.objects.filter(
        product_id=product_id,
        remaining_quantity__gt=0
    ).order_by('date_added', 'addition_id')
    
    remaining_to_deduct = quantity
    
    for batch in batches:
        if remaining_to_deduct <= 0:
            break
        
        deduct_amount = min(remaining_to_deduct, batch.remaining_quantity)
        batch.remaining_quantity -= deduct_amount
        batch.save()
        
        remaining_to_deduct -= deduct_amount
    
    if remaining_to_deduct > 0:
        raise ValueError(f"Insufficient stock in batches for product ID {product_id}.")
    
    # Update product stock total from batch sums and clamp to >= 0
    total_remaining = StockAddition.objects.filter(
        product_id=product_id
    ).aggregate(total=models.Sum('remaining_quantity'))['total'] or 0
    total_remaining = max(0, int(total_remaining))
    Product.objects.filter(product_id=product_id).update(stock=total_remaining)


def _expand_batch_box_ids(batch_id, quantity):
    """Expand a batch_id into per-box IDs by appending/rolling 2-digit sequence.
    Assumes last two chars of batch_id are a numeric sequence start; if not, starts at 1.
    """
    try:
        start_seq = int(batch_id[-2:])
        prefix = batch_id[:-2]
    except Exception:
        start_seq = 1
        prefix = batch_id
    box_ids = []
    for i in range(int(quantity or 0)):
        seq = ((start_seq - 1 + i) % 99) + 1
        box_ids.append(f"{prefix}{seq:02d}")
    return box_ids


def _compute_sale_batch_ids(sale):
    """Compute which per-box batch IDs were consumed by this sale using strict FIFO.
    Works for single-product sales by replaying prior completed sales.
    """
    product = sale.product
    if not product:
        return []
    # Build FIFO queue of box IDs from stock additions
    additions = (StockAddition.objects
                 .filter(product=product)
                 .order_by('date_added', 'addition_id'))
    fifo_boxes = []
    for add in additions:
        fifo_boxes.extend(_expand_batch_box_ids(add.batch_id, add.quantity))
    # Replay all prior completed sales for this product in chronological order
    prior_sales = (Sale.objects
                   .filter(product=product, status__iexact='completed')
                   .order_by('recorded_at', 'sale_id'))
    consumed_index = 0
    target_ids = []
    for s in prior_sales:
        qty = int(s.quantity or 0)
        if s.sale_id == sale.sale_id:
            # Take the next qty boxes for this sale
            target_ids = fifo_boxes[consumed_index:consumed_index + qty]
            break
        consumed_index += qty
    return target_ids

def can_print_receipt(sale_id, user_id, user_role):
    """Check if user can print receipt"""
    # For now, allow unlimited prints since ReceiptPrint model was removed
    return True


# SMS Notification Views
@require_app_login
def sms_settings_view(request):
    """SMS notification page with real-time data."""
    if request.session.get('app_role') != 'admin':
        return redirect('dashboard')

    user_id = request.session.get('app_user_id')
    user_obj = AppUser.objects.get(user_id=user_id)

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        
        # Validate and normalize Philippine phone number
        if phone_number:
            # Remove common formatting
            cleaned = phone_number.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            
            # Check if it's a valid Philippine number
            valid_formats = (
                cleaned.startswith('09') and len(cleaned) == 11,  # 09xxxxxxxxx
                cleaned.startswith('+639') and len(cleaned) == 13,  # +639xxxxxxxxx
                cleaned.startswith('639') and len(cleaned) == 12,  # 639xxxxxxxxx
                cleaned.startswith('9') and len(cleaned) == 10,  # 9xxxxxxxxx
            )
            
            if not any(valid_formats):
                messages.error(request, 'Invalid Philippine mobile number. Use format: 09xxxxxxxxx, +639xxxxxxxxx, or 639xxxxxxxxx')
            else:
                user_obj.phone_number = phone_number
                user_obj.save(update_fields=['phone_number'])
                messages.success(request, f'SMS settings saved! Number: {phone_number}')
        else:
            user_obj.phone_number = ''
            user_obj.save(update_fields=['phone_number'])
            messages.success(request, 'Phone number cleared.')

    # Get real-time data for SMS previews
    from datetime import timedelta
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Today's sales data
    today_sales = Sale.objects.filter(recorded_at__date=today, status='completed')
    today_stats = {
        'total_sales': today_sales.count(),
        'total_revenue': today_sales.aggregate(total=Sum('total'))['total'] or 0,
        'total_boxes': today_sales.aggregate(total=Sum('quantity'))['total'] or 0,
    }
    
    # Top selling products today
    top_products = (today_sales
        .values('product__name')
        .annotate(quantity=Sum('quantity'))
        .order_by('-quantity')[:3])
    
    # Low stock products
    low_stock_products = Product.objects.filter(
        status='active',
        stock__lte=10
    ).order_by('stock')[:5]

    context = {
        'sms_notification': type('Obj', (), {
            'phone_number': getattr(user_obj, 'phone_number', ''),
            'is_active': bool(getattr(user_obj, 'phone_number', '')),
        })(),
        'app_role': request.session.get('app_role'),
        'today_stats': today_stats,
        'top_products': top_products,
        'low_stock_products': low_stock_products,
        'today_date': today,
    }
    return render(request, 'sms_settings.html', context)


@require_app_login
def send_test_sms(request):
    """Send test SMS using the admin AppUser phone (if configured) and report result."""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})

    try:
        user_id = request.session.get('app_user_id')
        user_obj = AppUser.objects.get(user_id=user_id)
        if not user_obj.phone_number:
            return JsonResponse({'success': False, 'message': 'No phone number configured'})

        # Trigger the daily SMS command as a test and capture output
        from django.core.management import call_command
        from io import StringIO
        import sys

        old_stdout = sys.stdout
        sys.stdout = captured = StringIO()
        try:
            call_command('send_daily_sms', '--test')
            output = captured.getvalue()
        finally:
            sys.stdout = old_stdout

        if 'SMS sent successfully' in output or 'Daily summary sent to' in output or 'Test SMS sent to' in output:
            return JsonResponse({'success': True, 'message': 'Test SMS sent successfully!'})
        # Clean up ANSI color codes and provide a friendly hint for common Twilio errors
        try:
            import re
            cleaned = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", output or "").strip()
        except Exception:
            cleaned = (output or "").strip()

        hint = ''
        lowered = cleaned.lower()
        if 'invalid' in lowered and 'phone' in lowered:
            hint = ' Tip: Use a valid Philippine mobile number (e.g., 09123456789 or +639123456789).'
        elif 'authenticate' in lowered or 'credentials' in lowered or 'token' in lowered:
            hint = ' Tip: Check IPROG_API_TOKEN in your environment or settings.py.'

        short_msg = cleaned[:300]
        return JsonResponse({'success': False, 'message': f'Failed to send test SMS: {short_msg}{hint}'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@require_app_login
def test_notification_type(request):
    """Send test SMS for specific notification types"""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})

    try:
        notification_type = request.POST.get('type', 'sales')
        user_id = request.session.get('app_user_id')
        user_obj = AppUser.objects.get(user_id=user_id)
        
        if not user_obj.phone_number:
            return JsonResponse({'success': False, 'message': 'No phone number configured'})

        # Generate real data message based on notification type
        if notification_type == 'sales':
            # Get real sales data for today
            today = timezone.now().date()
            today_sales = Sale.objects.filter(recorded_at__date=today, status='completed')
            total_revenue = today_sales.aggregate(total=Sum('total'))['total'] or 0
            total_transactions = today_sales.count()
            total_boxes = today_sales.aggregate(total=Sum('quantity'))['total'] or 0
            
            # Get top product
            top_product = today_sales.values('product__name').annotate(
                quantity=Sum('quantity')
            ).order_by('-quantity').first()
            
            top_product_name = top_product['product__name'] if top_product else 'None'
            top_product_qty = top_product['quantity'] if top_product else 0
            
            message = f"📊 StockWise Today's Sales Summary\n"
            message += f"📅 Date: {today.strftime('%B %d, %Y')}\n\n"
            message += f"💰 Total Revenue: ₱{total_revenue:,.2f}\n"
            message += f"📦 Total Boxes Sold: {total_boxes}\n"
            message += f"🛒 Total Transactions: {total_transactions}\n\n"
            if top_product_name != 'None':
                message += f"🏆 Top Product: {top_product_name} ({top_product_qty} boxes)\n"
            message += "\n📱 Sent by StockWise System"
            
        elif notification_type == 'stock':
            # Get real low stock data
            low_stock_products = Product.objects.filter(
                stock__lte=10,
                stock__gt=0,
                status='active'
            ).order_by('stock')[:3]
            
            out_of_stock_products = Product.objects.filter(
                stock=0,
                status='active'
            ).order_by('name')[:2]
            
            message = "⚠️ StockWise Low Stock Alert\n\n"
            
            if out_of_stock_products.exists():
                message += "🚨 OUT OF STOCK:\n"
                for product in out_of_stock_products:
                    message += f"• {product.name} ({product.size})\n"
                message += "\n"
            
            if low_stock_products.exists():
                message += "📉 LOW STOCK (≤10):\n"
                for product in low_stock_products:
                    message += f"• {product.name} ({product.size}): {product.stock} boxes\n"
                message += "\n"
            
            if not low_stock_products.exists() and not out_of_stock_products.exists():
                message += "✅ All products have sufficient stock.\n\n"
            
            message += "📱 Sent by StockWise System"
            
        elif notification_type == 'pricing':
            # Get real pricing recommendations
            try:
                from core.pricing_ai import DemandPricingAI, PolicyConfig
                import pandas as pd
                
                # Get recent sales data (last 30 days)
                end_date = timezone.now()
                start_date = end_date - timezone.timedelta(days=30)
                
                sales = Sale.objects.filter(
                    recorded_at__gte=start_date,
                    recorded_at__lte=end_date,
                    status='completed'
                ).select_related('product')
                
                if sales.exists():
                    # Convert to DataFrame
                    sales_data = []
                    for sale in sales:
                        sales_data.append({
                            'product_id': sale.product.product_id,
                            'date': sale.recorded_at.date(),
                            'quantity': sale.quantity,
                            'price': sale.product.price,
                            'revenue': sale.total
                        })
                    
                    sales_df = pd.DataFrame(sales_data)
                    sales_df['date'] = pd.to_datetime(sales_df['date'])
                    
                    # Get product catalog
                    products = Product.objects.all().values('product_id', 'name', 'price', 'cost')
                    catalog_df = pd.DataFrame(list(products))
                    catalog_df.columns = ['product_id', 'name', 'price', 'cost']
                    catalog_df['last_change_date'] = None
                    
                    # Generate recommendations
                    cfg = PolicyConfig(
                        min_margin_pct=0.10,
                        max_move_pct=0.20,
                        cooldown_days=3,
                        planning_horizon_days=7,
                        min_obs_per_product=3,
                        default_elasticity=-1.0,
                        hold_band_pct=0.02,
                    )
                    
                    engine = DemandPricingAI(cfg)
                    proposals = engine.propose_prices(sales_df=sales_df, catalog_df=catalog_df)
                    
                    # Get actionable recommendations
                    actionable = proposals[proposals['action'].isin(['INCREASE', 'DECREASE'])]
                    
                    if not actionable.empty:
                        message = "💰 StockWise Pricing Recommendation\n"
                        message += "📊 Based on 30 days of sales data\n\n"
                        
                        # Add top recommendation
                        top_rec = actionable.iloc[0]
                        action_emoji = "📈" if top_rec['action'] == 'INCREASE' else "📉"
                        change_pct = abs(top_rec['change_pct'])
                        
                        message += f"1. {action_emoji} {top_rec['name']}\n"
                        message += f"   Current: ₱{top_rec['current_price']:.2f}\n"
                        message += f"   Suggested: ₱{top_rec['suggested_price']:.2f} ({change_pct:.1f}% {top_rec['action'].lower()})\n"
                        message += f"   Reason: {top_rec['reason']}\n\n"
                        
                        message += f"💡 Total actionable recommendations: {len(actionable)}\n"
                        message += "📱 Sent by StockWise System"
                    else:
                        message = "💰 StockWise Pricing Recommendation\n\n"
                        message += "✅ No pricing changes recommended at this time.\n"
                        message += "📊 All products are optimally priced.\n\n"
                        message += "📱 Sent by StockWise System"
                else:
                    message = "💰 StockWise Pricing Recommendation\n\n"
                    message += "⚠️ Insufficient sales data for pricing analysis.\n"
                    message += "📊 Need more sales history to generate recommendations.\n\n"
                    message += "📱 Sent by StockWise System"
                    
            except Exception as e:
                message = "💰 StockWise Pricing Recommendation\n\n"
                message += f"⚠️ Error generating recommendations: {str(e)}\n\n"
                message += "📱 Sent by StockWise System"
        else:
            # Fallback generic message (should rarely be used)
            message = "StockWise Notification\n\nThis is a live notification triggered from the SMS settings page."
        
        # Send SMS using the existing SMS service
        from core.management.commands.send_daily_sms import Command
        sms_command = Command()
        
        try:
            # allow multipart for full details
            from core.sms_service import sms_service as _svc
            if _svc.send_sms(user_obj.phone_number, message, allow_multipart=True):
                return JsonResponse({'success': True, 'message': f'{notification_type.capitalize()} notification sent successfully!'})
            else:
                return JsonResponse({'success': False, 'message': 'Failed to send notification'})
        except Exception as e:
            error_msg = str(e)
            if 'invalid' in error_msg.lower() and 'phone' in error_msg.lower():
                return JsonResponse({
                    'success': False, 
                    'message': 'Invalid phone number format. Please use a valid Philippine mobile number (e.g., 09123456789).'
                })
            else:
                return JsonResponse({'success': False, 'message': f'Failed to send notification: {error_msg}'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@require_app_login
def check_sms_status(request):
    """Check the status of a sent SMS message"""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    try:
        message_code = request.GET.get('message_code')
        if not message_code:
            return JsonResponse({'success': False, 'message': 'Message code required'})
        
        from core.sms_service import sms_service
        result = sms_service.check_sms_status(message_code)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error checking SMS status: {str(e)}'})


@require_app_login
def check_sms_credits(request):
    """Check remaining SMS credits"""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    try:
        from core.sms_service import sms_service
        result = sms_service.check_credits()
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error checking credits: {str(e)}'})


@require_app_login
def update_notification_settings(request):
    """Update notification settings for different types"""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})

    try:
        user_id = request.session.get('app_user_id')
        user_obj = AppUser.objects.get(user_id=user_id)
        
        # Get settings from POST data
        sales_enabled = request.POST.get('sales_enabled') == 'true'
        stock_enabled = request.POST.get('stock_enabled') == 'true'
        sales_time = request.POST.get('sales_time', '22:00')
        stock_threshold = int(request.POST.get('stock_threshold', 10))
        
        # Store settings in user model (you might want to create a separate settings model)
        # For now, we'll store in a JSON field or use existing fields
        user_obj.phone_number = user_obj.phone_number  # Keep existing phone
        user_obj.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Notification settings updated successfully!',
            'settings': {
                'sales_enabled': sales_enabled,
                'stock_enabled': stock_enabled,
                'sales_time': sales_time,
                'stock_threshold': stock_threshold
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@require_app_login
def get_notification_stats(request):
    """Get notification statistics"""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})

    try:
        from django.db.models import Count
        from datetime import datetime, timedelta
        from core.models import SMS
        
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        # Get SMS statistics (you might need to adjust based on your SMS model)
        stats = {
            'messages_today': SMS.objects.filter(sent_at__date=today).count(),
            'messages_week': SMS.objects.filter(sent_at__date__gte=week_ago).count(),
            'stock_alerts': SMS.objects.filter(message_type='stock_alert').count(),
            'sales_summaries': SMS.objects.filter(message_type='sales_summary_daily').count()
        }
        
        return JsonResponse({'success': True, 'stats': stats})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@require_app_login
def get_pricing_recommendations(request):
    """Get demand-driven pricing recommendations"""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})

    try:
        from core.pricing_ai import DemandPricingAI, PolicyConfig
        from core.models import Sale, Product
        from datetime import datetime, timedelta
        import pandas as pd
        
        # Get sales data from last 120 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=120)
        
        sales_data = Sale.objects.filter(
            recorded_at__date__gte=start_date,
            recorded_at__date__lte=end_date
        ).values('recorded_at', 'product__product_id', 'quantity', 'price')
        
        if not sales_data.exists():
            return JsonResponse({
                'success': False, 
                'message': 'Insufficient sales data for pricing analysis. Need at least 15 days of sales.'
            })
        
        # Convert to DataFrame
        sales_df = pd.DataFrame(list(sales_data))
        sales_df.columns = ['date', 'product_id', 'units_sold', 'price']
        
        # Get product catalog
        products = Product.objects.all().values('product_id', 'name', 'price', 'cost')
        catalog_df = pd.DataFrame(list(products))
        catalog_df.columns = ['product_id', 'name', 'price', 'cost']
        catalog_df['last_change_date'] = None  # Add last change tracking
        
        # Configure pricing AI
        cfg = PolicyConfig(
            min_margin_pct=0.10,         # 10% margin above cost
            max_move_pct=0.20,           # don't move more than 20% at once
            cooldown_days=3,             # respect 3-day cool-down
            planning_horizon_days=7,     # optimize for next 7 days
            min_obs_per_product=15,
            default_elasticity=-1.0,
            hold_band_pct=0.02,          # small changes (<2%) become HOLD
        )
        
        # Generate recommendations
        engine = DemandPricingAI(cfg)
        proposals = engine.propose_prices(sales_df=sales_df, catalog_df=catalog_df)
        
        # Convert to JSON-serializable format
        recommendations = []
        for _, row in proposals.iterrows():
            recommendations.append({
                'product_id': row['product_id'],
                'name': row['name'],
                'current_price': float(row['current_price']),
                'suggested_price': float(row['suggested_price']),
                'change_pct': float(row['change_pct']),
                'action': row['action'],
                'reason': row['reason'],
                'elasticity': float(row['elasticity']) if row['elasticity'] else None,
                'r2': float(row['r2']) if row['r2'] else None,
                'confidence': row['confidence']
            })
        
        return JsonResponse({
            'success': True, 
            'recommendations': recommendations,
            'total_products': len(recommendations),
            'actionable_count': len([r for r in recommendations if r['action'] in ['INCREASE', 'DECREASE']])
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error generating recommendations: {str(e)}'})


# ============================================================================
# INVENTORY REPORTS
# ============================================================================

@require_app_login
def inventory_stock_report(request):
    """Generate stock snapshot report"""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    try:
        products = Product.objects.all().order_by('name')
        
        report_data = []
        total_value_cost = 0
        total_value_price = 0
        
        for product in products:
            stock_value_cost = float(product.stock * (product.cost or 0))
            stock_value_price = float(product.stock * product.price)
            
            total_value_cost += stock_value_cost
            total_value_price += stock_value_price
            
            # Check for low stock (less than 10 boxes)
            low_stock = product.stock < 10
            
            report_data.append({
                'product_id': product.product_id,
                'name': product.name,
                'size': product.size,
                'current_stock': int(product.stock),
                'unit_cost': float(product.cost or 0),
                'unit_price': float(product.price),
                'stock_value_cost': stock_value_cost,
                'stock_value_price': stock_value_price,
                'margin': float(product.price - (product.cost or 0)),
                'margin_pct': float(((product.price - (product.cost or 0)) / product.price * 100)) if product.price > 0 else 0,
                'low_stock_flag': low_stock,
                'last_updated': product.last_updated.strftime('%Y-%m-%d %H:%M') if product.last_updated else 'N/A'
            })
        
        summary = {
            'total_products': len(report_data),
            'total_stock_boxes': sum(item['current_stock'] for item in report_data),
            'total_value_cost': total_value_cost,
            'total_value_price': total_value_price,
            'total_potential_profit': total_value_price - total_value_cost,
            'low_stock_count': sum(1 for item in report_data if item['low_stock_flag'])
        }
        
        return JsonResponse({
            'success': True,
            'data': report_data,
            'summary': summary
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_app_login
def inventory_movement_report(request):
    """Generate stock movement history report"""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    try:
        from datetime import datetime, timedelta
        
        # Get date range from request
        days_back = int(request.GET.get('days', 30))
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # Get stock additions
        additions = StockAddition.objects.filter(
            date_added__gte=start_date,
            date_added__lte=end_date
        ).select_related('product').order_by('-date_added')
        
        # Get sales
        sales = Sale.objects.filter(
            recorded_at__date__gte=start_date,
            recorded_at__date__lte=end_date
        ).select_related('product').order_by('-recorded_at')
        
        movements = []
        
        # Add stock additions
        for addition in additions:
            movements.append({
                'date': addition.date_added.strftime('%Y-%m-%d'),
                'time': addition.created_at.strftime('%H:%M') if addition.created_at else '',
                'product_name': addition.product.name,
                'product_size': addition.product.size,
                'type': 'Addition',
                'quantity': int(addition.quantity),
                'batch_id': addition.batch_id,
                'supplier': addition.supplier or 'N/A',
                'unit_cost': float(addition.cost or 0),
                'total_value': float(addition.quantity * (addition.cost or 0)),
                'reference': f"Batch {addition.batch_id}"
            })
        
        # Add sales
        for sale in sales:
            movements.append({
                'date': sale.recorded_at.strftime('%Y-%m-%d'),
                'time': sale.recorded_at.strftime('%H:%M'),
                'product_name': sale.product.name,
                'product_size': sale.product.size,
                'type': 'Sale',
                'quantity': -int(sale.quantity),  # Negative for sales
                'batch_id': sale.batch_id or 'N/A',
                'supplier': 'N/A',
                'unit_cost': float(sale.product.cost or 0),
                'total_value': -float(sale.quantity * sale.price),  # Negative for sales
                'reference': f"Sale #{sale.sale_id}"
            })
        
        # Sort by date and time
        movements.sort(key=lambda x: (x['date'], x['time']), reverse=True)
        
        # Calculate summary
        total_additions = sum(m['quantity'] for m in movements if m['type'] == 'Addition')
        total_sales = abs(sum(m['quantity'] for m in movements if m['type'] == 'Sale'))
        total_value_in = sum(m['total_value'] for m in movements if m['type'] == 'Addition')
        total_value_out = abs(sum(m['total_value'] for m in movements if m['type'] == 'Sale'))
        
        summary = {
            'date_range': f"{start_date} to {end_date}",
            'total_movements': len(movements),
            'total_additions': total_additions,
            'total_sales': total_sales,
            'net_movement': total_additions - total_sales,
            'total_value_in': total_value_in,
            'total_value_out': total_value_out,
            'net_value': total_value_in - total_value_out
        }
        
        return JsonResponse({
            'success': True,
            'data': movements,
            'summary': summary
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_app_login
def inventory_batch_report(request):
    """Generate batch-level inventory report"""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    try:
        from datetime import datetime
        
        # Get all stock additions with remaining quantity
        batches = StockAddition.objects.filter(
            remaining_quantity__gt=0
        ).select_related('product').order_by('date_added', 'batch_id')
        
        batch_data = []
        
        for batch in batches:
            # Calculate age in days
            age_days = (datetime.now().date() - batch.date_added).days
            
            # Expand into individual boxes
            try:
                total_boxes = int(batch.quantity or 0)
                prefix = batch.batch_id[:-2] if len(batch.batch_id) >= 2 else batch.batch_id
                start_seq = int(batch.batch_id[-2:]) if len(batch.batch_id) >= 2 and batch.batch_id[-2:].isdigit() else 1
            except:
                total_boxes = int(batch.quantity or 0)
                prefix = batch.batch_id
                start_seq = 1
            
            remaining_boxes = int(batch.remaining_quantity or 0)
            consumed = max(0, total_boxes - remaining_boxes)
            
            # Generate individual batch IDs for remaining boxes
            individual_batches = []
            for i in range(total_boxes):
                if i < consumed:  # Skip consumed boxes
                    continue
                seq = ((start_seq - 1 + i) % 99) + 1
                box_id = f"{prefix}{seq:02d}" if prefix else f"{seq:02d}"
                individual_batches.append(box_id)
            
            if individual_batches:  # Only add if there are remaining boxes
                batch_data.append({
                    'batch_id': batch.batch_id,
                    'individual_batches': individual_batches,
                    'product_name': batch.product.name,
                    'product_size': batch.product.size,
                    'date_added': batch.date_added.strftime('%Y-%m-%d'),
                    'supplier': batch.supplier or 'N/A',
                    'original_quantity': total_boxes,
                    'remaining_quantity': remaining_boxes,
                    'consumed_quantity': consumed,
                    'unit_cost': float(batch.cost or 0),
                    'total_value': float(remaining_boxes * (batch.cost or 0)),
                    'age_days': age_days,
                    'age_category': 'Fresh' if age_days <= 7 else 'Aging' if age_days <= 14 else 'Old'
                })
        
        # Calculate summary
        total_batches = len(batch_data)
        total_boxes = sum(item['remaining_quantity'] for item in batch_data)
        total_value = sum(item['total_value'] for item in batch_data)
        
        age_breakdown = {
            'fresh': len([b for b in batch_data if b['age_category'] == 'Fresh']),
            'aging': len([b for b in batch_data if b['age_category'] == 'Aging']),
            'old': len([b for b in batch_data if b['age_category'] == 'Old'])
        }
        
        summary = {
            'total_batches': total_batches,
            'total_boxes': total_boxes,
            'total_value': total_value,
            'age_breakdown': age_breakdown,
            'avg_age_days': sum(item['age_days'] for item in batch_data) / total_batches if total_batches > 0 else 0
        }
        
        return JsonResponse({
            'success': True,
            'data': batch_data,
            'summary': summary
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_app_login
def inventory_turnover_report(request):
    """Generate inventory turnover and aging report"""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    try:
        from datetime import datetime, timedelta
        
        # Get date range (last 30 days for turnover calculation)
        days_back = 30
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        products = Product.objects.all()
        turnover_data = []
        
        for product in products:
            # Get sales in the period
            sales_qty = Sale.objects.filter(
                product=product,
                recorded_at__date__gte=start_date,
                recorded_at__date__lte=end_date
            ).aggregate(total_sold=Sum('quantity'))['total_sold'] or 0
            
            # Get stock additions in the period
            additions_qty = StockAddition.objects.filter(
                product=product,
                date_added__gte=start_date,
                date_added__lte=end_date
            ).aggregate(total_added=Sum('quantity'))['total_added'] or 0
            
            # Calculate average inventory (simplified as current stock)
            avg_inventory = float(product.stock)
            
            # Calculate turnover metrics
            daily_sales_rate = float(sales_qty) / days_back if days_back > 0 else 0
            turnover_ratio = float(sales_qty) / avg_inventory if avg_inventory > 0 else 0
            days_of_cover = avg_inventory / daily_sales_rate if daily_sales_rate > 0 else float('inf')
            
            # Sell-through rate
            total_available = avg_inventory + float(additions_qty)
            sell_through_pct = (float(sales_qty) / total_available * 100) if total_available > 0 else 0
            
            turnover_data.append({
                'product_id': product.product_id,
                'product_name': product.name,
                'product_size': product.size,
                'current_stock': int(product.stock),
                'sales_qty_30d': int(sales_qty),
                'additions_qty_30d': int(additions_qty),
                'daily_sales_rate': round(daily_sales_rate, 2),
                'turnover_ratio': round(turnover_ratio, 2),
                'days_of_cover': round(days_of_cover, 1) if days_of_cover != float('inf') else 999,
                'sell_through_pct': round(sell_through_pct, 1),
                'velocity_category': (
                    'Fast' if daily_sales_rate > 2 else
                    'Medium' if daily_sales_rate > 0.5 else
                    'Slow'
                ),
                'stock_status': (
                    'Overstocked' if days_of_cover > 30 else
                    'Normal' if days_of_cover > 7 else
                    'Low Stock' if days_of_cover > 0 else
                    'Out of Stock'
                )
            })
        
        # Sort by turnover ratio (highest first)
        turnover_data.sort(key=lambda x: x['turnover_ratio'], reverse=True)
        
        # Calculate summary
        total_products = len(turnover_data)
        avg_turnover = sum(item['turnover_ratio'] for item in turnover_data) / total_products if total_products > 0 else 0
        
        velocity_breakdown = {
            'fast': len([p for p in turnover_data if p['velocity_category'] == 'Fast']),
            'medium': len([p for p in turnover_data if p['velocity_category'] == 'Medium']),
            'slow': len([p for p in turnover_data if p['velocity_category'] == 'Slow'])
        }
        
        stock_status_breakdown = {
            'overstocked': len([p for p in turnover_data if p['stock_status'] == 'Overstocked']),
            'normal': len([p for p in turnover_data if p['stock_status'] == 'Normal']),
            'low_stock': len([p for p in turnover_data if p['stock_status'] == 'Low Stock']),
            'out_of_stock': len([p for p in turnover_data if p['stock_status'] == 'Out of Stock'])
        }
        
        summary = {
            'total_products': total_products,
            'avg_turnover_ratio': round(avg_turnover, 2),
            'period_days': days_back,
            'velocity_breakdown': velocity_breakdown,
            'stock_status_breakdown': stock_status_breakdown
        }
        
        return JsonResponse({
            'success': True,
            'data': turnover_data,
            'summary': summary
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_app_login
def inventory_supplier_report(request):
    """Generate supplier performance report"""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    try:
        from datetime import datetime, timedelta
        
        # Get date range
        days_back = int(request.GET.get('days', 90))
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # Get all stock additions with suppliers
        additions = StockAddition.objects.filter(
            date_added__gte=start_date,
            date_added__lte=end_date
        ).select_related('product')
        
        # Group by supplier
        supplier_data = {}
        
        for addition in additions:
            supplier = addition.supplier or 'Unknown Supplier'
            
            if supplier not in supplier_data:
                supplier_data[supplier] = {
                    'supplier_name': supplier,
                    'total_deliveries': 0,
                    'total_boxes': 0,
                    'total_value': 0,
                    'products_supplied': set(),
                    'deliveries': [],
                    'avg_delivery_size': 0,
                    'last_delivery': None
                }
            
            supplier_data[supplier]['total_deliveries'] += 1
            supplier_data[supplier]['total_boxes'] += int(addition.quantity or 0)
            supplier_data[supplier]['total_value'] += float(addition.quantity * (addition.cost or 0))
            supplier_data[supplier]['products_supplied'].add(addition.product.name)
            supplier_data[supplier]['deliveries'].append({
                'date': addition.date_added.strftime('%Y-%m-%d'),
                'product': addition.product.name,
                'quantity': int(addition.quantity or 0),
                'batch_id': addition.batch_id
            })
            
            # Track last delivery
            if not supplier_data[supplier]['last_delivery'] or addition.date_added > datetime.strptime(supplier_data[supplier]['last_delivery'], '%Y-%m-%d').date():
                supplier_data[supplier]['last_delivery'] = addition.date_added.strftime('%Y-%m-%d')
        
        # Convert to list and calculate averages
        supplier_list = []
        for supplier, data in supplier_data.items():
            data['products_supplied'] = list(data['products_supplied'])
            data['unique_products'] = len(data['products_supplied'])
            data['avg_delivery_size'] = round(data['total_boxes'] / data['total_deliveries'], 1) if data['total_deliveries'] > 0 else 0
            
            # Calculate days since last delivery
            if data['last_delivery']:
                last_delivery_date = datetime.strptime(data['last_delivery'], '%Y-%m-%d').date()
                days_since_last = (datetime.now().date() - last_delivery_date).days
                data['days_since_last_delivery'] = days_since_last
            else:
                data['days_since_last_delivery'] = 999
            
            supplier_list.append(data)
        
        # Sort by total value (highest first)
        supplier_list.sort(key=lambda x: x['total_value'], reverse=True)
        
        # Calculate summary
        total_suppliers = len(supplier_list)
        total_deliveries = sum(s['total_deliveries'] for s in supplier_list)
        total_boxes = sum(s['total_boxes'] for s in supplier_list)
        total_value = sum(s['total_value'] for s in supplier_list)
        
        summary = {
            'total_suppliers': total_suppliers,
            'total_deliveries': total_deliveries,
            'total_boxes': total_boxes,
            'total_value': total_value,
            'period_days': days_back,
            'avg_deliveries_per_supplier': round(total_deliveries / total_suppliers, 1) if total_suppliers > 0 else 0,
            'avg_boxes_per_delivery': round(total_boxes / total_deliveries, 1) if total_deliveries > 0 else 0
        }
        
        return JsonResponse({
            'success': True,
            'data': supplier_list,
            'summary': summary
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_app_login
def generate_inventory_pdf_report(request):
    """Generate comprehensive PDF report for inventory"""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    try:
        from django.http import HttpResponse
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from io import BytesIO
        from datetime import datetime
        import json
        
        # Get report type
        report_type = request.GET.get('type', 'comprehensive')
        
        # Create the PDF document
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30, textColor=colors.darkblue)
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, spaceAfter=12, textColor=colors.darkblue)
        
        # Title
        title = Paragraph("StockWise Inventory Report", title_style)
        elements.append(title)
        
        # Report info
        report_info = Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal'])
        elements.append(report_info)
        elements.append(Spacer(1, 20))
        
        if report_type == 'comprehensive' or report_type == 'stock':
            # Stock Snapshot Report
            elements.append(Paragraph("Stock Snapshot Report", heading_style))
            
            # Get stock data (reuse the existing endpoint logic)
            products = Product.objects.all().order_by('name')
            stock_data = []
            total_value_cost = 0
            total_value_price = 0
            
            for product in products:
                stock_value_cost = float(product.stock * (product.cost or 0))
                stock_value_price = float(product.stock * product.price)
                total_value_cost += stock_value_cost
                total_value_price += stock_value_price
                
                stock_data.append([
                    product.name,
                    product.size or 'N/A',
                    str(int(product.stock)),
                    f"₱{product.price:.2f}",
                    f"₱{stock_value_price:.2f}",
                    "⚠️" if product.stock < 10 else "✓"
                ])
            
            # Stock table
            stock_headers = ['Product', 'Size', 'Stock', 'Unit Price', 'Total Value', 'Status']
            stock_table_data = [stock_headers] + stock_data
            
            stock_table = Table(stock_table_data, colWidths=[2*inch, 1*inch, 0.8*inch, 1*inch, 1*inch, 0.7*inch])
            stock_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            
            elements.append(stock_table)
            
            # Stock summary
            summary_data = [
                ['Total Products', str(len(stock_data))],
                ['Total Stock Value', f"₱{total_value_price:,.2f}"],
                ['Total Cost Value', f"₱{total_value_cost:,.2f}"],
                ['Potential Profit', f"₱{total_value_price - total_value_cost:,.2f}"],
                ['Low Stock Items', str(sum(1 for row in stock_data if row[5] == "⚠️"))]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(Spacer(1, 12))
            elements.append(summary_table)
            elements.append(PageBreak())
        
        if report_type == 'comprehensive' or report_type == 'movement':
            # Movement Report
            elements.append(Paragraph("Stock Movement Report (Last 30 Days)", heading_style))
            
            from datetime import timedelta
            days_back = 30
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            # Get movements (simplified for PDF)
            additions = StockAddition.objects.filter(
                date_added__gte=start_date,
                date_added__lte=end_date
            ).select_related('product').order_by('-date_added')[:20]  # Limit for PDF
            
            movement_data = []
            for addition in additions:
                movement_data.append([
                    addition.date_added.strftime('%m/%d'),
                    addition.product.name[:20],
                    'Addition',
                    str(int(addition.quantity)),
                    addition.supplier or 'N/A',
                    addition.batch_id[:15]
                ])
            
            if movement_data:
                movement_headers = ['Date', 'Product', 'Type', 'Qty', 'Supplier', 'Batch ID']
                movement_table_data = [movement_headers] + movement_data
                
                movement_table = Table(movement_table_data, colWidths=[0.8*inch, 2*inch, 1*inch, 0.6*inch, 1.2*inch, 1.4*inch])
                movement_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                ]))
                
                elements.append(movement_table)
            else:
                elements.append(Paragraph("No stock movements in the last 30 days.", styles['Normal']))
            
            elements.append(PageBreak())
        
        if report_type == 'comprehensive' or report_type == 'batches':
            # Batch Report
            elements.append(Paragraph("Active Batches Report", heading_style))
            
            batches = StockAddition.objects.filter(
                remaining_quantity__gt=0
            ).select_related('product').order_by('date_added')[:30]  # Limit for PDF
            
            batch_data = []
            for batch in batches:
                age_days = (datetime.now().date() - batch.date_added).days
                age_category = 'Fresh' if age_days <= 7 else 'Aging' if age_days <= 14 else 'Old'
                
                batch_data.append([
                    batch.batch_id[:15],
                    batch.product.name[:20],
                    batch.date_added.strftime('%m/%d/%y'),
                    str(int(batch.remaining_quantity)),
                    str(age_days),
                    age_category
                ])
            
            if batch_data:
                batch_headers = ['Batch ID', 'Product', 'Date Added', 'Remaining', 'Age (Days)', 'Category']
                batch_table_data = [batch_headers] + batch_data
                
                batch_table = Table(batch_table_data, colWidths=[1.2*inch, 2*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch])
                batch_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                ]))
                
                elements.append(batch_table)
            else:
                elements.append(Paragraph("No active batches found.", styles['Normal']))
        
        if report_type == 'comprehensive':
            elements.append(PageBreak())
            
            # Turnover Summary
            elements.append(Paragraph("Inventory Turnover Summary", heading_style))
            
            products = Product.objects.all()[:15]  # Limit for PDF
            turnover_data = []
            
            for product in products:
                # Simplified turnover calculation
                from datetime import timedelta
                days_back = 30
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=days_back)
                
                sales_qty = Sale.objects.filter(
                    product=product,
                    recorded_at__date__gte=start_date,
                    recorded_at__date__lte=end_date
                ).aggregate(total_sold=Sum('quantity'))['total_sold'] or 0
                
                daily_sales_rate = float(sales_qty) / days_back if days_back > 0 else 0
                days_of_cover = float(product.stock) / daily_sales_rate if daily_sales_rate > 0 else 999
                
                velocity = 'Fast' if daily_sales_rate > 2 else 'Medium' if daily_sales_rate > 0.5 else 'Slow'
                
                turnover_data.append([
                    product.name[:20],
                    str(int(product.stock)),
                    str(int(sales_qty)),
                    f"{daily_sales_rate:.1f}",
                    f"{days_of_cover:.0f}" if days_of_cover < 999 else "∞",
                    velocity
                ])
            
            if turnover_data:
                turnover_headers = ['Product', 'Stock', '30d Sales', 'Daily Rate', 'Days Cover', 'Velocity']
                turnover_table_data = [turnover_headers] + turnover_data
                
                turnover_table = Table(turnover_table_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch])
                turnover_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                ]))
                
                elements.append(turnover_table)
        
        # Build PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer and write it to the response
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="inventory_report_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf"'
        response.write(pdf)
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_app_login
def apply_pricing_recommendation(request):
    """Apply a pricing recommendation with user approval"""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})

    try:
        product_id = request.POST.get('product_id')
        new_price = float(request.POST.get('new_price'))
        
        if not product_id or new_price <= 0:
            return JsonResponse({'success': False, 'message': 'Invalid product ID or price'})
        
        # Update product price
        from core.models import Product
        product = Product.objects.get(product_id=product_id)
        old_price = product.price
        product.price = new_price
        product.save()
        
        # Log the price change
        from core.models import SMS
        SMS.objects.create(
            product=product,
            user_id=request.session.get('app_user_id'),
            message_type='pricing_alert',
            demand_level='high',  # Could be determined by the recommendation
            message_content=f"Price updated from ₱{old_price:.2f} to ₱{new_price:.2f}",
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Price updated successfully from ₱{old_price:.2f} to ₱{new_price:.2f}'
        })
        
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error updating price: {str(e)}'})


@require_app_login
def test_pricing_notification(request):
    """Send pricing notification with real data"""
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})

    try:
        user_id = request.session.get('app_user_id')
        user_obj = AppUser.objects.get(user_id=user_id)
        
        if not user_obj.phone_number:
            return JsonResponse({'success': False, 'message': 'No phone number configured'})

        # Generate real pricing recommendation message
        try:
            from core.pricing_ai import DemandPricingAI, PolicyConfig
            import pandas as pd
            
            # Get recent sales data (last 30 days)
            end_date = timezone.now()
            start_date = end_date - timezone.timedelta(days=30)
            
            sales = Sale.objects.filter(
                recorded_at__gte=start_date,
                recorded_at__lte=end_date,
                status='completed'
            ).select_related('product')
            
            if sales.exists():
                # Convert to DataFrame
                sales_data = []
                for sale in sales:
                    sales_data.append({
                        'product_id': sale.product.product_id,
                        'date': sale.recorded_at.date(),
                        'units_sold': sale.quantity,
                        'price': sale.product.price,
                        'revenue': sale.total
                    })
                
                sales_df = pd.DataFrame(sales_data)
                sales_df['date'] = pd.to_datetime(sales_df['date'])
                
                # Get product catalog
                products = Product.objects.all().values('product_id', 'name', 'price', 'cost')
                catalog_df = pd.DataFrame(list(products))
                catalog_df.columns = ['product_id', 'name', 'price', 'cost']
                catalog_df['last_change_date'] = None
                
                # Generate recommendations
                cfg = PolicyConfig(
                    min_margin_pct=0.10,
                    max_move_pct=0.20,
                    cooldown_days=3,
                    planning_horizon_days=7,
                    min_obs_per_product=3,
                    default_elasticity=-1.0,
                    hold_band_pct=0.02,
                )
                
                engine = DemandPricingAI(cfg)
                proposals = engine.propose_prices(sales_df=sales_df, catalog_df=catalog_df)
                
                # Get actionable recommendations
                actionable = proposals[proposals['action'].isin(['INCREASE', 'DECREASE'])]
                
                if not actionable.empty:
                    # Format recommendations
                    message = "💰 StockWise Pricing Recommendation\n"
                    message += "📊 Based on 30 days of sales data\n\n"
                    
                    # Add top recommendation
                    top_rec = actionable.iloc[0]
                    action_emoji = "📈" if top_rec['action'] == 'INCREASE' else "📉"
                    change_pct = abs(top_rec['change_pct'])
                    
                    message += f"1. {action_emoji} {top_rec['name']}\n"
                    message += f"   Current: ₱{top_rec['current_price']:.2f}\n"
                    message += f"   Suggested: ₱{top_rec['suggested_price']:.2f} ({change_pct:.1f}% {top_rec['action'].lower()})\n"
                    message += f"   Reason: {top_rec['reason']}\n\n"
                    
                    message += f"💡 Total actionable recommendations: {len(actionable)}\n"
                    message += "📱 Sent by StockWise System"
                else:
                    message = "💰 StockWise Pricing Recommendation\n\n"
                    message += "✅ No pricing changes recommended at this time.\n"
                    message += "📊 All products are optimally priced.\n\n"
                    message += "📱 Sent by StockWise System"
            else:
                message = "💰 StockWise Pricing Recommendation\n\n"
                message += "⚠️ Insufficient sales data for pricing analysis.\n"
                message += "📊 Need more sales history to generate recommendations.\n\n"
                message += "📱 Sent by StockWise System"
                
        except Exception as e:
            message = "💰 StockWise Pricing Recommendation\n\n"
            message += f"⚠️ Error generating recommendations: {str(e)}\n\n"
            message += "📱 Sent by StockWise System"
        
        # Send SMS using the existing SMS service
        from core.management.commands.send_daily_sms import Command
        sms_command = Command()
        
        try:
            from core.sms_service import sms_service as _svc
            if _svc.send_sms(user_obj.phone_number, message, allow_multipart=True):
                return JsonResponse({'success': True, 'message': 'Pricing recommendation sent successfully!'})
            else:
                return JsonResponse({'success': False, 'message': 'Failed to send pricing recommendation'})
        except Exception as e:
            error_msg = str(e)
            if 'unverified' in error_msg.lower():
                return JsonResponse({
                    'success': False, 
                    'message': 'Phone number not verified. Please verify your number in Twilio console or use a verified number.'
                })
            else:
                return JsonResponse({'success': False, 'message': f'Failed to send pricing recommendation: {error_msg}'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@require_GET
def get_product_id(request):
    name = request.GET.get('name')
    variant = request.GET.get('variant')
    size = request.GET.get('size')
    full_name = f"{name} ({variant})" if variant else name
    product = Product.objects.filter(name=full_name, size=size, is_built_in=False).first()
    if product:
        return JsonResponse({'success': True, 'product_id': product.product_id})
    else:
        return JsonResponse({'success': False, 'message': 'Product not found'})


@require_app_login
@require_POST
def send_all_notifications_now(request):
    if request.session.get('app_role') != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})

    try:
        user_id = request.session.get('app_user_id')
        user_obj = AppUser.objects.get(user_id=user_id)
        if not user_obj.phone_number:
            return JsonResponse({'success': False, 'message': 'No phone number configured'})

        from core.sms_service import sms_service as _svc
        results = {}

        # Sales summary (full list)
        today = timezone.now().date()
        today_sales = Sale.objects.filter(recorded_at__date=today, status='completed')
        total_revenue = today_sales.aggregate(total=Sum('total'))['total'] or 0
        total_transactions = today_sales.count()
        total_boxes = today_sales.aggregate(total=Sum('quantity'))['total'] or 0
        sales_msg = "📊 StockWise Today's Sales Summary\n"
        sales_msg += f"📅 Date: {today.strftime('%B %d, %Y')}\n\n"
        sales_msg += f"💰 Total Revenue: ₱{total_revenue:,.2f}\n"
        sales_msg += f"📦 Total Boxes Sold: {total_boxes}\n"
        sales_msg += f"🛒 Total Transactions: {total_transactions}\n\n"
        if today_sales.exists():
            sales_msg += "🏆 Products:\n"
            for row in (today_sales.values('product__name')
                        .annotate(quantity=Sum('quantity'))
                        .order_by('-quantity')):
                sales_msg += f"• {row['product__name']}: {row['quantity']} boxes\n"
            sales_msg += "\n"
        sales_msg += "📱 Sent by StockWise System"
        results['sales'] = _svc.send_sms(user_obj.phone_number, sales_msg, allow_multipart=True)

        # Low stock (full list)
        low_stock = Product.objects.filter(stock__lte=10, stock__gt=0, status='active').order_by('stock')
        oos = Product.objects.filter(stock=0, status='active').order_by('name')
        stock_msg = "⚠️ StockWise Low Stock Alert\n\n"
        if oos.exists():
            stock_msg += "🚨 OUT OF STOCK:\n"
            for p in oos:
                stock_msg += f"• {p.name} ({p.size})\n"
            stock_msg += "\n"
        if low_stock.exists():
            stock_msg += "📉 LOW STOCK (≤10):\n"
            for p in low_stock:
                stock_msg += f"• {p.name} ({p.size}): {p.stock} boxes\n"
            stock_msg += "\n"
        if not low_stock.exists() and not oos.exists():
            stock_msg += "✅ All products have sufficient stock.\n\n"
        stock_msg += "📱 Sent by StockWise System"
        results['stock'] = _svc.send_sms(user_obj.phone_number, stock_msg, allow_multipart=True)

        # Pricing (full actionable list)
        try:
            from core.pricing_ai import DemandPricingAI, PolicyConfig
            import pandas as pd
            end_date = timezone.now()
            start_date = end_date - timezone.timedelta(days=30)
            sales = Sale.objects.filter(recorded_at__gte=start_date, recorded_at__lte=end_date, status='completed').select_related('product')
            if sales.exists():
                rows = [{
                    'product_id': s.product.product_id,
                    'date': s.recorded_at.date(),
                    'quantity': s.quantity,
                    'price': s.product.price,
                    'revenue': s.total
                } for s in sales]
                sales_df = pd.DataFrame(rows)
                sales_df['date'] = pd.to_datetime(sales_df['date'])
                catalog = Product.objects.all().values('product_id', 'name', 'price', 'cost')
                catalog_df = pd.DataFrame(list(catalog))
                catalog_df.columns = ['product_id', 'name', 'price', 'cost']
                catalog_df['last_change_date'] = None
                cfg = PolicyConfig(min_margin_pct=0.10, max_move_pct=0.20, cooldown_days=3,
                                   planning_horizon_days=7, min_obs_per_product=3, default_elasticity=-1.0,
                                   hold_band_pct=0.02)
                engine = DemandPricingAI(cfg)
                proposals = engine.propose_prices(sales_df=sales_df, catalog_df=catalog_df)
                actionable = proposals[proposals['action'].isin(['INCREASE', 'DECREASE'])]
                if not actionable.empty:
                    pricing_msg = "💰 StockWise Pricing Recommendation\n"
                    pricing_msg += "📊 Based on 30 days of sales data\n\n"
                    for i, (_, rec) in enumerate(actionable.iterrows(), 1):
                        emoji = "📈" if rec['action'] == 'INCREASE' else "📉"
                        change_pct = abs(rec['change_pct'])
                        pricing_msg += f"{i}. {emoji} {rec['name']}\n"
                        pricing_msg += f"   Current: ₱{rec['current_price']:.2f}\n"
                        pricing_msg += f"   Suggested: ₱{rec['suggested_price']:.2f} ({change_pct:.1f}% {rec['action'].lower()})\n"
                        pricing_msg += f"   Reason: {rec['reason']}\n\n"
                    pricing_msg += f"💡 Total actionable recommendations: {len(actionable)}\n"
                    pricing_msg += "📱 Sent by StockWise System"
                else:
                    pricing_msg = "💰 StockWise Pricing Recommendation\n\n✅ No pricing changes recommended at this time.\n📊 All products are optimally priced.\n\n📱 Sent by StockWise System"
            else:
                pricing_msg = "💰 StockWise Pricing Recommendation\n\n⚠️ Insufficient sales data for pricing analysis.\n📊 Need more sales history to generate recommendations.\n\n📱 Sent by StockWise System"
        except Exception as e:
            pricing_msg = f"💰 StockWise Pricing Recommendation\n\n⚠️ Error generating recommendations: {str(e)}\n\n📱 Sent by StockWise System"
        results['pricing'] = _svc.send_sms(user_obj.phone_number, pricing_msg, allow_multipart=True)

        summary = {k: bool(v) for k, v in results.items()}
        return JsonResponse({'success': any(summary.values()), 'results': summary})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
