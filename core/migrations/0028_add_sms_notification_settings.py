# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_add_backup_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='SMSNotificationSettings',
            fields=[
                ('setting_id', models.AutoField(primary_key=True)),
                ('sales_enabled', models.BooleanField(default=True)),
                ('sales_time', models.CharField(default='20:00', help_text='Time in HH:MM format (24-hour)', max_length=5)),
                ('stock_enabled', models.BooleanField(default=True)),
                ('stock_threshold', models.IntegerField(default=10, help_text='Low stock threshold in boxes')),
                ('pricing_enabled', models.BooleanField(default=True)),
                ('pricing_sensitivity', models.CharField(choices=[('conservative', 'Conservative'), ('moderate', 'Moderate'), ('aggressive', 'Aggressive')], default='moderate', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'SMS Notification Settings',
                'verbose_name_plural': 'SMS Notification Settings',
                'db_table': 'sms_notification_settings',
            },
        ),
    ]

