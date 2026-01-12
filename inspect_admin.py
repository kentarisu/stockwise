import os
import django
import sys

# Setup Django environment
sys.path.append(r'c:\Users\Orly\stockwise')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise_py.settings')
django.setup()

from core.models import AppUser

print("--- Admin User Inspection ---")
try:
    admin_users = AppUser.objects.filter(role__iexact='Admin')
    print(f"Users with Admin role: {admin_users.count()}")
    for user in admin_users:
        print(f" - Username: '{user.username}', Role: '{user.role}', ID: {user.user_id}")

    target_user = AppUser.objects.filter(username='admin').first()
    if target_user:
        print(f"User 'admin' found: Role='{target_user.role}', ID={target_user.user_id}")
    else:
        print("User 'admin' NOT found.")
        
except Exception as e:
    print(f"Error: {e}")
print("--- End Inspection ---")
