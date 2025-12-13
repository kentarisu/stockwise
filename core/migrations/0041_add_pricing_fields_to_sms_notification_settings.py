from django.db import migrations, models


def add_fields_if_not_exists(apps, schema_editor):
    """Add fields only if they don't already exist (for PostgreSQL)"""
    db = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        # Check if columns exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='sms_notification_settings' 
            AND column_name IN ('pricing_time', 'pricing_frequency_days')
        """)
        existing_columns = {row[0] for row in cursor.fetchall()}
        
        # Add pricing_time if it doesn't exist
        if 'pricing_time' not in existing_columns:
            cursor.execute("""
                ALTER TABLE sms_notification_settings 
                ADD COLUMN pricing_time VARCHAR(5) DEFAULT '08:00' NOT NULL
            """)
        
        # Add pricing_frequency_days if it doesn't exist
        if 'pricing_frequency_days' not in existing_columns:
            cursor.execute("""
                ALTER TABLE sms_notification_settings 
                ADD COLUMN pricing_frequency_days INTEGER DEFAULT 3 NOT NULL
            """)
        
        # Add comments
        if 'pricing_time' not in existing_columns:
            cursor.execute("""
                COMMENT ON COLUMN sms_notification_settings.pricing_time IS 'Time in HH:MM format (24-hour)'
            """)
        if 'pricing_frequency_days' not in existing_columns:
            cursor.execute("""
                COMMENT ON COLUMN sms_notification_settings.pricing_frequency_days IS 'Frequency in days for pricing recommendations'
            """)


def reverse_migration(apps, schema_editor):
    """Reverse migration - remove fields if they exist"""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='sms_notification_settings' 
            AND column_name IN ('pricing_time', 'pricing_frequency_days')
        """)
        existing_columns = {row[0] for row in cursor.fetchall()}
        
        if 'pricing_time' in existing_columns:
            cursor.execute("ALTER TABLE sms_notification_settings DROP COLUMN pricing_time")
        if 'pricing_frequency_days' in existing_columns:
            cursor.execute("ALTER TABLE sms_notification_settings DROP COLUMN pricing_frequency_days")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0040_remove_reportproductsummary_expired_qty'),
    ]

    operations = [
        migrations.RunPython(add_fields_if_not_exists, reverse_migration),
    ]

