from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_appuser_google_fields'),
    ]

    operations = [
        # Field was already removed by 0035_remove_appuser_google_email
        # This migration is kept for migration history consistency
    ]