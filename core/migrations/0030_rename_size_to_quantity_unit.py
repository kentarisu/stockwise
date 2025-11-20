# Generated migration to rename size field to quantity_unit
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_appuser_google_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='size',
            new_name='quantity_unit',
        ),
    ]

