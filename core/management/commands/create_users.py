from django.core.management.base import BaseCommand
from core.models import AppUser
from passlib.hash import bcrypt

class Command(BaseCommand):
    help = 'Create new admin and secretary users'

    def handle(self, *args, **options):
        # Delete all existing users
        self.stdout.write('Deleting all existing users...')
        AppUser.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('All existing users deleted!'))
        
        # Create Admin user
        self.stdout.write('Creating Admin user...')
        admin_user = AppUser.objects.create(
            username='admin',
            password=bcrypt.hash('admin143'),
            role='Admin',
            phone_number='1234567890'
        )
        self.stdout.write(self.style.SUCCESS(f'Admin user created: {admin_user.username}'))
        
        # Create Secretary user
        self.stdout.write('Creating Secretary user...')
        secretary_user = AppUser.objects.create(
            username='secretary',
            password=bcrypt.hash('secretary123'),
            role='Secretary',
            phone_number='0987654321'
        )
        self.stdout.write(self.style.SUCCESS(f'Secretary user created: {secretary_user.username}'))
        
        # Verify users
        self.stdout.write('\nVerifying users...')
        all_users = AppUser.objects.all()
        for user in all_users:
            self.stdout.write(f'User: {user.username}, Role: {user.role}')
            
        self.stdout.write(self.style.SUCCESS('\n✅ All users created successfully!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('Admin - Username: admin, Password: admin143')
        self.stdout.write('Secretary - Username: secretary, Password: secretary123')
