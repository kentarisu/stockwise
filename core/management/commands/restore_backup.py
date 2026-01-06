"""
Django management command to restore from a backup.
Restores database from a backup JSON file.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
from pathlib import Path
import zipfile
import shutil
import os
import sys
import json
from core.models import AppUser


class Command(BaseCommand):
    help = 'Restore system from a backup JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Path to the backup JSON file to restore from',
        )
        parser.add_argument(
            '--no-database',
            action='store_true',
            help='Skip database restoration',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force restore without confirmation prompts',
        )

    def handle(self, *args, **options):
        backup_file = Path(options['backup_file'])
        
        if not backup_file.exists():
            error_msg = f'Backup file not found: {backup_file}'
            self.stdout.write(self.style.ERROR(error_msg))
            raise Exception(error_msg)
        
        # Accept both .json and .zip files for backward compatibility
        if backup_file.suffix not in ['.json', '.zip']:
            error_msg = 'Backup file must be a .json or .zip file'
            self.stdout.write(self.style.ERROR(error_msg))
            raise Exception(error_msg)
        
        # Confirmation prompt
        if not options['force']:
            self.stdout.write(self.style.WARNING(
                '\n[WARNING]️  WARNING: This will overwrite your current database!\n'
                'All current data will be replaced with data from the backup.\n'
            ))
            confirm = input('Are you sure you want to continue? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.SUCCESS('Restore cancelled.'))
                return
        
        self.stdout.write(self.style.SUCCESS(f'Starting restore from: {backup_file}'))
        
        try:
            # Handle JSON files directly
            if backup_file.suffix == '.json':
                self._restore_from_json(backup_file, options)
            else:
                # Handle ZIP files for backward compatibility
                self._restore_from_zip(backup_file, options)
            
            # Fix sequences after restore (important for PostgreSQL)
            if not options['no_database']:
                try:
                    if 'postgresql' in settings.DATABASES['default']['ENGINE']:
                        self.stdout.write('  - Fixing database sequences...')
                        call_command('fix_sequences', verbosity=0)
                        self.stdout.write(self.style.SUCCESS('  [OK] Sequences fixed'))
                except Exception as seq_error:
                    # Log but don't fail if sequence fix fails
                    self.stdout.write(self.style.WARNING(f'  [WARNING] Warning fixing sequences: {seq_error}'))
            
            # Log the restore operation to audit logs
            try:
                from core.views import log_system_action
                backup_filename = backup_file.name
                backup_size = backup_file.stat().st_size / (1024 * 1024)  # Convert to MB
                log_system_action(
                    action='System Restore from Backup',
                    details=f'Backup File: {backup_filename}\nSize: {backup_size:.2f} MB\nDatabase Restored: {"Yes" if not options["no_database"] else "No"}\nStatus: Success'
                )
            except Exception:
                # If logging fails, don't break the restore process
                pass
            
            self.stdout.write(self.style.SUCCESS(
                '\n[OK] Restore completed successfully!\n'
                'Please restart your Django server to ensure all changes take effect.'
            ))
            
        except Exception as e:
            error_msg = f'Error during restore: {str(e)}'
            self.stdout.write(self.style.ERROR(error_msg))
            import traceback
            traceback.print_exc()
            # Re-raise the exception instead of sys.exit so it can be caught by callers
            raise
    
    def _restore_from_json(self, backup_file, options):
        """Restore from a JSON backup file"""
        if not options['no_database']:
            # Validate JSON file
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    json.load(f)  # Validate JSON structure
            except json.JSONDecodeError as e:
                error_msg = f'Invalid JSON file: {e}'
                self.stdout.write(self.style.ERROR(error_msg))
                raise Exception(error_msg)
            
            # Preserve current users
            preserved_users = list(AppUser.objects.values('username','password','role','phone_number','email','is_active','full_name'))
            
            self.stdout.write('Restoring database from JSON...')
            
            # Validate JSON file structure and filter problematic entries
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    if not isinstance(json_data, list) or len(json_data) == 0:
                        self.stdout.write(self.style.WARNING('  [WARNING] JSON file appears to be empty or invalid'))
                    else:
                        original_count = len(json_data)
                        self.stdout.write(f'  - Found {original_count} objects in backup file')
                        
                        # Filter out problematic entries before loading
                        json_data = self._filter_problematic_entries(json_data)
                        filtered_count = len(json_data)
                        
                        if filtered_count < original_count:
                            self.stdout.write(self.style.WARNING(
                                f'  [WARNING] Filtered out {original_count - filtered_count} problematic entries'
                            ))
                            # Write filtered data back to file
                            with open(backup_file, 'w', encoding='utf-8') as f:
                                json.dump(json_data, f, ensure_ascii=False, indent=2)
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f'Invalid JSON file: {e}'))
                sys.exit(1)
            
            # Close database connections before clearing
            from django.db import connections
            connections.close_all()
            
            # Preserve user accounts before clearing
            from core.models import AppUser
            preserved_users = list(AppUser.objects.all().values(
                'user_id', 'username', 'password', 'role', 'phone_number', 
                'email', 'is_active', 'full_name'
            ))
            self.stdout.write(f'  - Preserved {len(preserved_users)} user accounts')
            
            # Clear existing data before loading backup (EXCEPT users)
            # This is critical - loaddata doesn't clear data, it just inserts
            self.stdout.write('  - Clearing existing database data (preserving accounts)...')
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    # Disable foreign key checks temporarily
                    if 'sqlite' in settings.DATABASES['default']['ENGINE'].lower():
                        cursor.execute("PRAGMA foreign_keys = OFF")
                    elif 'postgresql' in settings.DATABASES['default']['ENGINE'].lower():
                        cursor.execute("SET session_replication_role = 'replica'")
                    
                    # Get all table names EXCEPT app users
                    if 'sqlite' in settings.DATABASES['default']['ENGINE'].lower():
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'core_appuser'")
                        tables = [row[0] for row in cursor.fetchall()]
                        for table in tables:
                            if table != 'core_appuser':  # Extra safety check
                                cursor.execute(f"DELETE FROM {table}")
                    elif 'postgresql' in settings.DATABASES['default']['ENGINE'].lower():
                        cursor.execute("""
                            SELECT tablename FROM pg_tables 
                            WHERE schemaname = 'public' 
                            AND tablename NOT LIKE 'django_%'
                            AND tablename != 'core_appuser'
                        """)
                        tables = [row[0] for row in cursor.fetchall()]
                        for table in tables:
                            if table != 'core_appuser':  # Extra safety check
                                cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                    
                    # Re-enable foreign key checks
                    if 'sqlite' in settings.DATABASES['default']['ENGINE'].lower():
                        cursor.execute("PRAGMA foreign_keys = ON")
                    elif 'postgresql' in settings.DATABASES['default']['ENGINE'].lower():
                        cursor.execute("SET session_replication_role = 'origin'")
                    
                    self.stdout.write(self.style.SUCCESS('  [OK] Database cleared (accounts preserved)'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [ERROR] Failed to clear database: {e}'))
                raise
            
            # Run migrations to ensure schema is up to date before loading data
            self.stdout.write('  - Running migrations...')
            call_command('migrate', verbosity=0)
            self.stdout.write(self.style.SUCCESS('  [OK] Migrations completed'))
            
            # Load data from JSON file
            try:
                self.stdout.write('  - Loading backup data...')
                
                # For PostgreSQL, disable constraints temporarily during load
                from django.db import connection
                is_postgresql = 'postgresql' in settings.DATABASES['default']['ENGINE']
                
                if is_postgresql:
                    self.stdout.write('  - Disabling PostgreSQL constraints...')
                    with connection.cursor() as cursor:
                        # Disable triggers (includes FK constraints)
                        cursor.execute("SET session_replication_role = 'replica';")
                    self.stdout.write(self.style.SUCCESS('  [OK] Constraints disabled'))
                
                try:
                    # Use verbosity=2 to see more details
                    # --ignorenonexistent to skip missing models
                    call_command('loaddata', str(backup_file), verbosity=2, ignorenonexistent=True)
                    self.stdout.write(self.style.SUCCESS('  [OK] JSON data loaded'))
                finally:
                    # Re-enable constraints for PostgreSQL
                    if is_postgresql:
                        self.stdout.write('  - Re-enabling PostgreSQL constraints...')
                        with connection.cursor() as cursor:
                            cursor.execute("SET session_replication_role = 'origin';")
                        self.stdout.write(self.style.SUCCESS('  [OK] Constraints re-enabled'))
                
                # Verify data was loaded by checking a few key models
                try:
                    from core.models import Product, Sale, StockAddition
                    product_count = Product.objects.count()
                    sale_count = Sale.objects.count()
                    stock_count = StockAddition.objects.count()
                    self.stdout.write(f'  - Verification: {product_count} products, {sale_count} sales, {stock_count} stock additions restored')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  [WARNING] Could not verify restored data: {e}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [ERROR] Failed to load JSON data: {e}'))
                import traceback
                traceback.print_exc()
                raise
            
            # Ensure accounts are preserved
            def _ensure_accounts():
                try:
                    created = 0
                    for u in preserved_users:
                        if not AppUser.objects.filter(username=u['username']).exists():
                            AppUser.objects.create(
                                username=u.get('username') or '',
                                password=u.get('password') or '',
                                role=u.get('role') or 'Secretary',
                                phone_number=u.get('phone_number') or '',
                                email=u.get('email'),
                                is_active=bool(u.get('is_active')),
                                full_name=u.get('full_name') or ''
                            )
                            created += 1
                    if not AppUser.objects.exists():
                        call_command('create_users')
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'  [OK] Restored {created} account(s)'))
                    else:
                        self.stdout.write('  - Accounts verified')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  [WARNING] Account preservation warning: {e}'))
            
            _ensure_accounts()
    
    def _restore_from_zip(self, backup_file, options):
        """Restore from a ZIP backup file (backward compatibility)"""
        with zipfile.ZipFile(backup_file, 'r') as backup_zip:
            # List contents
            file_list = backup_zip.namelist()
            preserved_users = list(AppUser.objects.values('username','password','role','phone_number','email','is_active','full_name'))
            
            # 1. Restore database
            if not options['no_database']:
                # Check for JSON file in database/ folder (new format from backup_system)
                db_files = [f for f in file_list if f.startswith('database/') and not f.endswith('/')]
                # Also check for JSON file in root of ZIP (legacy format)
                json_files = [f for f in file_list if f.endswith('.json') and not f.startswith('database/') and not f.startswith('media/')]
                
                # Prioritize database/stockwise_dump.json (new format)
                json_file = None
                if db_files:
                    json_in_db = [f for f in db_files if f.endswith('.json')]
                    if json_in_db:
                        json_file = json_in_db[0]
                        self.stdout.write(f'Found JSON backup file in ZIP: {json_file}')
                elif json_files:
                    json_file = json_files[0]
                    self.stdout.write(f'Found JSON backup file in ZIP root: {json_file}')
                
                if json_file:
                    # JSON file found in ZIP (either in database/ folder or root)
                    self.stdout.write('Restoring database from JSON file in ZIP...')
                    
                    # Close database connections before clearing
                    from django.db import connections
                    connections.close_all()
                    
                    # Clear existing data before loading backup
                    self.stdout.write('  - Clearing existing database data...')
                    try:
                        call_command('flush', '--noinput', verbosity=0)
                        self.stdout.write(self.style.SUCCESS('  [OK] Database cleared'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  [WARNING] Warning clearing database: {e}'))
                        # If flush fails, try manual truncation as fallback
                        try:
                            from django.db import connection
                            with connection.cursor() as cursor:
                                # Disable foreign key checks temporarily
                                if 'sqlite' in settings.DATABASES['default']['ENGINE'].lower():
                                    cursor.execute("PRAGMA foreign_keys = OFF")
                                elif 'postgresql' in settings.DATABASES['default']['ENGINE'].lower():
                                    cursor.execute("SET session_replication_role = 'replica'")
                                
                                # Get all table names EXCEPT app users
                                if 'sqlite' in settings.DATABASES['default']['ENGINE'].lower():
                                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'core_appuser'")
                                    tables = [row[0] for row in cursor.fetchall()]
                                    for table in tables:
                                        if table != 'core_appuser':  # Extra safety check
                                            cursor.execute(f"DELETE FROM {table}")
                                elif 'postgresql' in settings.DATABASES['default']['ENGINE'].lower():
                                    cursor.execute("""
                                        SELECT tablename FROM pg_tables 
                                        WHERE schemaname = 'public' 
                                        AND tablename NOT LIKE 'django_%'
                                        AND tablename != 'core_appuser'
                                    """)
                                    tables = [row[0] for row in cursor.fetchall()]
                                    for table in tables:
                                        if table != 'core_appuser':  # Extra safety check
                                            cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                                    cursor.execute("SET session_replication_role = 'origin'")
                                
                                # Re-enable foreign key checks
                                if 'sqlite' in settings.DATABASES['default']['ENGINE'].lower():
                                    cursor.execute("PRAGMA foreign_keys = ON")
                                
                                self.stdout.write(self.style.SUCCESS('  [OK] Database cleared (manual method)'))
                        except Exception as e2:
                            self.stdout.write(self.style.ERROR(f'  [ERROR] Failed to clear database: {e2}'))
                            raise
                    
                    # Run migrations before loading data
                    self.stdout.write('  - Running migrations...')
                    call_command('migrate', verbosity=0)
                    self.stdout.write(self.style.SUCCESS('  [OK] Migrations completed'))
                    
                    # Extract JSON file from ZIP
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.json', delete=False) as temp_json:
                        with backup_zip.open(json_file) as source:
                            temp_json.write(source.read())
                        json_path = temp_json.name
                    
                    # Validate and filter JSON before loading
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                            if not isinstance(json_data, list) or len(json_data) == 0:
                                self.stdout.write(self.style.WARNING('  [WARNING] JSON file appears to be empty or invalid'))
                            else:
                                original_count = len(json_data)
                                self.stdout.write(f'  - Found {original_count} objects in backup file')
                                
                                # Filter out problematic entries before loading
                                json_data = self._filter_problematic_entries(json_data)
                                filtered_count = len(json_data)
                                
                                if filtered_count < original_count:
                                    self.stdout.write(self.style.WARNING(
                                        f'  [WARNING] Filtered out {original_count - filtered_count} problematic entries'
                                    ))
                                    # Write filtered data back to file
                                    with open(json_path, 'w', encoding='utf-8') as f:
                                        json.dump(json_data, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  [ERROR] Invalid JSON file: {e}'))
                        if os.path.exists(json_path):
                            os.unlink(json_path)
                        raise
                    
                    try:
                        self.stdout.write('  - Loading backup data...')
                        # Use verbosity=2 to see more details
                        call_command('loaddata', json_path, verbosity=2)
                        self.stdout.write(self.style.SUCCESS('  [OK] JSON data loaded'))
                        
                        # Verify data was loaded by checking a few key models
                        try:
                            from core.models import Product, Sale, StockAddition
                            product_count = Product.objects.count()
                            sale_count = Sale.objects.count()
                            stock_count = StockAddition.objects.count()
                            self.stdout.write(f'  - Verification: {product_count} products, {sale_count} sales, {stock_count} stock additions restored')
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f'  [WARNING] Could not verify restored data: {e}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  [ERROR] Failed to load JSON data: {e}'))
                        import traceback
                        traceback.print_exc()
                        raise
                    finally:
                        if os.path.exists(json_path):
                            os.unlink(json_path)
                elif db_files:
                    # Old format: database folder in ZIP
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
                                
                                self.stdout.write(self.style.SUCCESS(f'  [OK] Database restored: {db_filename}'))
                                
                                # Run migrations to ensure schema is up to date
                                self.stdout.write('  - Running migrations...')
                                call_command('migrate', verbosity=0)
                                self.stdout.write(self.style.SUCCESS('  [OK] Migrations completed'))
                            else:
                                self.stdout.write(self.style.WARNING(
                                    f'  [WARNING] Database file {db_filename} is not a SQLite file. '
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
                                            self.stdout.write(self.style.SUCCESS(f'  [OK] Database restored from dump: {db_filename}'))
                                        else:
                                            self.stdout.write(self.style.ERROR(f'  [ERROR] Failed to restore database: {result.stderr}'))
                                    
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
                                            self.stdout.write(self.style.SUCCESS(f'  [OK] Database restored from dump: {db_filename}'))
                                        else:
                                            self.stdout.write(self.style.ERROR(f'  [ERROR] Failed to restore database: {result.stderr}'))
                                    else:
                                        self.stdout.write(self.style.WARNING(
                                            f'  [WARNING] Database engine {db_engine} restore not automatically supported. '
                                            f'Please restore the database dump manually: {dump_path}'
                                        ))
                                except FileNotFoundError:
                                    self.stdout.write(self.style.ERROR(
                                        f'  [ERROR] Database client tool not found. Please install the appropriate '
                                        f'database client tools to restore the database dump.'
                                    ))
                                finally:
                                    if os.path.exists(dump_path):
                                        os.unlink(dump_path)
                            elif db_file_lower.endswith('.json'):
                                # Django dumpdata JSON fallback
                                # Clear existing data before loading backup
                                self.stdout.write('  - Clearing existing database data...')
                                try:
                                    call_command('flush', '--noinput', verbosity=0)
                                    self.stdout.write(self.style.SUCCESS('  [OK] Database cleared'))
                                except Exception as e:
                                    self.stdout.write(self.style.WARNING(f'  [WARNING] Warning clearing database: {e}'))
                                    # If flush fails, try manual truncation as fallback
                                    try:
                                        from django.db import connection
                                        with connection.cursor() as cursor:
                                            # Disable foreign key checks temporarily
                                            if 'sqlite' in settings.DATABASES['default']['ENGINE'].lower():
                                                cursor.execute("PRAGMA foreign_keys = OFF")
                                            elif 'postgresql' in settings.DATABASES['default']['ENGINE'].lower():
                                                cursor.execute("SET session_replication_role = 'replica'")
                                            
                                            # Get all table names
                                            if 'sqlite' in settings.DATABASES['default']['ENGINE'].lower():
                                                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                                                tables = [row[0] for row in cursor.fetchall()]
                                                for table in tables:
                                                    cursor.execute(f"DELETE FROM {table}")
                                            elif 'postgresql' in settings.DATABASES['default']['ENGINE'].lower():
                                                cursor.execute("""
                                                    SELECT tablename FROM pg_tables 
                                                    WHERE schemaname = 'public' 
                                                    AND tablename NOT LIKE 'django_%'
                                                """)
                                                tables = [row[0] for row in cursor.fetchall()]
                                                for table in tables:
                                                    cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
                                                cursor.execute("SET session_replication_role = 'origin'")
                                            
                                            # Re-enable foreign key checks
                                            if 'sqlite' in settings.DATABASES['default']['ENGINE'].lower():
                                                cursor.execute("PRAGMA foreign_keys = ON")
                                            
                                            self.stdout.write(self.style.SUCCESS('  [OK] Database cleared (manual method)'))
                                    except Exception as e2:
                                        self.stdout.write(self.style.ERROR(f'  [ERROR] Failed to clear database: {e2}'))
                                        raise
                                
                                # Run migrations before loading data
                                self.stdout.write('  - Running migrations...')
                                call_command('migrate', verbosity=0)
                                self.stdout.write(self.style.SUCCESS('  [OK] Migrations completed'))
                                
                                import tempfile
                                with tempfile.NamedTemporaryFile(mode='w+b', suffix='.json', delete=False) as json_file:
                                    with backup_zip.open(db_file) as source:
                                        json_file.write(source.read())
                                    json_path = json_file.name
                                
                                # Filter problematic entries before loading
                                try:
                                    with open(json_path, 'r', encoding='utf-8') as f:
                                        json_data = json.load(f)
                                        if isinstance(json_data, list):
                                            original_count = len(json_data)
                                            json_data = self._filter_problematic_entries(json_data)
                                            if len(json_data) < original_count:
                                                # Write filtered data back
                                                with open(json_path, 'w', encoding='utf-8') as f:
                                                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                                except Exception as e:
                                    self.stdout.write(self.style.WARNING(f'  [WARNING] Could not filter JSON: {e}'))
                                
                                try:
                                    self.stdout.write('  - Loading JSON fixture via loaddata...')
                                    call_command('loaddata', json_path, verbosity=0)
                                    self.stdout.write(self.style.SUCCESS('  [OK] JSON data loaded'))
                                finally:
                                    if os.path.exists(json_path):
                                        os.unlink(json_path)
                            else:
                                self.stdout.write(self.style.WARNING(
                                    f'  [WARNING] Database file {db_filename} format not recognized. Skipping.'
                                ))
                    else:
                        self.stdout.write(self.style.WARNING('No database file found in backup'))
            
            def _ensure_accounts():
                try:
                    created = 0
                    for u in preserved_users:
                        if not AppUser.objects.filter(username=u['username']).exists():
                            AppUser.objects.create(
                                username=u.get('username') or '',
                                password=u.get('password') or '',
                                role=u.get('role') or 'Secretary',
                                phone_number=u.get('phone_number') or '',
                                email=u.get('email'),
                                is_active=bool(u.get('is_active')),
                                full_name=u.get('full_name') or ''
                            )
                            created += 1
                    if not AppUser.objects.exists():
                        call_command('create_users')
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'  [OK] Restored {created} account(s)'))
                    else:
                        self.stdout.write('  - Accounts verified')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  [WARNING] Account preservation warning: {e}'))

            _ensure_accounts()
            
            # 2. Restore media files (if present in old format)
            if not options.get('no_media', False):
                media_files = [f for f in file_list if f.startswith('media/')]
                if media_files:
                    self.stdout.write('Restoring media files...')
                    # Use MEDIA_ROOT from settings (not legacy uploads path)
                    media_root = Path(getattr(settings, 'MEDIA_ROOT', Path(settings.BASE_DIR) / 'media'))
                    media_root.mkdir(parents=True, exist_ok=True)
                    
                    # Backup current media files if they exist
                    if media_root.exists() and any(media_root.iterdir()):
                        backup_media = media_root.parent / f'media_backup_{Path(backup_file).stem}'
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
                    
                    self.stdout.write(self.style.SUCCESS(f'  [OK] {media_count} media files restored to {media_root}'))
                else:
                    self.stdout.write(self.style.WARNING('No media files found in backup'))
            
            # 3. Restore .env file (optional, with warning)
            env_files = [f for f in file_list if f == '.env']
            if env_files:
                self.stdout.write(self.style.WARNING(
                    '\n[WARNING]️  Backup contains .env file. Restoring it will overwrite current configuration.'
                ))
                if options.get('force', False) or input('Restore .env file? (yes/no): ').lower() == 'yes':
                    env_path = Path(settings.BASE_DIR.parent) / '.env'
                    if env_path.exists():
                        backup_env = f'{env_path}.backup_{Path(backup_file).stem}'
                        shutil.copy2(env_path, backup_env)
                        self.stdout.write(f'  - Current .env backed up to: {backup_env}')
                    
                    with backup_zip.open('.env') as source:
                        with open(env_path, 'wb') as target:
                            target.write(source.read())
                    self.stdout.write(self.style.SUCCESS('  [OK] .env file restored'))
    
    def _filter_problematic_entries(self, json_data):
        """
        Filter out entries that reference missing ContentTypes or apps.
        This prevents errors when restoring backups from systems with different installed apps.
        """
        from django.apps import apps
        
        # Get list of installed apps
        installed_apps = [app.label for app in apps.get_app_configs()]
        
        filtered_data = []
        skipped_count = 0
        
        for entry in json_data:
            model = entry.get('model', '')
            
            # Skip ContentType entries for apps that aren't installed
            if model == 'contenttypes.contenttype':
                app_label = entry.get('fields', {}).get('app_label', '')
                if app_label not in installed_apps:
                    skipped_count += 1
                    continue
            
            # Skip admin.logentry entries that reference missing ContentTypes
            if model == 'admin.logentry':
                content_type = entry.get('fields', {}).get('content_type', [])
                if isinstance(content_type, list) and len(content_type) >= 2:
                    app_label = content_type[0]
                    # Skip if the app isn't installed (like 'sites')
                    if app_label not in installed_apps:
                        skipped_count += 1
                        continue
            
            # Keep all other entries
            filtered_data.append(entry)
        
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(
                f'  [WARNING] Skipped {skipped_count} entries referencing missing apps or ContentTypes'
            ))
        
        return filtered_data
