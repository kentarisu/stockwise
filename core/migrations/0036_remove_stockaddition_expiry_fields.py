from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_remove_appuser_google_email'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='stockaddition',
            name='idx_sa_expiry',
        ),
        migrations.RemoveField(
            model_name='stockaddition',
            name='manufacturing_date',
        ),
        migrations.RemoveField(
            model_name='stockaddition',
            name='expiry_date',
        ),
    ]