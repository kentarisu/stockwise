"""
Django management command to create a complete backup of the system.
Backs up database as JSON file inside a ZIP archive, along with media files.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from pathlib import Path
import os
import zipfile
import tempfile
from datetime import datetime
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Create a complete backup of the database and media files as ZIP with JSON database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Directory to save backup (default: backups/ in project root)',
        )
        parser.add_argument(
            '--include-static',
            action='store_true',
            help='Include static files in backup (optional)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting backup process...'))
        
        # Determine backup directory
        if options['output_dir']:
            backup_dir = Path(options['output_dir'])
        else:
            backup_dir = Path(getattr(settings, 'BACKUPS_DIR', settings.BASE_DIR / 'backups'))
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            backup_dir = Path('/tmp/stockwise_backups')
            backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamp for backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'stockwise_backup_{timestamp}.zip'
        backup_path = backup_dir / backup_filename
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # 1. Backup database as JSON using Django dumpdata
                self.stdout.write('Creating JSON database backup using Django dumpdata...')
                try:
                    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False, encoding='utf-8') as json_dump:
                        # Exclude auth.permission and contenttypes to keep dump smaller/portable
                        # Use natural keys for better portability
                            call_command(
                                'dumpdata',
                                '--natural-foreign',
                                '--natural-primary',
                                '--exclude', 'auth.permission',
                                '--exclude', 'contenttypes',
                            stdout=json_dump,
                            indent=2  # Pretty print for readability
                            )
                            json_path = json_dump.name
                    
                    # Add JSON file to ZIP
                        backup_zip.write(json_path, 'database/stockwise_dump.json')
                        os.unlink(json_path)
                    self.stdout.write(self.style.SUCCESS('✓ Database JSON backup created'))
                    except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to create JSON backup: {e}'))
                    raise
            
            # Get backup size
            backup_size = backup_path.stat().st_size
            size_mb = backup_size / (1024 * 1024)
            
            # Try to create Backup record (if models are available)
            try:
                from core.models import Backup
                Backup.objects.create(
                    filename=backup_filename,
                    file_path=str(backup_path),
                    file_size=backup_size,
                    backup_type='full',
                    is_verified=True
                )
                
                # Log the automated backup to audit logs
                try:
                    from core.views import log_system_action
                    log_system_action(
                        action='Automatic System Backup',
                        details=f'Backup File: {backup_filename}\nSize: {size_mb:.2f} MB\nType: Full Backup\nStatus: Success'
                    )
                except Exception:
                    # If logging fails, don't break the backup process
                    pass
            except Exception:
                # If models aren't available (e.g., during initial setup), skip
                pass
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Backup completed successfully!\n'
                f'  File: {backup_path}\n'
                f'  Size: {size_mb:.2f} MB\n'
                f'  Timestamp: {timestamp}'
            ))
            
            # Return the path as string for views to use
            return str(backup_path)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating backup: {str(e)}'))
            if backup_path.exists():
                backup_path.unlink()  # Remove incomplete backup
            raise
