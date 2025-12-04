# Generated migration to support decimal quantities for kg products
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0049_stockaddition_spoiled'),
    ]

    operations = [
        # Change Product.stock from Integer to Decimal
        migrations.AlterField(
            model_name='product',
            name='stock',
            field=models.DecimalField(max_digits=10, decimal_places=2, default=0),
        ),
        # Change Sale.quantity from Integer to Decimal
        migrations.AlterField(
            model_name='sale',
            name='quantity',
            field=models.DecimalField(max_digits=10, decimal_places=2, default=0),
        ),
        # Change StockAddition.quantity from Integer to Decimal
        migrations.AlterField(
            model_name='stockaddition',
            name='quantity',
            field=models.DecimalField(max_digits=10, decimal_places=2, default=0),
        ),
        # Change StockAddition.spoiled from Integer to Decimal
        migrations.AlterField(
            model_name='stockaddition',
            name='spoiled',
            field=models.DecimalField(max_digits=10, decimal_places=2, default=0),
        ),
    ]

