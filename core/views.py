from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.utils import timezone
from django.core import signing
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
import os
import csv
from django.conf import settings
from django.db.models import Sum, Count, Q, F, Case, When, CharField, Value
from django.db.models.functions import Coalesce, Substr
from .models import AppUser, Product, Sale, StockAddition, SMS, ReportProductSummary
import json
from django.db import transaction
from django.http import JsonResponse
 
from datetime import datetime, timedelta
from decimal import Decimal
from io import StringIO
import csv
from django.http import HttpResponse

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
					return redirect('dashboard')
				else:
					messages.error(request, 'Password is incorrect.')
		except Exception as exc:
			messages.error(request, f'Login error: {exc}')
	return render(request, 'login.html')


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

        # Base queryset: only products actually added to inventory. If the column doesn't exist yet,
        # avoid querying it and return none (so built-ins don't leak into the list).
        try:
            # is_inventory may not exist; rely on is_built_in flag
            products = Product.objects.filter(is_built_in=False)
        except Exception:
            products = Product.objects.none()

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

        # Calculate dashboard stats
        total_products = products.count()
        active_products = products.filter(status='active').count()
        total_stock = products.aggregate(total=Sum('stock'))['total'] or 0
        restock_alerts = products.filter(status='active', stock__lt=10).count()

        # Get unique fruits and suppliers for client-side dropdown
        unique_fruits = list(Product.objects.filter(is_built_in=True).values_list('name', flat=True).distinct())
        unique_suppliers = list(Product.objects.filter(is_built_in=False).exclude(supplier__isnull=True).exclude(supplier='').values_list('supplier', flat=True).distinct())
        
        context = {
            'products': products,
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
    context = {
        'app_role': request.session.get('app_role', 'user'),
        'today': timezone.now().date(),
        'show_cost': request.session.get('app_role') == 'admin',
    }
    return render(request, 'record_sale.html', context)

@require_app_login
def add_stock_page(request):
    """Standalone page that mirrors the Add Stock modal (UI + JS)."""
    context = {
        'app_role': request.session.get('app_role', 'user'),
        'today': timezone.now().date(),
    }
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
					StockAddition.objects.create(
						product=product,
						quantity=int(quantity),
						date_added=date_added or timezone.now().date(),
						remaining_quantity=int(quantity),
						batch_id=batch_id,
						supplier=supplier
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

    # Base query for completed sales
    sales_query = Sale.objects.filter(status='completed')
    
    # Apply date filters
    if filter_type == 'Daily':
        sales_query = sales_query.filter(recorded_at__date=today)
    elif filter_type == 'Weekly':
        sales_query = sales_query.filter(recorded_at__gte=timezone.now() - timedelta(days=7))
    elif filter_type == 'Monthly':
        sales_query = sales_query.filter(recorded_at__gte=timezone.now() - timedelta(days=30))
    elif filter_type == 'Custom' and start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            sales_query = sales_query.filter(recorded_at__date__range=[start, end])
        except ValueError:
            # Invalid date format, fallback to daily
            sales_query = sales_query.filter(recorded_at__date=today)

    # Apply search filter if provided
    if search:
        if search.isdigit():
            # Search by sale ID
            sales_query = sales_query.filter(sale_id=search)
        else:
            # Try parsing as date
            try:
                search_date = datetime.strptime(search, '%B %d, %Y').date()
                sales_query = sales_query.filter(recorded_at__date=search_date)
            except ValueError:
                # Search by product name or size
                sales_query = sales_query.filter(
                    Q(items__product__name__icontains=search) |
                    Q(items__product__size__icontains=search)
                ).distinct()

    # Calculate statistics
    total_sales = sales_query.count()
    total_boxes = sales_query.aggregate(total=Sum('quantity'))['total'] or 0
    total_revenue = sales_query.aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')

    # Get sales with related data
    sales = sales_query.select_related('product', 'user').order_by('-recorded_at')

    # Format sales data for template
    sales_data = []
    for sale in sales:
        sales_data.append({
            'sale_id': sale.sale_id,
            'recorded_at': sale.recorded_at.strftime('%b %d, %Y %I:%M %p'),
            'items': [{
                'product_name': sale.product.name,
                'size': sale.product.size,
                'quantity': sale.quantity,
                'price': sale.price,
                'subtotal': sale.total
            }],
            'items_json': [{
                'product_name': sale.product.name,
                'size': sale.product.size,
                'quantity': sale.quantity,
                'price': sale.price,
                'subtotal': sale.total
            }],
            'total': sale.total,
            'status': sale.status,
            'product_count': 1,
            'total_boxes': sale.quantity,
            'products': sale.product.name
        })

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
                    'quantity': sale.quantity,
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
        sales_query = Sale.objects.filter(status=status.lower())

        # Apply filters (same logic as sales_view)
        if filter_type == 'Daily':
            sales_query = sales_query.filter(recorded_at__date=timezone.now().date())
        elif filter_type == 'Weekly':
            sales_query = sales_query.filter(recorded_at__gte=timezone.now() - timedelta(days=7))
        elif filter_type == 'Monthly':
            sales_query = sales_query.filter(recorded_at__gte=timezone.now() - timedelta(days=30))
        elif filter_type == 'Custom' and start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                sales_query = sales_query.filter(recorded_at__date__range=[start, end])
            except ValueError:
                sales_query = sales_query.filter(recorded_at__date=timezone.now().date())

        # Apply search
        if search:
            if search.isdigit():
                sales_query = sales_query.filter(sale_id=search)
            else:
                try:
                    search_date = datetime.strptime(search, '%B %d, %Y').date()
                    sales_query = sales_query.filter(recorded_at__date=search_date)
                except ValueError:
                    sales_query = sales_query.filter(
                        Q(items__product__name__icontains=search) |
                        Q(items__product__size__icontains=search)
                    ).distinct()

        # Get sales with related data
        sales = sales_query.prefetch_related(
            'items__product'
        ).select_related('user').order_by('-recorded_at')

        # Format response data
        sales_data = []
        for sale in sales:
            items = sale.items.all()
            items_data = [{
                'product_name': item.product.name,
                'size': item.product.size,
                'quantity': item.quantity,
                'price': item.product.price,
                'subtotal': item.subtotal
            } for item in items]
            
            sale_dict = {
                'sale_id': sale.sale_id,
                'recorded_at': sale.recorded_at.strftime('%b %d, %Y %I:%M %p'),
                'items': items_data,
                'items_json': items_data,
                'total': str(sale.total),
                'status': sale.status,
                'product_count': len(items),
                'total_boxes': sum(item.quantity for item in items),
                'products': ', '.join(item.product.name for item in items)
            }

            if status == 'voided' and sale.voided_at:
                days_passed = (timezone.now() - sale.voided_at).days
                sale_dict['days_until_deletion'] = max(0, 30 - days_passed)

            sales_data.append(sale_dict)

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
def _apply_report_filters(queryset, filter_type, start_date, end_date):
    today = timezone.now().date()
    if filter_type == 'Daily':
        queryset = queryset.filter(recorded_at__date=today)
    elif filter_type == 'Weekly':
        queryset = queryset.filter(recorded_at__gte=timezone.now()-timedelta(days=7))
    elif filter_type == 'Monthly':
        queryset = queryset.filter(recorded_at__gte=timezone.now()-timedelta(days=30))
    elif filter_type == 'Custom' and start_date and end_date:
        try:
            s = datetime.strptime(start_date,'%Y-%m-%d').date()
            e = datetime.strptime(end_date,'%Y-%m-%d').date()
            queryset = queryset.filter(recorded_at__date__range=[s,e])
        except ValueError:
            queryset = queryset.filter(recorded_at__date=today)
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

    try:
        sales_q=Sale.objects.filter(status__iexact='completed').prefetch_related('items__product')
        sales_q=_apply_report_filters(sales_q,filter_type,start_date,end_date)
        if search:
            if search.isdigit():
                sales_q=sales_q.filter(sale_id=search)
            else:
                sales_q=sales_q.filter(Q(items__product__name__icontains=search)|Q(items__product__size__icontains=search)).distinct()

        # sales_summary
        agg=sales_q.aggregate(total_revenue=Sum(F('items__quantity')*F('items__product__price')),transaction_count=Count('sale_id',distinct=True),total_items_sold=Sum('items__quantity'))
        total_rev=agg['total_revenue'] or Decimal('0.00')
        trans_cnt=agg['transaction_count'] or 0
        total_boxes=agg['total_items_sold'] or 0
        sales_summary={
            'total_revenue':float(total_rev),
            'transaction_count':trans_cnt,
            'total_items_sold':total_boxes,
            'avg_order_value': float(total_rev/trans_cnt) if trans_cnt else 0
        }

        # top fruits - using single-table sales
        top=sales_q.values('product__product_id','product__name','product__size').annotate(boxes_sold=Sum('quantity'),revenue=Sum(F('quantity')*F('product__price'))).order_by('-boxes_sold')[:5]
        top_fruits=[{
            'product_id':t['product__product_id'],
            'name':t['product__name'],
            'size':t['product__size'],
            'boxes_sold':t['boxes_sold'],
            'revenue':float(t['revenue']) if t['revenue'] else 0
        } for t in top]

        # fruit summary - using single-table sales
        fs=sales_q.values('product__product_id','product__name','product__size','product__price').annotate(boxes_sold=Sum('quantity'),revenue=Sum(F('quantity')*F('product__price'))).order_by('-revenue')
        fruit_summary=[{
            'product_id':r['product__product_id'],
            'name':r['product__name'],
            'size':r['product__size'],
            'boxes_sold':r['boxes_sold'],
            'price_per_box':float(r['product__price']),
            'revenue':float(r['revenue']) if r['revenue'] else 0
        } for r in fs]

        # low stock fruits - using Product model directly
        low_q=Product.objects.filter(stock__lte=10,status='Active').order_by('stock')
        low_stock=[{
            'product_id':inv.product_id,
            'name':inv.name,
            'size':inv.size,
            'stock':inv.stock,
            'price':float(inv.price)
        } for inv in low_q]

        # transactions - using single-table sales
        tx_data=[]
        for sale in sales_q.order_by('-recorded_at')[:100]:
            tx_data.append({
                'sale_id':sale.sale_id,
                'recorded_at':sale.recorded_at.strftime('%Y-%m-%d %H:%M:%S'),
                'total':float(sale.total),
                'status':sale.status,
                'fruit_count':1,
                'total_boxes':sale.quantity,
                'fruits':sale.product.name if sale.product else 'Unknown',
                'sizes':sale.product.size if sale.product else '',
            })

        return JsonResponse({'success':True,'data':{
            'sales_summary':sales_summary,
            'top_fruits':top_fruits,
            'fruit_summary':fruit_summary,
            'low_stock':low_stock,
            'transactions':tx_data
        }})
    except Exception as e:
        return JsonResponse({'success':False,'message':str(e)})

@require_app_login
def export_report(request):
    if request.method!='POST' or request.session.get('app_role')!='admin':
        return JsonResponse({'success':False,'message':'Forbidden'},status=403)
    report_type=request.POST.get('report_type')
    filter_type=request.POST.get('filter','Daily')
    start_date=request.POST.get('start_date','')
    end_date=request.POST.get('end_date','')
    search=request.POST.get('search','')

    sales_q=Sale.objects.filter(status__iexact='completed')
    sales_q=_apply_report_filters(sales_q,filter_type,start_date,end_date)
    if search:
        if search.isdigit():
            sales_q=sales_q.filter(sale_id=search)
        else:
            sales_q=sales_q.filter(items__product__name__icontains=search).distinct()

    response=HttpResponse(content_type='text/csv')
    response['Content-Disposition']=f'attachment; filename="{report_type}_report.csv"'
    csv_writer=csv.writer(response)

    if report_type=='sales_summary':
        agg=sales_q.aggregate(total=Sum(F('quantity')*F('product__price')),count=Count('sale_id',distinct=True),boxes=Sum('quantity'))
        csv_writer.writerow(['Total Revenue','Transactions','Total Boxes'])
        csv_writer.writerow([agg['total'] or 0,agg['count'] or 0,agg['boxes'] or 0])
    elif report_type=='transactions':
        csv_writer.writerow(['Sale ID','Date','Total','Status'])
        for s in sales_q:
            csv_writer.writerow([s.sale_id,s.recorded_at,s.total,s.status])
    else:
        csv_writer.writerow(['Not implemented'])
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
    if filter_status != 'All Products':
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

                # OR per line to keep uniqueness simple
                or_seq = Sale.objects.filter(recorded_at__year=year).count() + 1
                or_number = f'OR-{year}-{or_seq:06d}'

                line_total = Decimal(product.price) * quantity

                sale_row = Sale.objects.create(
                    product=product,
                    quantity=quantity,
                    price=product.price,
                    or_number=or_number,
                    customer_name=request.POST.get('customer_name', ''),
                    address=request.POST.get('address', ''),
                    contact_number=int(request.POST.get('contact_number', 0) or 0),
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
        
        # For single-table sales, create items data from the sale itself
        items_data = [{
            'product_id': sale.product.product_id if sale.product else None,
            'product__name': sale.product.name if sale.product else 'Unknown',
            'product__size': sale.product.size if sale.product else '',
            'quantity': sale.quantity,
            'price': sale.price
        }]

        return JsonResponse({
            'success': True,
            'sale': {
                'sale_id': sale.sale_id,
                'or_number': sale.or_number,
                'recorded_at': sale.recorded_at.isoformat(),
                'total': sale.total,
                'status': sale.status,
                'username': sale.user.username if sale.user else 'Unknown'
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


def can_print_receipt(sale_id, user_id, user_role):
    """Check if user can print receipt"""
    # For now, allow unlimited prints since ReceiptPrint model was removed
    return True


# SMS Notification Views
@require_app_login
def sms_settings_view(request):
    """SMS settings page bound to current admin's AppUser (phone only)."""
    if request.session.get('app_role') != 'admin':
        return redirect('dashboard')

    user_id = request.session.get('app_user_id')
    user_obj = AppUser.objects.get(user_id=user_id)

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        if phone_number and not phone_number.startswith('+'):
            messages.error(request, 'Phone number must include country code (e.g., +1234567890)')
        else:
            user_obj.phone_number = phone_number
            user_obj.save(update_fields=['phone_number'])
            messages.success(request, 'SMS settings saved.')

    context = {
        'sms_notification': type('Obj', (), {
            'phone_number': getattr(user_obj, 'phone_number', ''),
            'is_active': bool(getattr(user_obj, 'phone_number', '')),
        })(),
        'app_role': request.session.get('app_role'),
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
        if 'invalid \"to\" phone number' in lowered or "invalid 'to' phone number" in lowered:
            hint = ' Tip: Use a valid mobile number in E.164 format (e.g., +639xxxxxxxxx) and ensure the recipient is verified on your Twilio trial account.'
        elif 'authenticate' in lowered or 'credentials' in lowered:
            hint = ' Tip: Check TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_PHONE in your environment.'

        short_msg = cleaned[:300]
        return JsonResponse({'success': False, 'message': f'Failed to send test SMS: {short_msg}{hint}'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


