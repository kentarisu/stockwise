"""
Django management command to incrementally restore from a backup.
Only restores missing data, preserving existing records.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
from pathlib import Path
import zipfile
import json
import sys
from django.apps import apps
from django.db import models, transaction, connection


class Command(BaseCommand):
    help = 'Incrementally restore from a backup - only adds missing data'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Path to the backup JSON file to restore from',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force restore without confirmation prompts',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be restored without actually restoring',
        )

    def handle(self, *args, **options):
        backup_file = Path(options['backup_file'])
        
        if not backup_file.exists():
            error_msg = f'Backup file not found: {backup_file}'
            self.stdout.write(self.style.ERROR(error_msg))
            raise Exception(error_msg)
        
        if backup_file.suffix not in ['.json', '.zip']:
            error_msg = 'Backup file must be a .json or .zip file'
            self.stdout.write(self.style.ERROR(error_msg))
            raise Exception(error_msg)
        
        if not options['force']:
            self.stdout.write(self.style.WARNING(
                '\n[INFO] Incremental Restore Mode\n'
                'This will only restore missing data from the backup.\n'
                'Existing records will be preserved.\n'
            ))
            confirm = input('Continue? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.SUCCESS('Restore cancelled.'))
                return
        
        self.stdout.write(self.style.SUCCESS(f'Starting incremental restore from: {backup_file}'))
        
        try:
            # Extract JSON data
            if backup_file.suffix == '.json':
                json_data = self._load_json(backup_file)
            else:
                json_data = self._extract_json_from_zip(backup_file)
            
            if not json_data:
                self.stdout.write(self.style.ERROR('No data found in backup file'))
                return
            
            # Filter problematic entries
            json_data = self._filter_problematic_entries(json_data)
            
            # Group data by model
            data_by_model = self._group_by_model(json_data)
            
            # Restore incrementally
            stats = {
                'total': len(json_data),
                'restored': 0,
                'skipped': 0,
                'errors': 0
            }
            
            # Use database transaction for hosting environments (PostgreSQL, etc.)
            # This ensures atomicity and better error handling
            is_postgresql = 'postgresql' in settings.DATABASES['default']['ENGINE'].lower()
            
            if is_postgresql:
                self.stdout.write('  - Using PostgreSQL transaction mode for safe restore')
            
            try:
                # Process each model within a transaction
                for model_name, records in data_by_model.items():
                    if is_postgresql:
                        # Use atomic transaction for PostgreSQL
                        with transaction.atomic():
                            model_stats = self._restore_model_incremental(model_name, records, options.get('dry_run', False))
                            stats['restored'] += model_stats['restored']
                            stats['skipped'] += model_stats['skipped']
                            stats['errors'] += model_stats['errors']
                    else:
                        # SQLite handles transactions differently
                        model_stats = self._restore_model_incremental(model_name, records, options.get('dry_run', False))
                        stats['restored'] += model_stats['restored']
                        stats['skipped'] += model_stats['skipped']
                        stats['errors'] += model_stats['errors']
            except Exception as e:
                if is_postgresql:
                    self.stdout.write(self.style.ERROR(f'  [ERROR] Transaction rolled back due to error: {e}'))
                raise
            
            # Fix sequences after restore (important for PostgreSQL in hosting environments)
            if not options.get('dry_run', False):
                try:
                    if 'postgresql' in settings.DATABASES['default']['ENGINE'].lower():
                        self.stdout.write('  - Fixing PostgreSQL sequences...')
                        call_command('fix_sequences', verbosity=0)
                        self.stdout.write(self.style.SUCCESS('  [OK] Sequences fixed'))
                except Exception as seq_error:
                    # Log but don't fail if sequence fix fails
                    self.stdout.write(self.style.WARNING(f'  [WARNING] Could not fix sequences: {seq_error}'))
            
            # Summary
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('Incremental Restore Summary:'))
            self.stdout.write(f'  Total records in backup: {stats["total"]}')
            if options.get('dry_run', False):
                self.stdout.write(self.style.WARNING('  DRY RUN MODE - No changes made'))
            else:
                if stats["restored"] == stats["total"]:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ All {stats["restored"]} records were missing and have been restored'))
                elif stats["restored"] > 0:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Restored {stats["restored"]} missing record(s)'))
                else:
                    self.stdout.write('  No records restored')
            if stats["skipped"] > 0:
                self.stdout.write(f'  → Skipped {stats["skipped"]} record(s) (already exist)')
            if stats['errors'] > 0:
                self.stdout.write(self.style.ERROR(f'  ✗ Errors: {stats["errors"]}'))
            self.stdout.write('='*60)
            
        except Exception as e:
            error_msg = f'Error during incremental restore: {str(e)}'
            self.stdout.write(self.style.ERROR(error_msg))
            import traceback
            traceback.print_exc()
            raise
    
    def _load_json(self, backup_file):
        """Load JSON data from file"""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON file: {e}'))
            raise
    
    def _extract_json_from_zip(self, backup_file):
        """Extract JSON data from ZIP file"""
        with zipfile.ZipFile(backup_file, 'r') as backup_zip:
            file_list = backup_zip.namelist()
            
            # Look for JSON file in database/ folder or root
            json_files = [
                f for f in file_list 
                if f.endswith('.json') and not f.startswith('media/')
            ]
            
            if not json_files:
                self.stdout.write(self.style.ERROR('No JSON file found in ZIP'))
                return []
            
            # Prefer database/stockwise_dump.json
            json_file = None
            for f in json_files:
                if 'database' in f.lower() or 'stockwise' in f.lower():
                    json_file = f
                    break
            
            if not json_file:
                json_file = json_files[0]
            
            self.stdout.write(f'  - Extracting JSON from: {json_file}')
            
            with backup_zip.open(json_file) as f:
                return json.load(f)
    
    def _filter_problematic_entries(self, json_data):
        """Filter out entries that reference missing ContentTypes or apps"""
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
                    if app_label not in installed_apps:
                        skipped_count += 1
                        continue
            
            filtered_data.append(entry)
        
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(
                f'  [WARNING] Filtered out {skipped_count} problematic entries'
            ))
        
        return filtered_data
    
    def _group_by_model(self, json_data):
        """Group JSON records by model name"""
        data_by_model = {}
        for entry in json_data:
            model_name = entry.get('model', '')
            if model_name not in data_by_model:
                data_by_model[model_name] = []
            data_by_model[model_name].append(entry)
        return data_by_model
    
    def _restore_model_incremental(self, model_name, records, dry_run=False):
        """Restore records for a specific model, skipping existing ones"""
        stats = {'restored': 0, 'skipped': 0, 'errors': 0}
        
        try:
            # Get the model class
            app_label, model_label = model_name.split('.')
            model_class = apps.get_model(app_label, model_label)
            
            if not model_class:
                self.stdout.write(self.style.WARNING(f'  [WARNING] Model {model_name} not found, skipping'))
                stats['errors'] = len(records)
                return stats
            
            # Get primary key field name
            pk_field = model_class._meta.pk.name
            
            self.stdout.write(f'\n  Processing {model_name} ({len(records)} records)...')
            
            # Get existing primary keys
            # Use iterator() for large datasets to avoid memory issues in hosting
            existing_pks = set()
            try:
                # For large tables, use iterator to avoid loading all into memory
                pk_queryset = model_class.objects.values_list(pk_field, flat=True)
                # Check if we should use iterator (for tables with many records)
                try:
                    count = model_class.objects.count()
                    if count > 10000:
                        # Use iterator for large tables
                        existing_pks = set(pk_queryset.iterator())
                    else:
                        # Use list for smaller tables (faster)
                        existing_pks = set(pk_queryset)
                except Exception:
                    # Fallback: use iterator
                    existing_pks = set(pk_queryset.iterator())
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'    [WARNING] Could not check existing records: {e}'))
            
            # Filter records to only include missing ones
            # This ensures: if all data is missing → restore all, if only 1 is missing → restore only that 1
            records_to_restore = []
            for record in records:
                pk_value = record.get('pk')
                if pk_value is None:
                    # Try to get PK from fields
                    fields = record.get('fields', {})
                    pk_value = fields.get(pk_field)
                
                if pk_value is None:
                    # No primary key, will try to create (might fail)
                    records_to_restore.append(record)
                elif pk_value not in existing_pks:
                    # Missing record - add to restore list
                    records_to_restore.append(record)
                else:
                    # Already exists - skip this one
                    stats['skipped'] += 1
            
            if not records_to_restore:
                self.stdout.write(f'    ✓ All {len(records)} records already exist, nothing to restore')
                return stats
            
            # Show what will be restored
            if len(records_to_restore) == len(records):
                self.stdout.write(f'    → All {len(records_to_restore)} records are missing, will restore all')
            else:
                self.stdout.write(f'    → Found {len(records_to_restore)} missing records (out of {len(records)} total), will restore only missing ones')
            
            if dry_run:
                self.stdout.write(self.style.WARNING(f'    [DRY RUN] Would restore {len(records_to_restore)} records'))
                stats['restored'] = len(records_to_restore)
                return stats
            
            # Restore missing records in batches for better performance in hosting
            restored_count = 0
            batch_size = 100  # Process in batches to avoid memory/timeout issues
            
            # Close connection before batch processing to avoid stale connections
            from django.db import connections
            connections.close_all()
            
            for i in range(0, len(records_to_restore), batch_size):
                batch = records_to_restore[i:i + batch_size]
                for record in batch:
                    try:
                        self._create_record(model_class, record)
                        restored_count += 1
                    except Exception as e:
                        stats['errors'] += 1
                        self.stdout.write(self.style.WARNING(
                            f'    [WARNING] Could not restore record pk={record.get("pk")}: {e}'
                        ))
                
                # Refresh connection periodically for long-running operations
                if (i + batch_size) % 500 == 0:
                    connections.close_all()
            
            stats['restored'] = restored_count
            self.stdout.write(self.style.SUCCESS(f'    Restored {restored_count} records'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [ERROR] Error processing {model_name}: {e}'))
            stats['errors'] = len(records)
            import traceback
            traceback.print_exc()
        
        return stats
    
    def _create_record(self, model_class, record):
        """Create a single record from JSON entry"""
        fields = record.get('fields', {})
        pk_value = record.get('pk')
        
        # Handle foreign keys and many-to-many fields
        processed_fields = {}
        m2m_fields = {}
        
        for field_name, field_value in fields.items():
            field = model_class._meta.get_field(field_name)
            
            if isinstance(field, models.ForeignKey):
                # Foreign key: resolve the referenced object
                if field_value:
                    if isinstance(field_value, list):
                        # Django serializes FKs as [app_label, model_name, pk]
                        if len(field_value) >= 3:
                            ref_app, ref_model, ref_pk = field_value[0], field_value[1], field_value[2]
                            ref_model_class = apps.get_model(ref_app, ref_model)
                            if ref_model_class:
                                try:
                                    ref_obj = ref_model_class.objects.get(pk=ref_pk)
                                    processed_fields[field_name] = ref_obj
                                except ref_model_class.DoesNotExist:
                                    # Referenced object doesn't exist, skip this field
                                    processed_fields[field_name] = None
                            else:
                                processed_fields[field_name] = None
                        else:
                            processed_fields[field_name] = None
                    else:
                        # Direct PK value
                        try:
                            ref_obj = field.related_model.objects.get(pk=field_value)
                            processed_fields[field_name] = ref_obj
                        except field.related_model.DoesNotExist:
                            processed_fields[field_name] = None
                else:
                    processed_fields[field_name] = None
            
            elif isinstance(field, models.ManyToManyField):
                # Many-to-many: store for later
                m2m_fields[field_name] = field_value
            
            else:
                # Regular field
                processed_fields[field_name] = field_value
        
        # Create the object
        # Note: We've already filtered out existing records, so this should always create new ones
        if pk_value:
            # Try to create with specific PK
            # Use get_or_create as safety check (should always create since we filtered)
            obj, created = model_class.objects.get_or_create(
                pk=pk_value,
                defaults=processed_fields
            )
            if not created:
                # This shouldn't happen since we filtered, but handle it gracefully
                raise Exception(f'Record with pk={pk_value} already exists (unexpected)')
        else:
            # Create without PK (will auto-generate)
            obj = model_class.objects.create(**processed_fields)
        
        # Handle many-to-many relationships
        for field_name, m2m_values in m2m_fields.items():
            if m2m_values:
                m2m_field = model_class._meta.get_field(field_name)
                related_objects = []
                
                for m2m_value in m2m_values:
                    if isinstance(m2m_value, list) and len(m2m_value) >= 3:
                        # Django format: [app_label, model_name, pk]
                        ref_app, ref_model, ref_pk = m2m_value[0], m2m_value[1], m2m_value[2]
                        ref_model_class = apps.get_model(ref_app, ref_model)
                        if ref_model_class:
                            try:
                                ref_obj = ref_model_class.objects.get(pk=ref_pk)
                                related_objects.append(ref_obj)
                            except ref_model_class.DoesNotExist:
                                pass
                
                if related_objects:
                    getattr(obj, field_name).set(related_objects)
        
        return obj

