# QR Stock views
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from core.models import Product
import qrcode
import io
import base64

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
                                'size': product.size,
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
        qr_data = f"STOCKWISE_PRODUCT:{product.product_id}:{product.name}:{product.size}:{product.price}:{product.stock}"
        
        return JsonResponse({
            'success': True,
            'product_id': product_id,
            'qr_data': qr_data,
            'product_info': {
                'name': product.name,
                'size': product.size,
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
        s = URLSafeSerializer(settings.SECRET_KEY)
        data = s.loads(token)
        product_id = data.get('p')
        
        if not product_id:
            return HttpResponse('Invalid QR token: No product ID found.', status=400)
        
        try:
            product = Product.objects.get(product_id=product_id)
        except Product.DoesNotExist:
            return HttpResponse(f'Product with ID {product_id} not found.', status=404)
        
        # Generate batch ID and date for display
        from datetime import date
        today = date.today()
        date_arrived = today.strftime('%b. %d, %Y')
        
        # Generate a simple batch ID
        batch_id = f"AF{product.size}{today.strftime('%m%d%Y')}XX"
        
        context = {
            'product': product,
            'product_id': product_id,
            'date_arrived': date_arrived,
            'batch_id': batch_id,
        }
        
        return render(request, 'qrstock/confirm.html', context)
        
    except Exception as e:
        return HttpResponse(f'Error processing QR token: {str(e)}', status=500)
