import os
import django
import sys

# Setup Django environment
sys.path.append(r'c:\Users\Orly\stockwise')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise_py.settings')
django.setup()

from core.models import AppUser

print("--- AppUser Roles ---")
users = AppUser.objects.all()
for user in users:
    print(f"Username: {user.username}, Role: '{user.role}', ID: {user.user_id}")
