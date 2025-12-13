from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0040_remove_reportproductsummary_expired_qty'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsnotificationsettings',
            name='pricing_time',
            field=models.CharField(
                max_length=5,
                default='08:00',
                help_text='Time in HH:MM format (24-hour)'
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='smsnotificationsettings',
            name='pricing_frequency_days',
            field=models.IntegerField(
                default=3,
                help_text='Frequency in days for pricing recommendations'
            ),
            preserve_default=True,
        ),
    ]

