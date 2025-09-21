from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, Http404
from django.db import transaction
from django.utils import timezone
from itsdangerous import URLSafeSerializer, BadSignature
from datetime import datetime
import qrcode
import io
from django.conf import settings

from .models import Product, Inventory, StockAddition


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

    confirm_url = request.build_absolute_uri(f"/qr/confirm/{token}/")

    img = qrcode.make(confirm_url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return HttpResponse(buf.read(), content_type='image/png')


def confirm_view(request, token: str):
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
        batch_id = _generate_batch_id(product, delivery_date, variant)

    if request.method == 'POST':
        qty = int(request.POST.get('quantity', '0'))
        supplier = request.POST.get('supplier', '').strip()
        if qty <= 0:
            return JsonResponse({'success': False, 'message': 'Quantity must be positive'})
        with transaction.atomic():
            # Merge logic: existing batch with same product, batch_id and date
            addition, created = StockAddition.objects.select_for_update().get_or_create(
                product=product,
                batch_id=batch_id,
                date_added=delivery_date,
                defaults={'quantity': 0, 'remaining_quantity': 0, 'created_at': timezone.now()},
            )
            addition.quantity = addition.quantity + qty
            addition.remaining_quantity = addition.remaining_quantity + qty
            # Update supplier if provided
            if supplier:
                addition.supplier = supplier
            addition.save()

            inv, _ = Inventory.objects.get_or_create(product=product, defaults={'stock': 0, 'last_updated': timezone.now()})
            inv.stock = inv.stock + qty
            inv.last_updated = timezone.now()
            inv.save()
        return JsonResponse({'success': True, 'message': 'Stock added', 'batch_id': batch_id})

    # GET -> simple confirm page
    return render(request, 'qrstock/confirm.html', {
        'product': product,
        'delivery_date': delivery_date,
        'batch_id': batch_id,
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
    confirm_url = request.build_absolute_uri(f"/qr/confirm/{token}/")

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
