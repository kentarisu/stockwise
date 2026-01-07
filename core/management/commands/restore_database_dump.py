"""
Django management command to restore from a database dump file.
Simple restore: just load the dump file back to the database.
Works with pg_dump, mysqldump, or SQLite files.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import os
import subprocess
import zipfile
import tempfile


class Command(BaseCommand):
    help = 'Restore database from a dump file (simple dump restore)'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Path to the backup dump file (.sql, .sqlite3, or .zip)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force restore without confirmation prompts',
        )

    def handle(self, *args, **options):
        backup_file = Path(options['backup_file'])
        
        if not backup_file.exists():
            raise Exception(f'Backup file not found: {backup_file}')
        
        if not options['force']:
            self.stdout.write(self.style.WARNING(
                '\n[WARNING] This will replace your current database!\n'
                'All current data will be replaced with data from the backup.\n'
            ))
            confirm = input('Are you sure you want to continue? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.SUCCESS('Restore cancelled.'))
                return
        
        self.stdout.write(self.style.SUCCESS(f'Starting restore from: {backup_file}'))
        
        try:
            # Extract dump file if it's a ZIP
            if backup_file.suffix == '.zip':
                dump_file = self._extract_dump_from_zip(backup_file)
            else:
                dump_file = backup_file
            
            # Restore based on database type
            db_engine = settings.DATABASES['default']['ENGINE'].lower()
            
            if 'postgresql' in db_engine or 'postgres' in db_engine:
                self._restore_postgresql(dump_file)
            elif 'mysql' in db_engine:
                self._restore_mysql(dump_file)
            elif 'sqlite' in db_engine:
                self._restore_sqlite(dump_file)
            else:
                raise Exception(f'Unsupported database engine: {db_engine}')
            
            # Fix sequences after restore (for PostgreSQL)
            if 'postgresql' in db_engine:
                try:
                    from django.core.management import call_command
                    call_command('fix_sequences', verbosity=0)
                    self.stdout.write(self.style.SUCCESS('  [OK] Sequences fixed'))
                except Exception:
                    pass
            
            self.stdout.write(self.style.SUCCESS('\n[OK] Database restored successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during restore: {str(e)}'))
            raise
        finally:
            # Clean up extracted temp file if it was from ZIP
            if 'temp_dump_file' in locals() and temp_dump_file.exists():
                try:
                    temp_dump_file.unlink()
                except Exception:
                    pass
    
    def _extract_dump_from_zip(self, zip_file):
        """Extract database dump file from ZIP"""
        with zipfile.ZipFile(zip_file, 'r') as backup_zip:
            file_list = backup_zip.namelist()
            
            # Look for database dump file
            dump_files = [
                f for f in file_list 
                if ('database' in f.lower() or f.endswith('.sql') or f.endswith('.sqlite3') or f.endswith('.db'))
                and not f.endswith('/')
            ]
            
            if not dump_files:
                raise Exception('No database dump file found in ZIP')
            
            dump_file_in_zip = dump_files[0]
            
            # Extract to temp file
            temp_dump = tempfile.NamedTemporaryFile(
                mode='wb', 
                delete=False,
                suffix=Path(dump_file_in_zip).suffix
            )
            temp_dump.write(backup_zip.read(dump_file_in_zip))
            temp_dump.close()
            
            self.stdout.write(f'  - Extracted dump file: {dump_file_in_zip}')
            return Path(temp_dump.name)
    
    def _restore_postgresql(self, dump_file):
        """Restore PostgreSQL dump"""
        db_config = settings.DATABASES['default']
        db_name = db_config['NAME']
        db_user = db_config.get('USER', '')
        db_host = db_config.get('HOST', 'localhost')
        db_port = db_config.get('PORT', '5432')
        db_pass = db_config.get('PASSWORD', '')
        
        self.stdout.write('  - Restoring PostgreSQL database...')
        
        # Check if it's custom format (binary) or plain SQL
        is_custom_format = dump_file.suffix == '.sql' and dump_file.stat().st_size > 0
        # Try to detect: custom format files are usually smaller and binary
        
        if dump_file.suffix == '.sql' and self._is_binary_file(dump_file):
            # Custom format (binary)
            cmd = ['pg_restore']
            if db_host:
                cmd.extend(['-h', db_host])
            if db_port:
                cmd.extend(['-p', str(db_port)])
            if db_user:
                cmd.extend(['-U', db_user])
            cmd.extend(['-d', db_name, '--clean', '--if-exists', str(dump_file)])
        else:
            # Plain SQL format
            cmd = ['psql']
            if db_host:
                cmd.extend(['-h', db_host])
            if db_port:
                cmd.extend(['-p', str(db_port)])
            if db_user:
                cmd.extend(['-U', db_user])
            cmd.extend(['-d', db_name, '-f', str(dump_file)])
        
        env = os.environ.copy()
        if db_pass:
            env['PGPASSWORD'] = db_pass
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            self.stdout.write(self.style.SUCCESS('  [OK] PostgreSQL database restored'))
        except subprocess.CalledProcessError as e:
            raise Exception(f'PostgreSQL restore failed: {e.stderr or e.stdout}')
        except FileNotFoundError:
            raise Exception('PostgreSQL client tools (psql/pg_restore) not found. Please install them.')
    
    def _restore_mysql(self, dump_file):
        """Restore MySQL dump"""
        db_config = settings.DATABASES['default']
        db_name = db_config['NAME']
        db_user = db_config.get('USER', '')
        db_host = db_config.get('HOST', 'localhost')
        db_port = db_config.get('PORT', '3306')
        db_pass = db_config.get('PASSWORD', '')
        
        self.stdout.write('  - Restoring MySQL database...')
        
        cmd = ['mysql']
        if db_user:
            cmd.extend(['-u', db_user])
        if db_pass:
            cmd.extend([f'-p{db_pass}'])
        if db_host:
            cmd.extend(['-h', db_host])
        if db_port:
            cmd.extend(['-P', str(db_port)])
        cmd.append(db_name)
        
        try:
            with open(dump_file, 'r', encoding='utf-8') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True, check=True)
            self.stdout.write(self.style.SUCCESS('  [OK] MySQL database restored'))
        except subprocess.CalledProcessError as e:
            raise Exception(f'MySQL restore failed: {e.stderr}')
        except FileNotFoundError:
            raise Exception('MySQL client (mysql) not found. Please install it.')
    
    def _restore_sqlite(self, dump_file):
        """Restore SQLite by replacing the database file"""
        db_config = settings.DATABASES['default']
        db_name = db_config['NAME']
        
        if isinstance(db_name, Path):
            db_path = db_name
        else:
            db_path = Path(db_name)
        
        self.stdout.write('  - Restoring SQLite database...')
        
        # Close all database connections first
        from django.db import connections
        connections.close_all()
        
        # Backup current database
        if db_path.exists():
            backup_path = db_path.parent / f'{db_path.name}.backup_{dump_file.stem}'
            import shutil
            shutil.copy2(db_path, backup_path)
            self.stdout.write(f'  - Current database backed up to: {backup_path}')
        
        # Copy dump file to database location
        import shutil
        shutil.copy2(dump_file, db_path)
        
        self.stdout.write(self.style.SUCCESS('  [OK] SQLite database restored'))
    
    def _is_binary_file(self, file_path):
        """Check if file is binary (custom pg_dump format)"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(512)
                # Custom format starts with specific header
                return chunk.startswith(b'PGDMP') or b'\x00' in chunk
        except Exception:
            return False

