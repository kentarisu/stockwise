from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_add_sms_notification_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='appuser',
            name='allow_google_login',
            field=models.BooleanField(default=False, help_text='Allow this account to sign in via Google OAuth'),
        ),
        migrations.AddField(
            model_name='appuser',
            name='google_email',
            field=models.EmailField(blank=True, help_text='Google account email used for OAuth login', max_length=150, null=True),
        ),
    ]

