from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0042_remove_reportproductsummary_filters_json'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='discount_pct',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='sale',
            name='discount_amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10, null=True),
        ),
    ]
