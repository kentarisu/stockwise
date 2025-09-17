from django.db import models
from django.utils import timezone


class Product(models.Model):
	STATUS_CHOICES = (
		('active', 'active'),
		('discontinued', 'discontinued'),
	)

	product_id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=50)
	variant = models.CharField(max_length=50, null=True, blank=True)
	status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='active')
	image = models.CharField(max_length=100, null=True, blank=True)
	date_added = models.DateField(default=timezone.now)
	price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	size = models.CharField(max_length=50)
	low_stock_threshold = models.IntegerField(default=10)
	stock = models.IntegerField(default=0)
	is_built_in = models.BooleanField(default=False)  # Distinguishes built-in products from inventory products
	supplier = models.CharField(max_length=100, null=True, blank=True)
	qr_code = models.BinaryField(default=b'')  # VARBINARY(MAX)
	created_at = models.DateTimeField(default=timezone.now)
	last_updated = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'products'

	def __str__(self) -> str:
		return self.name


# Removed Inventory per 6-table schema


# Stock additions table remains unchanged
class StockAddition(models.Model):
	addition_id = models.AutoField(primary_key=True)
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	quantity = models.IntegerField(default=0)
	date_added = models.DateTimeField(default=timezone.now)
	created_at = models.DateTimeField(auto_now_add=True)
	remaining_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	batch_id = models.CharField(max_length=20)
	supplier = models.CharField(max_length=100, null=True, blank=True)

	class Meta:
		db_table = 'stock_additions'
		indexes = [
			models.Index(fields=['product', 'date_added'], name='idx_sa_product_date'),
			models.Index(fields=['batch_id'], name='idx_sa_batch'),
		]


class AppUser(models.Model):
	ROLE_CHOICES = (
		('Admin', 'Admin'),
		('Secretary', 'Secretary'),
	)

	user_id = models.AutoField(primary_key=True)
	username = models.CharField(max_length=25)
	password = models.CharField(max_length=255)
	phone_number = models.CharField(max_length=15)
	role = models.CharField(max_length=9, choices=ROLE_CHOICES, default='Secretary')
	profile_picture = models.CharField(max_length=100, null=True, blank=True)

	class Meta:
		db_table = 'users'

	def __str__(self) -> str:
		return self.username


class Sale(models.Model):
	STATUS_CHOICES = (
		('completed', 'completed'),
		('voided', 'voided'),
	)

	sale_id = models.AutoField(primary_key=True)
	product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
	quantity = models.IntegerField(default=0)
	price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	or_number = models.CharField(max_length=32, default='')
	customer_name = models.CharField(max_length=50, default='')
	address = models.CharField(max_length=50, default='')
	contact_number = models.IntegerField(default=0)
	recorded_at = models.DateTimeField(default=timezone.now)
	total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	change_given = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='completed')
	user = models.ForeignKey(AppUser, on_delete=models.PROTECT, null=True, blank=True)
	voided_at = models.DateTimeField(null=True, blank=True)
	stock_restored = models.BooleanField(default=False)

	class Meta:
		db_table = 'sales'


# Removed SaleItem per single-table sales schema


# Removed ReceiptPrint per 6-table schema


class SMS(models.Model):
	sms_id = models.AutoField(primary_key=True)
	product = models.ForeignKey(Product, on_delete=models.CASCADE, unique=True)
	user = models.ForeignKey(AppUser, on_delete=models.CASCADE, unique=True)
	MESSAGE_TYPE_CHOICES = (
		('sales_summary_daily', 'sales_summary_daily'),
		('sales_summary_weekly', 'sales_summary_weekly'),
		('stock_alert', 'stock_alert'),
		('pricing_alert', 'pricing_alert'),
	)
	demand_level_choices = (
		('high', 'high'),
		('mid', 'mid'),
		('low', 'low'),
	)
	message_type = models.CharField(max_length=32, choices=MESSAGE_TYPE_CHOICES)
	demand_level = models.CharField(max_length=4, choices=demand_level_choices)
	message_content = models.TextField()
	sent_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'sms'
		verbose_name = 'SMS'
		verbose_name_plural = 'SMS'

	def __str__(self):
		return f"SMS {self.sms_id}"


class ReportProductSummary(models.Model):
	report_id = models.AutoField(primary_key=True)
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	period_start = models.DateTimeField()
	period_end = models.DateTimeField()
	granularity = models.CharField(max_length=10)

	generated_at = models.DateTimeField(auto_now_add=True)
	generated_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, blank=True)
	filters_json = models.JSONField(null=True, blank=True)

	opening_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	added_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	sold_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	expired_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	closing_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	last_addition_at = models.DateTimeField(null=True, blank=True)

	avg_sell_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
	revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	avg_unit_cost = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
	cogs = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	gross_profit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	gross_margin_pct = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

	sell_through_pct = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	avg_daily_sales = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
	days_of_cover_end = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
	low_stock_threshold = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	low_stock_flag = models.BooleanField(default=False)

	sms_low_stock_count = models.IntegerField(default=0)
	sms_expiry_count = models.IntegerField(default=0)
	last_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
	suggested_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
	price_action = models.CharField(max_length=10, null=True, blank=True)
	demand_level = models.CharField(max_length=4, null=True, blank=True)

	first_sale_at = models.DateTimeField(null=True, blank=True)
	last_sale_at = models.DateTimeField(null=True, blank=True)

	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'report_product_summary'
		verbose_name = 'generated reports'
		verbose_name_plural = 'generated reports'
