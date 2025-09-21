from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_stockaddition_supplier'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='transaction_number',
            field=models.CharField(max_length=32, default=''),
        ),
    ]


