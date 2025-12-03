"""
Django management command to create a complete backup of the system.
Backs up database and all media files.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from pathlib import Path
import shutil
import zipfile
import os
from datetime import datetime


class Command(BaseCommand):
    help = 'Create a complete backup of the database and media files'

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
                # 1. Backup database
                db_engine = settings.DATABASES['default']['ENGINE']
                db_name = settings.DATABASES['default']['NAME']
                
                if 'sqlite' in db_engine.lower():
                    # SQLite: backup the database file directly
                    db_path = db_name
                    if isinstance(db_path, Path):
                        db_path = str(db_path)
                    if os.path.exists(db_path):
                        db_filename = os.path.basename(db_path)
                        self.stdout.write(f'Backing up SQLite database: {db_filename}')
                        backup_zip.write(db_path, f'database/{db_filename}')
                        self.stdout.write(self.style.SUCCESS(f'✓ Database backed up'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Database file not found: {db_path}'))
                else:
                    # PostgreSQL, MySQL, etc.: create database dump
                    self.stdout.write(f'Creating database dump for {db_engine}...')
                    import tempfile
                    import subprocess
                    
                    dump_ext = '.sql'
                    if 'postgresql' in db_engine.lower() or 'postgres' in db_engine.lower():
                        dump_ext = '.pgdump'
                        dump_cmd = ['pg_dump', db_name]
                    elif 'mysql' in db_engine.lower():
                        dump_ext = '.mysqldump'
                        # Extract connection details for MySQL
                        db_user = settings.DATABASES['default'].get('USER', '')
                        db_pass = settings.DATABASES['default'].get('PASSWORD', '')
                        db_host = settings.DATABASES['default'].get('HOST', 'localhost')
                        db_port = settings.DATABASES['default'].get('PORT', '3306')
                        dump_cmd = ['mysqldump', '-u', db_user]
                        if db_pass:
                            dump_cmd.extend(['-p' + db_pass])
                        dump_cmd.extend(['-h', db_host, '-P', str(db_port), db_name])
                    else:
                        # Generic SQL dump (fallback)
                        dump_cmd = None
                    
                    if dump_cmd:
                        try:
                            with tempfile.NamedTemporaryFile(mode='w+b', suffix=dump_ext, delete=False) as dump_file:
                                result = subprocess.run(dump_cmd, stdout=dump_file, stderr=subprocess.PIPE, text=True)
                                if result.returncode == 0:
                                    dump_filename = f'database_backup{dump_ext}'
                                    backup_zip.write(dump_file.name, f'database/{dump_filename}')
                                    os.unlink(dump_file.name)
                                    self.stdout.write(self.style.SUCCESS(f'✓ Database dump created and backed up'))
                                else:
                                    self.stdout.write(self.style.ERROR(f'Failed to create database dump: {result.stderr}'))
                                    os.unlink(dump_file.name)
                        except FileNotFoundError:
                            self.stdout.write(self.style.WARNING(
                                f'Database dump tool not found. Please install the appropriate database client tools '
                                f'({dump_cmd[0]}) to enable database backups in production.'
                            ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'Database engine {db_engine} backup not automatically supported. '
                            f'Please create a manual database backup and include it in the backup zip.'
                        ))
                
                # 2. Backup media files (uploads)
                media_root = Path(settings.BASE_DIR.parent) / 'uploads'
                if media_root.exists():
                    self.stdout.write(f'Backing up media files from: {media_root}')
                    media_count = 0
                    for root, dirs, files in os.walk(media_root):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = f'media/{file_path.relative_to(media_root)}'
                            backup_zip.write(file_path, arcname)
                            media_count += 1
                    self.stdout.write(self.style.SUCCESS(f'✓ {media_count} media files backed up'))
                else:
                    self.stdout.write(self.style.WARNING(f'Media directory not found: {media_root}'))
                
                # 3. Backup static files (optional)
                if options['include_static']:
                    static_root = settings.STATIC_ROOT
                    if static_root and os.path.exists(static_root):
                        self.stdout.write(f'Backing up static files from: {static_root}')
                        static_count = 0
                        for root, dirs, files in os.walk(static_root):
                            for file in files:
                                file_path = Path(root) / file
                                arcname = f'static/{file_path.relative_to(static_root)}'
                                backup_zip.write(file_path, arcname)
                                static_count += 1
                        self.stdout.write(self.style.SUCCESS(f'✓ {static_count} static files backed up'))
                
                # 4. Backup .env file (if exists) - contains important configuration
                env_path = Path(settings.BASE_DIR.parent) / '.env'
                if env_path.exists():
                    self.stdout.write('Backing up .env file')
                    backup_zip.write(env_path, '.env')
                    self.stdout.write(self.style.SUCCESS('✓ .env file backed up'))
            
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
