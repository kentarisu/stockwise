"""
Django management command to restore from a backup ZIP file stored in fixtures folder.
This is specifically designed for Render deployment where we need to restore
data during the build command without shell access.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import os


class Command(BaseCommand):
    help = 'Restore system from backup ZIP file in fixtures/production_backup.zip'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-file',
            type=str,
            default='fixtures/production_backup.zip',
            help='Path to backup file (default: fixtures/production_backup.zip)',
        )

    def handle(self, *args, **options):
        backup_file = options['backup_file']
        backup_path = Path(settings.BASE_DIR) / backup_file
        
        if not backup_path.exists():
            self.stdout.write(self.style.WARNING(
                f'Backup file not found: {backup_path}\n'
                f'Skipping restore. This is normal for first deployment.'
            ))
            return
        
        self.stdout.write(self.style.SUCCESS(
            f'Found backup file: {backup_path}\n'
            f'Starting automatic restore for deployment...'
        ))
        
        # Call the existing restore_backup command with --force flag
        from django.core.management import call_command
        
        try:
            call_command('restore_backup', str(backup_path), force=True, verbosity=2)
            self.stdout.write(self.style.SUCCESS(
                '[OK] Data restored successfully from backup!'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'[ERROR] Failed to restore backup: {e}\n'
                f'Deployment will continue with empty/existing database.'
            ))
            # Don't raise - allow deployment to continue even if restore fails

