import os
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise_py.settings')
django.setup()

from django.test import RequestFactory, Client
from core.models import AppUser

# Create a test client
client = Client()

# Try to get an admin user
try:
    admin_user = AppUser.objects.filter(role='Admin').first()
    if not admin_user:
        print("No admin user found")
        exit(1)
    
    print(f"Found admin: {admin_user.username}")
    
    # Set up session
    session = client.session
    session['app_user_id'] = admin_user.user_id
    session['app_role'] = 'admin'
    session['app_username'] = admin_user.username
    session.save()
    
    # Try to load the page
    print("\n=== Attempting to load /sms-settings/ ===")
    response = client.get('/sms-settings/')
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ SUCCESS!")
    else:
        print(f"✗ ERROR {response.status_code}")
        if hasattr(response, 'content'):
            print(f"Content: {response.content[:1000]}")
            
except Exception as e:
    print(f"\n✗ EXCEPTION: {e}")
    traceback.print_exc()
