"""
Django management command to restore from a backup.
Restores database and media files from a backup zip file.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
from pathlib import Path
import zipfile
import shutil
import os
import sys


class Command(BaseCommand):
    help = 'Restore system from a backup zip file'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Path to the backup zip file to restore from',
        )
        parser.add_argument(
            '--no-database',
            action='store_true',
            help='Skip database restoration',
        )
        parser.add_argument(
            '--no-media',
            action='store_true',
            help='Skip media files restoration',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force restore without confirmation prompts',
        )

    def handle(self, *args, **options):
        backup_file = Path(options['backup_file'])
        
        if not backup_file.exists():
            self.stdout.write(self.style.ERROR(f'Backup file not found: {backup_file}'))
            sys.exit(1)
        
        if not backup_file.suffix == '.zip':
            self.stdout.write(self.style.ERROR('Backup file must be a .zip file'))
            sys.exit(1)
        
        # Confirmation prompt
        if not options['force']:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  WARNING: This will overwrite your current database and media files!\n'
                'All current data will be replaced with data from the backup.\n'
            ))
            confirm = input('Are you sure you want to continue? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.SUCCESS('Restore cancelled.'))
                return
        
        self.stdout.write(self.style.SUCCESS(f'Starting restore from: {backup_file}'))
        
        try:
            with zipfile.ZipFile(backup_file, 'r') as backup_zip:
                # List contents
                file_list = backup_zip.namelist()
                
                # 1. Restore database
                if not options['no_database']:
                    db_files = [f for f in file_list if f.startswith('database/') and not f.endswith('/')]
                    if db_files:
                        self.stdout.write('Restoring database...')
                        db_engine = settings.DATABASES['default']['ENGINE']
                        db_name = settings.DATABASES['default']['NAME']
                        
                        for db_file in db_files:
                            db_filename = os.path.basename(db_file)
                            db_file_lower = db_filename.lower()
                            
                            if 'sqlite' in db_engine.lower():
                                # SQLite: restore database file directly
                                if db_file_lower.endswith(('.sqlite3', '.db', '.sqlite')):
                                    temp_db = Path(settings.BASE_DIR.parent) / 'temp_restore_db.sqlite3'
                                    # Extract to temp file
                                    with backup_zip.open(db_file) as source:
                                        with open(temp_db, 'wb') as target:
                                            target.write(source.read())
                                    
                                    # Replace database file
                                    db_path = db_name
                                    if isinstance(db_path, Path):
                                        db_path = str(db_path)
                                    
                                    if os.path.exists(db_path):
                                        # Create backup of current DB before overwriting
                                        backup_current = f'{db_path}.backup_{Path(backup_file).stem}'
                                        shutil.copy2(db_path, backup_current)
                                        self.stdout.write(f'  - Current database backed up to: {backup_current}')
                                    
                                    # Copy temp DB to actual location
                                    shutil.copy2(temp_db, db_path)
                                    os.remove(temp_db)
                                    
                                    self.stdout.write(self.style.SUCCESS(f'  ✓ Database restored: {db_filename}'))
                                    
                                    # Run migrations to ensure schema is up to date
                                    self.stdout.write('  - Running migrations...')
                                    call_command('migrate', verbosity=0)
                                    self.stdout.write(self.style.SUCCESS('  ✓ Migrations completed'))
                                else:
                                    self.stdout.write(self.style.WARNING(
                                        f'  ⚠ Database file {db_filename} is not a SQLite file. '
                                        f'Current database engine is SQLite. Skipping database restore.'
                                    ))
                            else:
                                # PostgreSQL, MySQL, etc.: restore from dump
                                if db_file_lower.endswith(('.sql', '.dump', '.pgdump', '.mysqldump', '.backup')):
                                    import tempfile
                                    import subprocess
                                    
                                    # Extract dump to temp file
                                    with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix=os.path.splitext(db_filename)[1]) as dump_file:
                                        with backup_zip.open(db_file) as source:
                                            dump_file.write(source.read())
                                        dump_path = dump_file.name
                                    
                                    try:
                                        if 'postgresql' in db_engine.lower() or 'postgres' in db_engine.lower():
                                            # PostgreSQL restore
                                            db_user = settings.DATABASES['default'].get('USER', '')
                                            db_pass = settings.DATABASES['default'].get('PASSWORD', '')
                                            db_host = settings.DATABASES['default'].get('HOST', 'localhost')
                                            db_port = settings.DATABASES['default'].get('PORT', '5432')
                                            
                                            restore_cmd = ['psql']
                                            if db_host:
                                                restore_cmd.extend(['-h', db_host])
                                            if db_port:
                                                restore_cmd.extend(['-p', str(db_port)])
                                            if db_user:
                                                restore_cmd.extend(['-U', db_user])
                                            restore_cmd.extend(['-d', db_name, '-f', dump_path])
                                            
                                            env = os.environ.copy()
                                            if db_pass:
                                                env['PGPASSWORD'] = db_pass
                                            
                                            result = subprocess.run(restore_cmd, env=env, stderr=subprocess.PIPE, text=True)
                                            if result.returncode == 0:
                                                self.stdout.write(self.style.SUCCESS(f'  ✓ Database restored from dump: {db_filename}'))
                                            else:
                                                self.stdout.write(self.style.ERROR(f'  ✗ Failed to restore database: {result.stderr}'))
                                        
                                        elif 'mysql' in db_engine.lower():
                                            # MySQL restore
                                            db_user = settings.DATABASES['default'].get('USER', '')
                                            db_pass = settings.DATABASES['default'].get('PASSWORD', '')
                                            db_host = settings.DATABASES['default'].get('HOST', 'localhost')
                                            db_port = settings.DATABASES['default'].get('PORT', '3306')
                                            
                                            restore_cmd = ['mysql', '-u', db_user]
                                            if db_pass:
                                                restore_cmd.extend(['-p' + db_pass])
                                            restore_cmd.extend(['-h', db_host, '-P', str(db_port), db_name])
                                            
                                            with open(dump_path, 'r') as dump:
                                                result = subprocess.run(restore_cmd, stdin=dump, stderr=subprocess.PIPE, text=True)
                                            
                                            if result.returncode == 0:
                                                self.stdout.write(self.style.SUCCESS(f'  ✓ Database restored from dump: {db_filename}'))
                                            else:
                                                self.stdout.write(self.style.ERROR(f'  ✗ Failed to restore database: {result.stderr}'))
                                        else:
                                            self.stdout.write(self.style.WARNING(
                                                f'  ⚠ Database engine {db_engine} restore not automatically supported. '
                                                f'Please restore the database dump manually: {dump_path}'
                                            ))
                                    except FileNotFoundError:
                                        self.stdout.write(self.style.ERROR(
                                            f'  ✗ Database client tool not found. Please install the appropriate '
                                            f'database client tools to restore the database dump.'
                                        ))
                                    finally:
                                        if os.path.exists(dump_path):
                                            os.unlink(dump_path)
                                else:
                                    self.stdout.write(self.style.WARNING(
                                        f'  ⚠ Database file {db_filename} format not recognized. Skipping.'
                                    ))
                    else:
                        self.stdout.write(self.style.WARNING('No database file found in backup'))
                
                # 2. Restore media files
                if not options['no_media']:
                    media_files = [f for f in file_list if f.startswith('media/')]
                    if media_files:
                        self.stdout.write('Restoring media files...')
                        media_root = Path(settings.BASE_DIR.parent) / 'uploads'
                        media_root.mkdir(parents=True, exist_ok=True)
                        
                        # Backup current media files
                        if media_root.exists() and any(media_root.iterdir()):
                            backup_media = Path(settings.BASE_DIR.parent) / f'uploads_backup_{Path(backup_file).stem}'
                            if backup_media.exists():
                                shutil.rmtree(backup_media)
                            shutil.copytree(media_root, backup_media)
                            self.stdout.write(f'  - Current media files backed up to: {backup_media}')
                        
                        # Extract media files
                        media_count = 0
                        for media_file in media_files:
                            # Get relative path within media directory
                            relative_path = media_file.replace('media/', '')
                            target_path = media_root / relative_path
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            with backup_zip.open(media_file) as source:
                                with open(target_path, 'wb') as target:
                                    target.write(source.read())
                            media_count += 1
                        
                        self.stdout.write(self.style.SUCCESS(f'  ✓ {media_count} media files restored'))
                    else:
                        self.stdout.write(self.style.WARNING('No media files found in backup'))
                
                # 3. Restore .env file (optional, with warning)
                env_files = [f for f in file_list if f == '.env']
                if env_files:
                    self.stdout.write(self.style.WARNING(
                        '\n⚠️  Backup contains .env file. Restoring it will overwrite current configuration.'
                    ))
                    if options['force'] or input('Restore .env file? (yes/no): ').lower() == 'yes':
                        env_path = Path(settings.BASE_DIR.parent) / '.env'
                        if env_path.exists():
                            backup_env = f'{env_path}.backup_{Path(backup_file).stem}'
                            shutil.copy2(env_path, backup_env)
                            self.stdout.write(f'  - Current .env backed up to: {backup_env}')
                        
                        with backup_zip.open('.env') as source:
                            with open(env_path, 'wb') as target:
                                target.write(source.read())
                        self.stdout.write(self.style.SUCCESS('  ✓ .env file restored'))
            
            self.stdout.write(self.style.SUCCESS(
                '\n✓ Restore completed successfully!\n'
                'Please restart your Django server to ensure all changes take effect.'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during restore: {str(e)}'))
            import traceback
            traceback.print_exc()
            sys.exit(1)

