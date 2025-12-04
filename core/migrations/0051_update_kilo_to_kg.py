# Generated migration to update "kilo" to "kg" in quantity_unit field
from django.db import migrations


def update_kilo_to_kg(apps, schema_editor):
    """Update all products with quantity_unit 'kilo' to 'kg'"""
    db_alias = schema_editor.connection.alias
    
    # Use raw SQL for case-insensitive update (works with both SQLite and PostgreSQL)
    with schema_editor.connection.cursor() as cursor:
        # Update products table (case-insensitive)
        cursor.execute(
            "UPDATE products SET quantity_unit = 'kg' WHERE LOWER(quantity_unit) = 'kilo'"
        )
        updated_count = cursor.rowcount
        
        if updated_count > 0:
            print(f"Updated {updated_count} product(s) from 'kilo' to 'kg'")


def reverse_update(apps, schema_editor):
    """Reverse migration: change 'kg' back to 'kilo' (if needed)"""
    # Note: This reverse is intentionally left empty as we don't want to change
    # all 'kg' back to 'kilo' automatically. If you need to reverse, do it manually.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0050_decimal_quantities_for_kg'),
    ]

    operations = [
        migrations.RunPython(update_kilo_to_kg, reverse_update),
    ]

