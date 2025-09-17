from django.db import models


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    variant = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20)
    date_added = models.DateField()
    image = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    size = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'products'
        managed = False


class Inventory(models.Model):
    inventory_id = models.AutoField(primary_key=True)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, db_column='product_id')
    stock = models.IntegerField(default=0)
    last_updated = models.DateTimeField()

    class Meta:
        db_table = 'inventory'
        managed = False


class StockAddition(models.Model):
    addition_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id')
    batch_id = models.CharField(max_length=64)
    quantity = models.IntegerField()
    date_added = models.DateField()
    remaining_quantity = models.IntegerField()
    created_at = models.DateTimeField()
    supplier = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'stock_additions'
        managed = False

# Create your models here.
