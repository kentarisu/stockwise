from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, Http404
from django.db import transaction
from django.utils import timezone
from itsdangerous import URLSafeSerializer, BadSignature
from datetime import datetime
import qrcode
import io
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from core.models import Product, StockAddition


def require_app_login(view_func):
    """Decorator to require app login - redirects to main app login if not authenticated"""
    from functools import wraps
    
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Debug: Check session data
        app_user_id = request.session.get('app_user_id')
        app_username = request.session.get('app_username')
        app_role = request.session.get('app_role', '').lower()
        
        print(f"DEBUG QR AUTH: user_id={app_user_id}, username={app_username}, role={app_role}")
        
        # Strict authentication check
        if not app_user_id or not app_username:
            print(f"DEBUG QR AUTH: No valid session, redirecting to login")
            # Store the current URL to redirect back after login
            request.session['qr_redirect_url'] = request.get_full_path()
            # Clear any partial session data
            request.session.pop('app_user_id', None)
            request.session.pop('app_username', None) 
            request.session.pop('app_role', None)
            # Redirect to main app login page
            return redirect('/login/')
        
        # Check if user has appropriate role (admin or secretary)
        if app_role not in ['admin', 'secretary']:
            print(f"DEBUG QR AUTH: Invalid role '{app_role}', redirecting to login")
            # Store the current URL to redirect back after login
            request.session['qr_redirect_url'] = request.get_full_path()
            # Redirect to login if role is not authorized
            return redirect('/login/')
        
        print(f"DEBUG QR AUTH: Authentication successful for {app_username} ({app_role})")
        return view_func(request, *args, **kwargs)
    return wrapper


def _get_acronym(s: str) -> str:
    if not s:
        return ''
    parts = [p for p in s.split() if p]
    return ''.join([p[0].upper() for p in parts])


def _generate_batch_id(product: Product, delivery_date: datetime.date, variant: str = '') -> str:
    """Generate batch id identical to manual add-stock:
    <FRUIT_ACR><VARIANT_ACR?><SIZE_FULL><MMDDYYYY><SEQ_01_99>
    Sequence increases per product across additions and wraps at 99.
    """
    import re
    base_name = product.name or ''
    # Remove trailing (variant) from name if present so acronym is for base fruit
    m = re.search(r"^(.*?)\s*\((.*?)\)\s*$", base_name)
    if m:
        base_only = m.group(1).strip()
        parsed_variant = m.group(2).strip()
    else:
        base_only = base_name.strip()
        parsed_variant = ''
    # If explicit variant provided, prefer it; else use parsed one
    variant_text = (variant or '').strip() or parsed_variant

    fruit_acr = _get_acronym(base_only)
    variant_acr = _get_acronym(variant_text) if variant_text else ''
    size_full = str(product.size or '')
    mm = f"{delivery_date.month:02d}"
    dd = f"{delivery_date.day:02d}"
    yyyy = f"{delivery_date.year:04d}"
    # Sequence based on existing additions for this product
    existing_total = StockAddition.objects.filter(product=product).count()
    seq = (existing_total % 99) + 1
    seq_part = f"{seq:02d}"
    return f"{fruit_acr}{variant_acr}{size_full}{mm}{dd}{yyyy}{seq_part}"


def _generate_incomplete_batch_id(product: Product, delivery_date: datetime.date, variant: str = '') -> str:
    """Generate incomplete batch ID with XX placeholder for quantity"""
    import re
    base_name = product.name or ''
    # Remove trailing (variant) from name if present so acronym is for base fruit
    m = re.search(r"^(.*?)\s*\((.*?)\)\s*$", base_name)
    if m:
        base_only = m.group(1).strip()
        parsed_variant = m.group(2).strip()
    else:
        base_only = base_name.strip()
        parsed_variant = ''
    # If explicit variant provided, prefer it; else use parsed one
    variant_text = (variant or '').strip() or parsed_variant

    fruit_acr = _get_acronym(base_only)
    variant_acr = _get_acronym(variant_text) if variant_text else ''
    size_full = str(product.size or '')
    mm = f"{delivery_date.month:02d}"
    dd = f"{delivery_date.day:02d}"
    yyyy = f"{delivery_date.year:04d}"
    
    # Get the next sequence number based on existing individual batches
    next_sequence = _get_next_batch_sequence(product, delivery_date)
    
    # Use XX as placeholder for sequence since quantity hasn't been entered yet
    return f"{fruit_acr}{variant_acr}{size_full}{mm}{dd}{yyyy}XX"

