"""
Django management command to help migrate data from SQLite to PostgreSQL.

Usage:
    python manage.py migrate_to_postgresql --check          # Check connection
    python manage.py migrate_to_postgresql --export          # Export data
    python manage.py migrate_to_postgresql --import          # Import data
    python manage.py migrate_to_postgresql --full             # Full migration
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connections
from django.conf import settings
import os
import json
from pathlib import Path


class Command(BaseCommand):
    help = 'Migrate database from SQLite to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Check PostgreSQL connection',
        )
        parser.add_argument(
            '--export',
            action='store_true',
            help='Export data from SQLite to JSON',
        )
        parser.add_argument(
            '--import',
            action='store_true',
            dest='import_data',
            help='Import data from JSON to PostgreSQL',
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Run full migration (export + import)',
        )
        parser.add_argument(
            '--backup-file',
            type=str,
            default='local_db_backup.json',
            help='Backup file name (default: local_db_backup.json)',
        )

    def handle(self, *args, **options):
        if options['check']:
            self.check_connection()
        elif options['export']:
            self.export_data(options['backup_file'])
        elif options['import_data']:
            self.import_data(options['backup_file'])
        elif options['full']:
            self.stdout.write(self.style.WARNING('Starting full migration...'))
            self.export_data(options['backup_file'])
            self.import_data(options['backup_file'])
        else:
            self.stdout.write(self.style.ERROR('Please specify an action: --check, --export, --import, or --full'))

    def check_connection(self):
        """Check if PostgreSQL connection is configured and working."""
        self.stdout.write('Checking database connection...')
        
        db_config = settings.DATABASES['default']
        engine = db_config.get('ENGINE', '')
        
        if 'postgresql' in engine or 'postgres' in engine:
            self.stdout.write(self.style.SUCCESS(f'✓ PostgreSQL engine detected: {engine}'))
            
            try:
                db = connections['default']
                with db.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                    self.stdout.write(self.style.SUCCESS(f'✓ Connected to PostgreSQL'))
                    self.stdout.write(f'  Version: {version[:50]}...')
                    
                    # Check if migrations are up to date
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name;
                    """)
                    tables = [row[0] for row in cursor.fetchall()]
                    if tables:
                        self.stdout.write(self.style.SUCCESS(f'✓ Found {len(tables)} tables'))
                    else:
                        self.stdout.write(self.style.WARNING('⚠ No tables found. Run migrations first.'))
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Connection failed: {str(e)}'))
                self.stdout.write(self.style.WARNING('Make sure DATABASE_URL is set correctly.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Current database: {engine}'))
            self.stdout.write(self.style.WARNING('Set DATABASE_URL environment variable to use PostgreSQL.'))

    def export_data(self, backup_file):
        """Export data from current database to JSON file."""
        self.stdout.write(f'Exporting data to {backup_file}...')
        
        backup_path = Path(backup_file)
        
        try:
            # Export all data except permissions and contenttypes (they're auto-generated)
            with open(backup_path, 'w', encoding='utf-8') as f:
                call_command('dumpdata', 
                           '--exclude', 'auth.permission',
                           '--exclude', 'contenttypes',
                           '--natural-foreign',
                           '--natural-primary',
                           stdout=f,
                           verbosity=0)
            
            # Get file size
            file_size = backup_path.stat().st_size / (1024 * 1024)  # MB
            self.stdout.write(self.style.SUCCESS(f'✓ Exported data to {backup_file} ({file_size:.2f} MB)'))
            
            # Count records
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.stdout.write(f'  Records exported: {len(data)}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Export failed: {str(e)}'))

    def import_data(self, backup_file):
        """Import data from JSON file to current database."""
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            self.stdout.write(self.style.ERROR(f'✗ Backup file not found: {backup_file}'))
            return
        
        self.stdout.write(f'Importing data from {backup_file}...')
        
        # Check if we're using PostgreSQL
        db_config = settings.DATABASES['default']
        engine = db_config.get('ENGINE', '')
        
        if 'postgresql' not in engine and 'postgres' not in engine:
            self.stdout.write(self.style.WARNING('⚠ Not using PostgreSQL. Set DATABASE_URL first.'))
            response = input('Continue anyway? (yes/no): ')
            if response.lower() != 'yes':
                return
        
        try:
            # Run migrations first
            self.stdout.write('Running migrations...')
            call_command('migrate', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✓ Migrations complete'))
            
            # Load data
            self.stdout.write('Loading data...')
            call_command('loaddata', backup_file, verbosity=1)
            
            self.stdout.write(self.style.SUCCESS('✓ Data import complete'))
            
            # Show summary
            self.show_data_summary()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Import failed: {str(e)}'))
            self.stdout.write(self.style.WARNING('You may need to clear existing data first.'))

    def show_data_summary(self):
        """Show summary of imported data."""
        try:
            from core.models import Product, Sale, AppUser, StockAddition
            from core.models import PricingRecommendation, PriceChangeHistory
            
            self.stdout.write('\n' + '='*50)
            self.stdout.write('Data Summary:')
            self.stdout.write('='*50)
            self.stdout.write(f'Products: {Product.objects.count()}')
            self.stdout.write(f'Sales: {Sale.objects.count()}')
            self.stdout.write(f'Users: {AppUser.objects.count()}')
            self.stdout.write(f'Stock Additions: {StockAddition.objects.count()}')
            self.stdout.write(f'Pricing Recommendations: {PricingRecommendation.objects.count()}')
            self.stdout.write(f'Price Change History: {PriceChangeHistory.objects.count()}')
            self.stdout.write('='*50)
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not show summary: {str(e)}'))
