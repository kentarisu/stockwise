from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0034_appuser_created_at_appuser_last_login_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='appuser',
            name='google_email',
        ),
    ]