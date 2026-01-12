import os
import django
import sys

# Setup Django environment
sys.path.append(r'c:\Users\Orly\stockwise')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise_py.settings')
django.setup()

from core.models import AppUser

print("--- AppUser Roles Inspection ---")
try:
    count = AppUser.objects.count()
    print(f"Total users found: {count}")
    
    users = AppUser.objects.all()
    for user in users:
        print(f"Username: '{user.username}', Role: '{user.role}', ID: {user.user_id}")
        
    print("--- End Inspection ---")
except Exception as e:
    print(f"Error inspecting users: {e}")
