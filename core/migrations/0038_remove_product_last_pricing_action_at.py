from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_remove_stockaddition_expiry_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='last_pricing_action_at',
        ),
    ]