def _get_next_batch_sequence(product: Product, target_date: datetime.date) -> int:
    """Get the next sequence number for batch ID generation by finding the highest individual batch sequence"""
    # Get all existing stock additions for this product
    existing_additions = StockAddition.objects.filter(product=product).order_by('date_added', 'addition_id')
    
    highest_sequence = 0
    
    for addition in existing_additions:
        try:
            # Parse the batch_id to get the base sequence number
            batch_id = addition.batch_id
            if len(batch_id) >= 2 and batch_id[-2:].isdigit():
                base_seq = int(batch_id[-2:])
                quantity = int(addition.quantity or 1)
                
                # Calculate the highest individual sequence for this addition
                # If base_seq is 04 and quantity is 20, individual sequences are 04, 05, 06, ..., 23
                individual_highest = base_seq + quantity - 1
                highest_sequence = max(highest_sequence, individual_highest)
        except (ValueError, AttributeError):
            continue
    
    # Return next sequence (wrap at 99)
    return ((highest_sequence % 99) + 1)


def qr_generate(request, product_id: int):
    # Requires query param ?date=YYYY-MM-DD optional &variant=...
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        raise Http404

    date_str = request.GET.get('date')
    variant = request.GET.get('variant', '')
    delivery_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()

    s = URLSafeSerializer(settings.SECRET_KEY)
    payload = {
        'p': product.product_id,
        'd': delivery_date.strftime('%Y-%m-%d'),
    }
    token = s.dumps(payload)

    # Point to QR confirm page with token for stock addition
    # Use request host for QR codes so they work with phone camera scanning
    host = request.get_host()
    scheme = 'https' if request.is_secure() else 'http'
    local_url = f"{scheme}://{host}"
    confirm_url = f"{local_url}/qr/confirm/{token}/"

    img = qrcode.make(confirm_url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return HttpResponse(buf.read(), content_type='image/png')


@csrf_exempt
def confirm_view(request, token: str):
    # STRICT authentication check - must be done first
    app_user_id = request.session.get('app_user_id')
    app_username = request.session.get('app_username')
    app_role = request.session.get('app_role', '').lower()
    
    print(f"DEBUG QR CONFIRM: user_id={app_user_id}, username={app_username}, role={app_role}")
    
    # Strict authentication - block access if not properly logged in
    if not app_user_id or not app_username:
        print(f"DEBUG QR CONFIRM: No valid session - BLOCKING ACCESS")
        # Store the current URL to redirect back after login
        request.session['qr_redirect_url'] = request.get_full_path()
        # Clear any partial session data
        request.session.pop('app_user_id', None)
        request.session.pop('app_username', None) 
        request.session.pop('app_role', None)
        # Force redirect to login
        return redirect('/login/')
    
    # Check if user has appropriate role (admin or secretary)
    if app_role not in ['admin', 'secretary']:
        print(f"DEBUG QR CONFIRM: Invalid role '{app_role}' - BLOCKING ACCESS")
        # Store the current URL to redirect back after login
        request.session['qr_redirect_url'] = request.get_full_path()
        # Force redirect to login
        return redirect('/login/')
    
    print(f"DEBUG QR CONFIRM: Authentication successful for {app_username} ({app_role})")
    s = URLSafeSerializer(settings.SECRET_KEY)
    try:
        data = s.loads(token)
    except BadSignature:
        raise Http404
    product_id = int(data['p'])
    # Use the actual scanning date instead of pre-generated date
    delivery_date = timezone.now().date()
    batch_id = data.get('b')

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        raise Http404

    # If batch_id was not embedded in QR, compute it now using current date and product variant
    if not batch_id:
        import re
        variant = ''
        name = product.name or ''
        m = re.search(r"^(.*?)\s*\((.*?)\)\s*$", name)
        if m:
            variant = (m.group(2) or '').strip()
        batch_id = _generate_incomplete_batch_id(product, delivery_date, variant)

    # This view now only shows action selection, no POST handling needed

    # GET -> simple confirm page
    return render(request, 'qrstock/confirm.html', {
        'product': product,
        'delivery_date': delivery_date,
        'batch_id': batch_id,
        'token': token,
        'app_username': request.session.get('app_username'),
        'app_role': request.session.get('app_role'),
    })


@csrf_exempt
def qr_add_stock_view(request, token: str):
    """Dedicated QR Add Stock page"""
    # STRICT authentication check - must be done first
    app_user_id = request.session.get('app_user_id')
    app_username = request.session.get('app_username')
    app_role = request.session.get('app_role', '').lower()
    
    print(f"DEBUG QR ADD STOCK: user_id={app_user_id}, username={app_username}, role={app_role}")
    
    # Strict authentication - block access if not properly logged in
    if not app_user_id or not app_username:
        print(f"DEBUG QR ADD STOCK: No valid session - BLOCKING ACCESS")
        # Store the current URL to redirect back after login
        request.session['qr_redirect_url'] = request.get_full_path()
        # Clear any partial session data
        request.session.pop('app_user_id', None)
        request.session.pop('app_username', None)
        request.session.pop('app_role', None)
        # Force redirect to login
        return redirect('/login/')
    
    # Check if user has appropriate role (admin or secretary)
    if app_role not in ['admin', 'secretary']:
        print(f"DEBUG QR ADD STOCK: Invalid role '{app_role}' - BLOCKING ACCESS")
        # Store the current URL to redirect back after login
        request.session['qr_redirect_url'] = request.get_full_path()
        # Force redirect to login
        return redirect('/login/')
    
    print(f"DEBUG QR ADD STOCK: Authentication successful for {app_username} ({app_role})")
    
    s = URLSafeSerializer(settings.SECRET_KEY)
    try:
        data = s.loads(token)
    except BadSignature:
        raise Http404
    product_id = int(data['p'])
    # Use the actual scanning date instead of pre-generated date
    delivery_date = timezone.now().date()
    batch_id = data.get('b')

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        raise Http404

    # If batch_id was not embedded in QR, compute it now using current date and product variant
    if not batch_id:
        import re
        variant = ''
        name = product.name or ''
        m = re.search(r"^(.*?)\s*\((.*?)\)\s*$", name)
        if m:
            variant = (m.group(2) or '').strip()
        batch_id = _generate_incomplete_batch_id(product, delivery_date, variant)

    if request.method == 'POST':
        qty = int(request.POST.get('quantity', '0'))
        supplier = request.POST.get('supplier', '').strip()
        if qty <= 0:
            return JsonResponse({'success': False, 'message': 'Quantity must be positive'})
        
        with transaction.atomic():
            # Generate proper batch ID with correct sequence continuation
            next_sequence = _get_next_batch_sequence(product, delivery_date)
            
            # Build the actual batch ID for this addition
            import re
            variant = ''
            name = product.name or ''
            m = re.search(r"^(.*?)\s*\((.*?)\)\s*$", name)
            if m:
                base_only = m.group(1).strip()
                variant = (m.group(2) or '').strip()
            else:
                base_only = name.strip()
            
            fruit_acr = _get_acronym(base_only)
            variant_acr = _get_acronym(variant) if variant else ''
            size_full = str(product.size or '')
            mm = f"{delivery_date.month:02d}"
            dd = f"{delivery_date.day:02d}"
            yyyy = f"{delivery_date.year:04d}"
            seq_part = f"{next_sequence:02d}"
            
            actual_batch_id = f"{fruit_acr}{variant_acr}{size_full}{mm}{dd}{yyyy}{seq_part}"
            
            # Create new stock addition (no merging - each addition gets its own batch)
            StockAddition.objects.create(
                product=product,
                batch_id=actual_batch_id,
                date_added=delivery_date,
                quantity=qty,
                remaining_quantity=qty,
                supplier=supplier or '',
                created_at=timezone.now(),
                cost=0.0
            )

            # Update product stock directly
            product.stock = product.stock + qty
            product.last_updated = timezone.now()
            product.save()
        return JsonResponse({'success': True, 'message': 'Stock added', 'batch_id': actual_batch_id})

    # GET -> add stock page
    return render(request, 'qrstock/add_stock.html', {
        'product': product,
        'delivery_date': delivery_date,
        'batch_id': batch_id,
        'token': token,
        'app_username': request.session.get('app_username'),
        'app_role': request.session.get('app_role'),
    })


@csrf_exempt
def qr_record_sale_view(request, token: str):
    """Dedicated QR Record Sale page"""
    # STRICT authentication check - must be done first
    app_user_id = request.session.get('app_user_id')
    app_username = request.session.get('app_username')
    app_role = request.session.get('app_role', '').lower()
    
    print(f"DEBUG QR RECORD SALE: user_id={app_user_id}, username={app_username}, role={app_role}")
    
    # Strict authentication - block access if not properly logged in
    if not app_user_id or not app_username:
        print(f"DEBUG QR RECORD SALE: No valid session - BLOCKING ACCESS")
        # Store the current URL to redirect back after login
        request.session['qr_redirect_url'] = request.get_full_path()
        # Clear any partial session data
        request.session.pop('app_user_id', None)
        request.session.pop('app_username', None)
        request.session.pop('app_role', None)
        # Force redirect to login
        return redirect('/login/')
    
    # Check if user has appropriate role (admin or secretary)
    if app_role not in ['admin', 'secretary']:
        print(f"DEBUG QR RECORD SALE: Invalid role '{app_role}' - BLOCKING ACCESS")
        # Store the current URL to redirect back after login
        request.session['qr_redirect_url'] = request.get_full_path()
        # Force redirect to login
        return redirect('/login/')
    
    print(f"DEBUG QR RECORD SALE: Authentication successful for {app_username} ({app_role})")
    
    s = URLSafeSerializer(settings.SECRET_KEY)
    try:
        data = s.loads(token)
    except BadSignature:
        raise Http404
    product_id = int(data['p'])
    
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        raise Http404

    # Get existing stock batches and expand them into individual boxes (like in stock_details)
    stock_additions = (
        StockAddition.objects
        .filter(product=product, remaining_quantity__gt=0)
        .order_by('date_added', 'addition_id')
    )
    
    # Expand aggregated batches into individual box batch IDs
    batches_list = []
    for addition in stock_additions:
        try:
            total_boxes = int(addition.quantity or 0)
            prefix, start_seq = addition.batch_id[:-2], int(addition.batch_id[-2:]) if len(addition.batch_id) >= 2 else (addition.batch_id, 1)
        except Exception:
            total_boxes, prefix, start_seq = int(addition.quantity or 0), addition.batch_id, 1
        
        total_boxes = max(total_boxes, 1)
        remaining_boxes = int(addition.remaining_quantity or 0)
        consumed = max(0, total_boxes - remaining_boxes)
        
        # Generate individual batch IDs for remaining boxes
        for i in range(total_boxes):
            if i < consumed:  # Skip consumed boxes
                continue
            seq = ((start_seq - 1 + i) % 99) + 1
            box_id = f"{prefix}{seq:02d}" if prefix else f"{seq:02d}"
            batches_list.append({
                'batch_id': box_id,
                'date_added': addition.date_added,
                'remaining': 1,  # Each individual box
                'supplier': addition.supplier or '',
            })
    
    # Use first available batch as default, or generate placeholder if no stock
    if batches_list:
        default_batch_id = batches_list[0]['batch_id']
    else:
        # No stock available - generate placeholder
        delivery_date = timezone.now().date()
        import re
        variant = ''
        name = product.name or ''
        m = re.search(r"^(.*?)\s*\((.*?)\)\s*$", name)
        if m:
            variant = (m.group(2) or '').strip()
        default_batch_id = _generate_incomplete_batch_id(product, delivery_date, variant)

    # GET -> record sale page (similar to record_sale.html but pre-filled with this product)
    return render(request, 'qrstock/record_sale.html', {
        'product': product,
        'token': token,
        'batch_id': default_batch_id,
        'stock_batches': batches_list,
        'app_username': request.session.get('app_username'),
        'app_role': request.session.get('app_role'),
    })


def stock_details(request, product_id: int):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        raise Http404
    batches = (
        StockAddition.objects
        .filter(product=product)
        .values('batch_id', 'date_added', 'quantity', 'remaining_quantity', 'supplier')
        .order_by('date_added', 'addition_id')
    )
    data = [
        {
            'batch_id': b['batch_id'],
            'date_added': b['date_added'].isoformat() if hasattr(b['date_added'], 'isoformat') else str(b['date_added']),
            'quantity': int(b['quantity'] or 0),
            'remaining': int(b['remaining_quantity'] or 0),
            'supplier': b['supplier'] or '',
        }
        for b in batches
    ]
    return JsonResponse({'success': True, 'data': data})


def qr_sticker(request, product_id: int):
    """Generate printable QR sticker with product details"""
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        raise Http404

    variant = request.GET.get('variant', '')
    # Use current date for delivery date (will be updated when actually scanning)
    delivery_date = timezone.now().date()

    # Parse product name to extract variant if not provided
    import re
    name = product.name or ''
    m = re.search(r"^(.*?)\s*\((.*?)\)\s*$", name)
    if m and not variant:
        name_only = m.group(1).strip()
        variant = m.group(2).strip()
    else:
        name_only = name

    s = URLSafeSerializer(settings.SECRET_KEY)
    payload = {
        'p': product.product_id,
        'd': delivery_date.strftime('%Y-%m-%d'),
    }
    token = s.dumps(payload)
    # Point to QR confirm page with token for stock addition
    # Use local IP for QR codes so they work with phone camera scanning on same network
    # Use request host for QR codes so they work with phone camera scanning
    host = request.get_host()
    scheme = 'https' if request.is_secure() else 'http'
    local_url = f"{scheme}://{host}"
    confirm_url = f"{local_url}/qr/confirm/{token}/"

    # Generate QR code
    img = qrcode.make(confirm_url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    qr_data = buf.getvalue()

    # Convert to base64 for template
    import base64
    qr_base64 = base64.b64encode(qr_data).decode('utf-8')

    return render(request, 'qrstock/sticker.html', {
        'product': product,
        'name_only': name_only,
        'variant': variant,
        'size': product.size or '',
        'delivery_date': delivery_date,
        'batch_id': None,
        'qr_base64': qr_base64,
        'confirm_url': confirm_url,
    })


def inventory_list(request):
    # Basic list mirroring PHP: id, name, variant, size, price, stock, status
    # Guard for instances where 'is_inventory' column may not exist yet
    try:
        products_qs = Product.objects.all()
        # Only keep inventory-marked items when the field exists
        if any(getattr(f, 'name', None) == 'is_inventory' for f in Product._meta.get_fields()):
            products_qs = products_qs.filter(is_inventory=True)
        else:
            products_qs = products_qs.none()
        products = list(products_qs.order_by('name'))
    except Exception:
        products = []
    # Prefetch inventory into a map to avoid N+1
    inv_by_pid = {inv.product_id: inv for inv in Inventory.objects.filter(product_id__in=[p.product_id for p in products])}
    rows = []
    import re
    for p in products:
        variant = ''
        name = p.name or ''
        m = re.search(r"^(.*?)\s*\((.*?)\)\s*$", name)
        if m:
            name_only = m.group(1).strip()
            variant = m.group(2).strip()
        else:
            name_only = name
        stock = getattr(inv_by_pid.get(p.product_id), 'stock', 0) or 0
        rows.append({
            'id': p.product_id,
            'name': name_only,
            'variant': variant,
            'size': p.size or '',
            'price': float(p.price or 0),
            'stock': int(stock),
            'status': p.status,
        })
    return render(request, 'qrstock/inventory.html', {'rows': rows})

# Create your views here.


@csrf_exempt
def get_next_batch_sequence(request, product_id: int):
    """Get the next batch sequence number for dynamic batch ID generation"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Only GET method allowed'})
    
    try:
        product = Product.objects.get(pk=product_id)
        delivery_date = timezone.now().date()
        
        # Get the next sequence number
        next_sequence = _get_next_batch_sequence(product, delivery_date)
        
        # Build base batch ID (without sequence)
        import re
        variant = ''
        name = product.name or ''
        m = re.search(r"^(.*?)\s*\((.*?)\)\s*$", name)
        if m:
            base_only = m.group(1).strip()
            variant = (m.group(2) or '').strip()
        else:
            base_only = name.strip()
        
        fruit_acr = _get_acronym(base_only)
        variant_acr = _get_acronym(variant) if variant else ''
        size_full = str(product.size or '')
        mm = f"{delivery_date.month:02d}"
        dd = f"{delivery_date.day:02d}"
        yyyy = f"{delivery_date.year:04d}"
        
        base_batch_id = f"{fruit_acr}{variant_acr}{size_full}{mm}{dd}{yyyy}"
        
        return JsonResponse({
            'success': True, 
            'next_sequence': next_sequence,
            'base_batch_id': base_batch_id
        })
        
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def decode_token(request):
    """Decode QR confirm token for Add Stock page integration"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Only GET method allowed'})
    
    token = request.GET.get('token')
    if not token:
        return JsonResponse({'success': False, 'message': 'Token parameter required'})
    
    try:
        from itsdangerous import URLSafeSerializer
        from django.conf import settings
        
        s = URLSafeSerializer(settings.SECRET_KEY)
        payload = s.loads(token)
        
        product_id = payload.get('p')
        delivery_date_str = payload.get('d')
        
        if not product_id:
            return JsonResponse({'success': False, 'message': 'Invalid token format'})
        
        # Verify product exists
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'})
        
        return JsonResponse({
            'success': True,
            'product_id': product_id,
            'product_name': product.name,
            'delivery_date': delivery_date_str
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error decoding token: {str(e)}'})
