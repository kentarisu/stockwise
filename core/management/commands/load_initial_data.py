"""
Management command to load initial data from fixtures into the database.
Useful for migrating from SQLite to PostgreSQL.
"""
import os
import zipfile
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

class Command(BaseCommand):
    help = 'Load initial data from fixtures/initial_data.json into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force load even if data already exists',
        )

    def handle(self, *args, **options):
        fixture_path = os.path.join(settings.BASE_DIR, 'fixtures', 'initial_data.json')
        zip_path = fixture_path + '.zip'
        
        # Extract if compressed
        if not os.path.exists(fixture_path) and os.path.exists(zip_path):
            self.stdout.write(f'Extracting compressed fixture from {zip_path}...')
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(os.path.dirname(fixture_path))
            self.stdout.write(self.style.SUCCESS('✅ Extracted successfully'))
        
        if not os.path.exists(fixture_path):
            self.stdout.write(
                self.style.WARNING(f'Fixture file not found: {fixture_path}')
            )
            return
        
        # Check if data already exists
        from core.models import AppUser
        if not options['force'] and AppUser.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    'Database already contains data. Use --force to load anyway.'
                )
            )
            return
        
        self.stdout.write('Loading initial data from fixtures...')
        self.stdout.write(f'Fixture: {fixture_path}')
        self.stdout.write(f'Size: {os.path.getsize(fixture_path) / 1024 / 1024:.2f} MB')
        
        try:
            call_command('loaddata', fixture_path, verbosity=2)
            self.stdout.write(
                self.style.SUCCESS('✅ Initial data loaded successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error loading data: {e}')
            )
            raise

