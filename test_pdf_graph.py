
import os
import django
from django.conf import settings
from django.test import RequestFactory
import sys

# Setup Django environment
sys.path.append('c:/Users/Orly/stockwise')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise_py.settings')
django.setup()

from core.views import export_report
from core.models import AppUser

def test_pdf_generation():
    factory = RequestFactory()
    # Create an admin user session mock
    request = factory.get('/api/reports/export/?pricing_analysis=true&date_range=2024-01-01_2024-12-31')
    
    # Get first available user or create one
    user = AppUser.objects.first()
    if not user:
        user = AppUser.objects.create(username='testadmin', role='admin', password='password')
        print("Created test user")
    
    # Mock session
    request.session = {
        'app_role': 'admin',
        'app_user_id': user.user_id,
        'user_id': user.user_id # fallback
    }
    
    # Add messages mock to handle potential error messages
    from django.contrib.messages.storage.fallback import FallbackStorage
    setattr(request, 'session', request.session)
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)

    
    # Create dummy product and sale to ensure data exists
    from core.models import Product, Sale
    from django.utils import timezone
    product, _ = Product.objects.get_or_create(
        name='Test Graph Product',
        defaults={'price': 100, 'cost': 50, 'stock': 100, 'status': 'active'}
    )
    Sale.objects.create(
        product=product,
        quantity=10,
        total=1000,
        price=100,
        recorded_at=timezone.now(),
        status='completed',
        user=user
    )
    print("Created dummy sales data")

    # Try to generate report
    try:
        print("Generating report...")
        # Use simple daily filter which defaults to today
        response = export_report(request)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content
            if content.startswith(b'%PDF'):
                print("SUCCESS: Valid PDF generated.")
                # save to file for manual inspection if needed
                with open('test_report_with_pg_num.pdf', 'wb') as f:
                    f.write(content)
                print("Saved to test_report_with_pg_num.pdf")
            else:
                print("FAILURE: Response is not a PDF.")
                print(content[:100])
        else:
            print("FAILURE: Request failed.")
            print(response.content)
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_pdf_generation()
