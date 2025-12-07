"""
Django management command to fix PostgreSQL sequence issues.
This is useful after bulk deletions when sequences get out of sync.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Reset PostgreSQL sequences for all tables to prevent duplicate key errors'

    def add_arguments(self, parser):
        parser.add_argument(
            '--table',
            type=str,
            help='Fix sequence for a specific table (e.g., django_admin_log)',
        )

    def handle(self, *args, **options):
        if 'postgresql' not in settings.DATABASES['default']['ENGINE']:
            self.stdout.write(self.style.WARNING('This command only works with PostgreSQL'))
            return

        specific_table = options.get('table')
        
        with connection.cursor() as cursor:
            if specific_table:
                # Fix sequence for a specific table
                self.fix_sequence(cursor, specific_table)
            else:
                # Fix all sequences
                self.stdout.write(self.style.SUCCESS('Fixing all PostgreSQL sequences...'))
                
                # Common Django tables that might have sequence issues
                tables_to_fix = [
                    'django_admin_log',
                    'django_content_type',
                    'django_session',
                    'auth_user',
                    'auth_group',
                    'auth_permission',
                ]
                
                # Get all core app tables
                cursor.execute("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND (tablename LIKE 'core_%' OR tablename IN ('products', 'sales', 'stock_additions', 'action_logs', 'sms', 'backups', 'pricing_recommendations', 'report_product_summary'))
                    ORDER BY tablename;
                """)
                core_tables = [row[0] for row in cursor.fetchall()]
                tables_to_fix.extend(core_tables)
                
                # Also check for tables without underscores (direct table names)
                cursor.execute("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename NOT LIKE 'pg_%'
                    AND tablename NOT LIKE 'sql_%'
                    AND tablename IN ('products', 'sales', 'stock_additions', 'action_logs', 'sms', 'backups', 'pricing_recommendations', 'report_product_summary');
                """)
                direct_tables = [row[0] for row in cursor.fetchall()]
                tables_to_fix.extend([t for t in direct_tables if t not in tables_to_fix])
                
                # Prioritize fixing the most common problematic tables first
                priority_tables = ['products', 'sales', 'stock_additions', 'action_logs']
                for priority_table in priority_tables:
                    if priority_table in tables_to_fix:
                        tables_to_fix.remove(priority_table)
                        tables_to_fix.insert(0, priority_table)
                
                for table in tables_to_fix:
                    self.fix_sequence(cursor, table)
                
                # Fix django_admin_log specifically (most common issue)
                self.stdout.write(self.style.SUCCESS('\n✓ Fixing django_admin_log sequence (common issue)...'))
                self.fix_sequence(cursor, 'django_admin_log')
        
        self.stdout.write(self.style.SUCCESS('\n✓ All sequences fixed!'))

    def fix_sequence(self, cursor, table_name):
        """Fix the sequence for a specific table"""
        try:
            # Get the primary key column name
            cursor.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass
                AND i.indisprimary;
            """, [table_name])
            
            pk_result = cursor.fetchone()
            if not pk_result:
                self.stdout.write(self.style.WARNING(f'  ⚠ No primary key found for {table_name}, skipping...'))
                return
            
            pk_column = pk_result[0]
            
            # Try multiple possible sequence names
            possible_sequence_names = [
                f"{table_name}_{pk_column}_seq",
                f"{table_name}_id_seq",
                f"{pk_column}_seq"
            ]
            
            sequence_name = None
            for seq_name in possible_sequence_names:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_class WHERE relname = %s
                    );
                """, [seq_name])
                if cursor.fetchone()[0]:
                    sequence_name = seq_name
                    break
            
            if not sequence_name:
                self.stdout.write(self.style.WARNING(f'  ⚠ Sequence not found for {table_name}, skipping...'))
                return
            
            # Get current max ID
            cursor.execute(f'SELECT COALESCE(MAX({pk_column}), 0) FROM {table_name};')
            max_id = cursor.fetchone()[0] or 0
            
            # Reset sequence to max_id + 1 (use false to set it to the exact value)
            # We use max_id + 1 so the next insert will use max_id + 1
            cursor.execute("SELECT setval(%s, %s, false);", [sequence_name, max_id + 1])
            
            # Verify
            cursor.execute(f"SELECT last_value FROM {sequence_name};")
            last_value = cursor.fetchone()[0]
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'  ✓ Fixed {table_name}.{pk_column}: sequence "{sequence_name}" set to {last_value} (max ID was {max_id})'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ✗ Error fixing {table_name}: {str(e)}')
            )

