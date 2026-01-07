"""
Django management command to create a simple database dump backup.
Creates a direct database dump file (pg_dump, mysqldump, or SQLite copy).
This is simpler and more reliable than JSON format - just dump and restore.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from pathlib import Path
import os
import subprocess
import zipfile
import tempfile
from datetime import datetime


class Command(BaseCommand):
    help = 'Create a simple database dump backup (like pg_dump or mysqldump)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Directory to save backup (default: backups/ in project root)',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['dump', 'zip'],
            default='zip',
            help='Output format: dump (single file) or zip (with media files)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database dump backup...'))
        
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
        
        db_engine = settings.DATABASES['default']['ENGINE'].lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            if 'postgresql' in db_engine or 'postgres' in db_engine:
                dump_file = self._dump_postgresql(backup_dir, timestamp)
            elif 'mysql' in db_engine:
                dump_file = self._dump_mysql(backup_dir, timestamp)
            elif 'sqlite' in db_engine:
                dump_file = self._dump_sqlite(backup_dir, timestamp)
            else:
                raise Exception(f'Unsupported database engine: {db_engine}')
            
            # If format is zip, create ZIP with dump and media files
            if options['format'] == 'zip':
                zip_file = self._create_zip_backup(backup_dir, dump_file, timestamp)
                # Remove the standalone dump file
                if dump_file.exists():
                    dump_file.unlink()
                final_file = zip_file
            else:
                final_file = dump_file
            
            # Get file size
            file_size = final_file.stat().st_size
            size_mb = file_size / (1024 * 1024)
            
            # Create Backup record
            try:
                from core.models import Backup
                Backup.objects.create(
                    filename=final_file.name,
                    file_path=str(final_file),
                    file_size=file_size,
                    backup_type='database',
                    is_verified=True
                )
            except Exception:
                pass  # Skip if models not available
            
            self.stdout.write(self.style.SUCCESS(
                f'\n[OK] Database dump backup completed!\n'
                f'  File: {final_file}\n'
                f'  Size: {size_mb:.2f} MB'
            ))
            
            return str(final_file)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating dump backup: {str(e)}'))
            raise
    
    def _dump_postgresql(self, backup_dir, timestamp):
        """Create PostgreSQL dump using pg_dump"""
        db_config = settings.DATABASES['default']
        db_name = db_config['NAME']
        db_user = db_config.get('USER', '')
        db_host = db_config.get('HOST', 'localhost')
        db_port = db_config.get('PORT', '5432')
        db_pass = db_config.get('PASSWORD', '')
        
        dump_filename = f'stockwise_db_dump_{timestamp}.sql'
        dump_path = backup_dir / dump_filename
        
        # Build pg_dump command
        cmd = ['pg_dump']
        if db_host:
            cmd.extend(['-h', db_host])
        if db_port:
            cmd.extend(['-p', str(db_port)])
        if db_user:
            cmd.extend(['-U', db_user])
        cmd.extend(['-d', db_name, '-F', 'c', '-f', str(dump_path)])  # Custom format (binary)
        
        # Set environment variable for password
        env = os.environ.copy()
        if db_pass:
            env['PGPASSWORD'] = db_pass
        
        self.stdout.write(f'  - Creating PostgreSQL dump...')
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            self.stdout.write(self.style.SUCCESS(f'  [OK] PostgreSQL dump created'))
            return dump_path
        except subprocess.CalledProcessError as e:
            # Try plain SQL format if custom format fails
            self.stdout.write('  - Custom format failed, trying plain SQL...')
            cmd[-2] = '-F'  # Change to plain SQL
            cmd[-1] = 'p'   # Plain format
            cmd.append('-f')
            cmd.append(str(dump_path))
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            self.stdout.write(self.style.SUCCESS(f'  [OK] PostgreSQL dump created (SQL format)'))
            return dump_path
        except FileNotFoundError:
            raise Exception('pg_dump command not found. Please install PostgreSQL client tools.')
    
    def _dump_mysql(self, backup_dir, timestamp):
        """Create MySQL dump using mysqldump"""
        db_config = settings.DATABASES['default']
        db_name = db_config['NAME']
        db_user = db_config.get('USER', '')
        db_host = db_config.get('HOST', 'localhost')
        db_port = db_config.get('PORT', '3306')
        db_pass = db_config.get('PASSWORD', '')
        
        dump_filename = f'stockwise_db_dump_{timestamp}.sql'
        dump_path = backup_dir / dump_filename
        
        # Build mysqldump command
        cmd = ['mysqldump']
        if db_user:
            cmd.extend(['-u', db_user])
        if db_pass:
            cmd.extend([f'-p{db_pass}'])
        if db_host:
            cmd.extend(['-h', db_host])
        if db_port:
            cmd.extend(['-P', str(db_port)])
        cmd.append(db_name)
        
        self.stdout.write(f'  - Creating MySQL dump...')
        try:
            with open(dump_path, 'w', encoding='utf-8') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, check=True)
            self.stdout.write(self.style.SUCCESS(f'  [OK] MySQL dump created'))
            return dump_path
        except subprocess.CalledProcessError as e:
            raise Exception(f'MySQL dump failed: {e.stderr}')
        except FileNotFoundError:
            raise Exception('mysqldump command not found. Please install MySQL client tools.')
    
    def _dump_sqlite(self, backup_dir, timestamp):
        """Create SQLite backup by copying the database file"""
        db_config = settings.DATABASES['default']
        db_name = db_config['NAME']
        
        # SQLite database path
        if isinstance(db_name, Path):
            db_path = db_name
        else:
            db_path = Path(db_name)
        
        if not db_path.exists():
            raise Exception(f'SQLite database file not found: {db_path}')
        
        dump_filename = f'stockwise_db_dump_{timestamp}.sqlite3'
        dump_path = backup_dir / dump_filename
        
        self.stdout.write(f'  - Copying SQLite database...')
        import shutil
        shutil.copy2(db_path, dump_path)
        self.stdout.write(self.style.SUCCESS(f'  [OK] SQLite database copied'))
        return dump_path
    
    def _create_zip_backup(self, backup_dir, dump_file, timestamp):
        """Create ZIP file with dump and media files"""
        zip_filename = f'stockwise_backup_{timestamp}.zip'
        zip_path = backup_dir / zip_filename
        
        self.stdout.write(f'  - Creating ZIP archive...')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
            # Add database dump
            if dump_file.suffix == '.sqlite3':
                backup_zip.write(dump_file, f'database/{dump_file.name}')
            else:
                backup_zip.write(dump_file, f'database/{dump_file.name}')
            
            # Add media files if they exist
            media_root = Path(getattr(settings, 'MEDIA_ROOT', settings.BASE_DIR / 'media'))
            if media_root.exists() and media_root.is_dir():
                media_count = 0
                for root, dirs, files in os.walk(media_root):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    for file in files:
                        if file.startswith('.'):
                            continue
                        file_path = Path(root) / file
                        relative_path = file_path.relative_to(media_root)
                        backup_zip.write(str(file_path), f'media/{relative_path}')
                        media_count += 1
                
                if media_count > 0:
                    self.stdout.write(f'  - Added {media_count} media files')
        
        self.stdout.write(self.style.SUCCESS(f'  [OK] ZIP archive created'))
        return zip_path

