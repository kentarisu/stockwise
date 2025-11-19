"""
Django management command to clean up old backup files.
Keeps only the most recent N backups (default: 7 days).
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import os
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Clean up old backup files, keeping only recent ones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-days',
            type=int,
            default=7,
            help='Number of days of backups to keep (default: 7)',
        )
        parser.add_argument(
            '--keep-count',
            type=int,
            default=None,
            help='Number of most recent backups to keep (overrides --keep-days)',
        )

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR.parent) / 'backups'
        
        if not backup_dir.exists():
            self.stdout.write(self.style.WARNING('Backup directory does not exist.'))
            return
        
        # Get all backup files
        backup_files = list(backup_dir.glob('stockwise_backup_*.zip'))
        
        if not backup_files:
            self.stdout.write(self.style.SUCCESS('No backup files to clean up.'))
            return
        
        # Sort by modification time (newest first)
        backup_files.sort(key=os.path.getmtime, reverse=True)
        
        deleted_count = 0
        deleted_size = 0
        
        if options['keep_count']:
            # Keep only the N most recent backups
            keep_count = options['keep_count']
            files_to_delete = backup_files[keep_count:]
        else:
            # Keep backups from the last N days
            keep_days = options['keep_days']
            cutoff_date = timezone.now() - timedelta(days=keep_days)
            files_to_delete = []
            
            for backup_file in backup_files:
                file_mtime = os.path.getmtime(backup_file)
                file_date = timezone.datetime.fromtimestamp(file_mtime, tz=timezone.get_current_timezone())
                
                if file_date < cutoff_date:
                    files_to_delete.append(backup_file)
        
        # Delete old backup files
        for backup_file in files_to_delete:
            try:
                file_size = backup_file.stat().st_size
                backup_file.unlink()
                deleted_count += 1
                deleted_size += file_size
                
                # Also delete from database if record exists
                try:
                    from core.models import Backup
                    Backup.objects.filter(file_path=str(backup_file)).delete()
                except Exception:
                    pass
                
                self.stdout.write(f'Deleted: {backup_file.name}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error deleting {backup_file.name}: {str(e)}'))
        
        if deleted_count > 0:
            size_mb = deleted_size / (1024 * 1024)
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Cleanup completed!\n'
                f'  Deleted: {deleted_count} backup(s)\n'
                f'  Freed space: {size_mb:.2f} MB'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('No old backups to delete.'))

