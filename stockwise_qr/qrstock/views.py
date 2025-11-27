# QR Stock views
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from core.models import Product
from core.views import require_app_login
from core.thermal_printer import get_printer_service
import qrcode
import io
import base64
from django.urls import reverse

def qr_sticker_view(request, product_id):
    """Generate QR code sticker page for a product"""
    try:
        product = get_object_or_404(Product, product_id=product_id)
        
        # Create QR code with URL that redirects to QR confirm page (existing system)
        from itsdangerous import URLSafeSerializer
        s = URLSafeSerializer(settings.SECRET_KEY)
        token = s.dumps({'p': product.product_id})
        
        qr_confirm_url = request.build_absolute_uri(f'/qr/confirm/{token}/')
        qr_data = qr_confirm_url
        
        qr = qrcode.QRCode(
            version=None,  # Auto-determine version based on data
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
            box_size=8,
            border=2,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for embedding in HTML
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # If AJAX/JSON requested, return data
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            return JsonResponse({
                'success': True,
                'data': {
                    'product_id': product.product_id,
                    'product_name': product.name,
                    'variant': product.variant or '',
                    'quantity': product.quantity_unit or '',
                    'qr_code_base64': qr_code_base64,
                    'qr_data': qr_data,
                }
            })
        
        # Render the sticker template
        context = {
            'product': product,
            'qr_code_base64': qr_code_base64,
            'qr_data': qr_data,
        }
        
        return render(request, 'qrstock/sticker.html', context)
        
    except Exception as e:
        return HttpResponse(f"Error generating QR sticker: {str(e)}", status=500)

def qr_scan_view(request):
    """Handle scanned QR codes"""
    if request.method == 'POST':
        try:
            qr_data = request.POST.get('qr_data', '').strip()
            
            if not qr_data:
                return JsonResponse({'success': False, 'message': 'No QR data provided'})
            
            # Parse the structured QR data
            if qr_data.startswith('STOCKWISE_PRODUCT:'):
                parts = qr_data.split(':')
                if len(parts) >= 6:
                    product_id = parts[1]
                    product_name = parts[2]
                    product_size = parts[3]
                    product_price = parts[4]
                    product_stock = parts[5]
                    
                    # Try to get the product from database
                    try:
                        product = Product.objects.get(product_id=product_id)
                        return JsonResponse({
                            'success': True,
                            'message': 'Product found',
                            'product': {
                                'id': product.product_id,
                                'name': product.name,
                            'quantity_unit': product.quantity_unit,
                                'price': float(product.price),
                                'stock': product.stock,
                                'variant': product.variant
                            }
                        })
                    except Product.DoesNotExist:
                        return JsonResponse({
                            'success': False,
                            'message': f'Product not found in database: {product_name}'
                        })
                else:
                    return JsonResponse({'success': False, 'message': 'Invalid QR code format'})
            else:
                return JsonResponse({'success': False, 'message': 'Not a StockWise product QR code'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error processing QR code: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def qr_test_view(request, product_id):
    """Test QR code data format"""
    try:
        product = get_object_or_404(Product, product_id=product_id)
        
        # Create QR code with structured product information
        qr_data = f"STOCKWISE_PRODUCT:{product.product_id}:{product.name}:{product.quantity_unit}:{product.price}:{product.stock}"
        
        return JsonResponse({
            'success': True,
            'product_id': product_id,
            'qr_data': qr_data,
            'product_info': {
                'name': product.name,
                'quantity_unit': product.quantity_unit,
                'price': float(product.price),
                'stock': product.stock,
                'variant': product.variant
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

def qr_scanner_view(request):
    """QR Code Scanner Test Page"""
    return render(request, 'qrstock/scanner.html')

def qr_generator_view(request, product_id):
    """QR Code Data Generator Page"""
    try:
        product = get_object_or_404(Product, product_id=product_id)
        
        # Create QR code with URL that redirects to QR confirm page (existing system)
        from itsdangerous import URLSafeSerializer
        s = URLSafeSerializer(settings.SECRET_KEY)
        token = s.dumps({'p': product.product_id})
        
        qr_confirm_url = request.build_absolute_uri(f'/qr/confirm/{token}/')
        qr_data = qr_confirm_url
        
        context = {
            'product': product,
            'qr_data': qr_data,
        }
        
        return render(request, 'qrstock/generator.html', context)
        
    except Exception as e:
        return HttpResponse(f"Error generating QR data: {str(e)}", status=500)


def qr_generate_image(request, product_id):
    """Return QR data (PNG or JSON) that encodes the confirm page URL.

    Used by products_inventory_full.html via /qr/generate/<product_id>/?date=YYYY-MM-DD
    The confirm page lets the user choose Add Stock or Record Sale.
    """
    try:
        product = get_object_or_404(Product, product_id=product_id)
        date_str = request.GET.get('date')
        from itsdangerous import URLSafeSerializer
        s = URLSafeSerializer(settings.SECRET_KEY)
        payload = {'p': product.product_id}
        if date_str:
            payload['d'] = date_str
        token = s.dumps(payload)
        confirm_url = request.build_absolute_uri(reverse('qr_confirm', kwargs={'token': token}))

        qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
        qr.add_data(confirm_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # If JSON requested, return base64 and the link
        if request.GET.get('format') == 'json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            b64 = base64.b64encode(buf.getvalue()).decode('ascii')
            return JsonResponse({'success': True, 'qr_code_base64': b64, 'qr_link': confirm_url})

        # Otherwise return the PNG image
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return HttpResponse(buf.getvalue(), content_type='image/png')
    except Exception as e:
        return HttpResponse(f"Error generating QR image: {str(e)}", status=500)

def qr_debug_view(request, product_id):
    """Debug view to show current QR data"""
    try:
        product = get_object_or_404(Product, product_id=product_id)
        
        # Create QR code with URL that redirects to QR confirm page (existing system)
        from itsdangerous import URLSafeSerializer
        s = URLSafeSerializer(settings.SECRET_KEY)
        token = s.dumps({'p': product.product_id})
        
        qr_confirm_url = request.build_absolute_uri(f'/qr/confirm/{token}/')
        qr_data = qr_confirm_url
        
        return HttpResponse(f"Product ID: {product_id}<br>QR Data: {qr_data}", content_type="text/html")
        
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)

def qr_confirm_view(request, token):
    """QR Confirm Page - Choose between Add Stock or Record Sale"""
    try:
        # Decode the QR token to get product information
        from itsdangerous import URLSafeSerializer
        from datetime import datetime, timedelta
        
        s = URLSafeSerializer(settings.SECRET_KEY)
        data = s.loads(token)
        product_id = data.get('p')
        
        if not product_id:
            return HttpResponse('Invalid QR token: No product ID found.', status=400)
        
        try:
            product = Product.objects.get(product_id=product_id)
        except Product.DoesNotExist:
            return HttpResponse(f'Product with ID {product_id} not found.', status=404)
        
        # Check if this is a new QR scan or an existing session
        current_time = datetime.now()
        session_key = f'qr_scan_{token}'
        
        if session_key not in request.session:
            # New QR scan - set the scan timestamp
            request.session[session_key] = current_time.isoformat()
            request.session['qr_scan_active'] = True
            request.session['qr_token'] = token
            request.session['qr_product_id'] = product_id
        else:
            # Existing session - check if it's expired (1 hour)
            scan_time_str = request.session.get(session_key)
            scan_time = datetime.fromisoformat(scan_time_str)
            
            if current_time - scan_time > timedelta(hours=1):
                # Session expired - clear the session and show error
                request.session.pop(session_key, None)
                request.session.pop('qr_scan_active', None)
                request.session.pop('qr_token', None)
                request.session.pop('qr_product_id', None)
                
                context = {
                    'session_expired': True,
                    'product': product,
                }
                return render(request, 'qrstock/confirm.html', context)
        
        # Generate batch ID and date for display
        from datetime import date
        today = date.today()
        date_arrived = today.strftime('%b. %d, %Y')
        
        # Generate a simple batch ID
        batch_id = f"AF{product.quantity_unit}{today.strftime('%m%d%Y')}XX"
        
        # Calculate time remaining for display
        scan_time_str = request.session.get(session_key)
        scan_time = datetime.fromisoformat(scan_time_str)
        time_remaining = timedelta(hours=1) - (current_time - scan_time)
        minutes_remaining = int(time_remaining.total_seconds() / 60)
        
        context = {
            'product': product,
            'product_id': product_id,
            'date_arrived': date_arrived,
            'batch_id': batch_id,
            'session_expired': False,
            'minutes_remaining': minutes_remaining,
        }
        
        return render(request, 'qrstock/confirm.html', context)
        
    except Exception as e:
        return HttpResponse(f'Error processing QR token: {str(e)}', status=500)


@require_app_login
@require_POST
def qr_sticker_print(request, product_id):
    """Print QR sticker to thermal printer"""
    try:
        product = get_object_or_404(Product, product_id=product_id)
        
        # Create QR code image bytes
        from itsdangerous import URLSafeSerializer
        s = URLSafeSerializer(settings.SECRET_KEY)
        token = s.dumps({'p': product.product_id})
        qr_confirm_url = request.build_absolute_uri(f'/qr/confirm/{token}/')
        
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=1,
        )
        qr.add_data(qr_confirm_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_bytes = buffer.getvalue()
        
        sticker_data = {
            'product_name': product.name,
            'variant': product.variant or '',
            'quantity': product.quantity_unit or '',
            'qr_image_bytes': qr_bytes,
        }
        
        connection_type = request.POST.get('connection_type', getattr(settings, 'THERMAL_PRINTER_TYPE', 'usb'))
        connection_params = {}
        
        if connection_type == 'usb':
            vendor_id = request.POST.get('vendor_id')
            product_id_hex = request.POST.get('product_id')
            if vendor_id and product_id_hex:
                connection_params['vendor_id'] = int(vendor_id, 16) if vendor_id.startswith('0x') else int(vendor_id)
                connection_params['product_id'] = int(product_id_hex, 16) if product_id_hex.startswith('0x') else int(product_id_hex)
        elif connection_type in ['serial', 'bluetooth']:
            port = request.POST.get('port', getattr(settings, 'THERMAL_PRINTER_PORT', 'COM3'))
            baudrate = int(request.POST.get('baudrate', getattr(settings, 'THERMAL_PRINTER_BAUDRATE', 9600)))
            connection_params['port'] = port
            connection_params['baudrate'] = baudrate
        elif connection_type == 'network':
            host = request.POST.get('host', getattr(settings, 'THERMAL_PRINTER_HOST', '192.168.1.100'))
            port = int(request.POST.get('port', getattr(settings, 'THERMAL_PRINTER_NETWORK_PORT', 9100)))
            connection_params['host'] = host
            connection_params['port'] = port
        elif connection_type == 'windows':
            printer_name = request.POST.get('printer_name', getattr(settings, 'THERMAL_PRINTER_NAME', 'POS58 Printer'))
            connection_params['printer_name'] = printer_name
        
        printer_service = get_printer_service(connection_type=connection_type, **connection_params)
        if not printer_service:
            return JsonResponse({
                'success': False,
                'message': 'Failed to connect to printer. Please check printer connection and settings.'
            }, status=500)
        
        success = printer_service.print_qr_sticker(sticker_data)
        printer_service.close()
        
        if success:
            # Log sticker print
            from core.views import log_action
            log_action(
                request,
                'Sticker printed',
                f'Printed QR sticker for product {product_id} ({product.name}).'
            )
            return JsonResponse({'success': True, 'message': 'Sticker printed successfully!'})
        else:
            error_msg = getattr(printer_service, 'last_error', 'Unknown printer error.')
            return JsonResponse({'success': False, 'message': error_msg}, status=500)
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Print error: {str(e)}'}, status=500)
