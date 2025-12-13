"""
Django management command to fix duplicate column migration errors.

This command helps resolve issues where migrations try to add columns that already exist.

Usage:
    python manage.py fix_duplicate_column_migration
    python manage.py fix_duplicate_column_migration --migration 0041
    python manage.py fix_duplicate_column_migration --check-only
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Fix duplicate column migration errors by checking column existence'

    def add_arguments(self, parser):
        parser.add_argument(
            '--migration',
            type=str,
            help='Specific migration to fix (e.g., 0041)',
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check for duplicate columns, do not fix',
        )
        parser.add_argument(
            '--fake',
            action='store_true',
            help='Mark migration as applied without running it',
        )

    def handle(self, *args, **options):
        migration_num = options.get('migration', '0041')
        check_only = options.get('check_only', False)
        fake = options.get('fake', False)

        self.stdout.write('Checking for duplicate column issues...')
        
        # Check migration status first
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT app, name, applied 
                FROM django_migrations 
                WHERE app='core' 
                AND (name LIKE '%0041%' OR name LIKE '%pricing_fields%')
                ORDER BY applied DESC, name
            """)
            migration_status = cursor.fetchall()
            
            if migration_status:
                self.stdout.write('\nFound migrations:')
                for app, name, applied in migration_status:
                    status = '✓ Applied' if applied else '✗ Not applied'
                    self.stdout.write(f'  {status}: {app}.{name}')
        
        # Check for pricing_time and pricing_frequency_days columns
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name='sms_notification_settings' 
                AND column_name IN ('pricing_time', 'pricing_frequency_days')
                ORDER BY column_name
            """)
            existing_columns = cursor.fetchall()
            
            if existing_columns:
                self.stdout.write(self.style.WARNING(f'Found {len(existing_columns)} existing columns:'))
                for col_name, data_type, default in existing_columns:
                    self.stdout.write(f'  - {col_name} ({data_type}) default: {default}')
            else:
                self.stdout.write(self.style.SUCCESS('No duplicate columns found. Migration should run normally.'))
                return
            
            if check_only:
                return
            
            # Fix options
            if existing_columns and len(existing_columns) == 2:
                self.stdout.write(self.style.WARNING(
                    '\nBoth columns exist. You can mark the migration as applied:'
                ))
                self.stdout.write('  Use the full migration name to avoid ambiguity:')
                self.stdout.write('  python manage.py migrate core 0041_add_pricing_fields_to_sms_notification_settings --fake')
                
                if fake:
                    self.stdout.write('\nMarking migration as applied...')
                    try:
                        # Use full migration name to avoid ambiguity
                        call_command('migrate', 'core', '0041_add_pricing_fields_to_sms_notification_settings', '--fake', verbosity=1)
                        self.stdout.write(self.style.SUCCESS('✓ Migration marked as applied'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'✗ Failed: {str(e)}'))
                        self.stdout.write(self.style.WARNING('Try using the full migration name manually'))
            else:
                self.stdout.write(self.style.WARNING(
                    '\nSome columns are missing. The migration should run normally.'
                ))
                self.stdout.write('Try running: python manage.py migrate')
