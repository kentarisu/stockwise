from django.db import models
from types import SimpleNamespace
from django.db import connection
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
	quantity_unit = models.CharField(max_length=50)
	low_stock_threshold = models.IntegerField(default=10)
	stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Supports decimal for kg products
	is_built_in = models.BooleanField(default=False)  # Distinguishes built-in products from inventory products
	supplier = models.CharField(max_length=100, null=True, blank=True)
	qr_code = models.BinaryField(default=b'')  # VARBINARY(MAX)
	sku = models.CharField(max_length=50, unique=True, null=True, blank=True)  # TC-009: SKU with unique constraint
	created_at = models.DateTimeField(default=timezone.now)
	last_updated = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'products'

	def __str__(self) -> str:
		return self.name


# Removed Inventory per 6-table schema


# Stock additions table with expiry tracking
class StockAddition(models.Model):
	addition_id = models.AutoField(primary_key=True)
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Supports decimal for kg products
	date_added = models.DateTimeField(default=timezone.now)
	created_at = models.DateTimeField(auto_now_add=True)
	remaining_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	batch_id = models.CharField(max_length=20)
	supplier = models.CharField(max_length=100, null=True, blank=True)
	spoiled = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Supports decimal for kg products

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
	full_name = models.CharField(max_length=100, null=True, blank=True)
	password = models.CharField(max_length=255)
	phone_number = models.CharField(max_length=15)
	role = models.CharField(max_length=9, choices=ROLE_CHOICES, default='Secretary')
	profile_picture = models.CharField(max_length=100, null=True, blank=True)
	is_active = models.BooleanField(default=True)  # TC-003: User account status
	email = models.EmailField(max_length=100, null=True, blank=True)  # TC-034: Profile email
	created_at = models.DateTimeField(default=timezone.now)
	last_login_at = models.DateTimeField(null=True, blank=True)

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
	product = models.ForeignKey(Product, on_delete=models.PROTECT)
	quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Supports decimal for kg products
	price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	transaction_number = models.CharField(max_length=32, default='')
	or_number = models.CharField(max_length=32, default='')
	customer_name = models.CharField(max_length=50, default='')
	address = models.CharField(max_length=50, default='')
	contact_number = models.CharField(max_length=15, default='')
	recorded_at = models.DateTimeField(default=timezone.localtime)
	total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	change_given = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	discount_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=0)
	discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='completed')
	user = models.ForeignKey(AppUser, on_delete=models.PROTECT)
	voided_at = models.DateTimeField(null=True, blank=True)
	void_reason = models.CharField(max_length=255, null=True, blank=True)
	stock_restored = models.BooleanField(default=False)

	class Meta:
		db_table = 'sales'


# Removed SaleItem per single-table sales schema


# Removed ReceiptPrint per 6-table schema


class SMS(models.Model):
	sms_id = models.AutoField(primary_key=True)
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
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


class SMSNotificationSettings(models.Model):
	"""Store SMS notification settings for the system"""
	setting_id = models.AutoField(primary_key=True)
	# Sales notification settings
	sales_enabled = models.BooleanField(default=True)
	sales_time = models.CharField(max_length=5, default='20:00', help_text='Time in HH:MM format (24-hour)')
	# Stock notification settings
	stock_enabled = models.BooleanField(default=True)
	stock_threshold = models.IntegerField(default=10, help_text='Low stock threshold in boxes')
	# Pricing notification settings
	pricing_enabled = models.BooleanField(default=True)
	pricing_sensitivity = models.CharField(max_length=20, default='moderate', choices=[
		('conservative', 'Conservative'),
		('moderate', 'Moderate'),
		('aggressive', 'Aggressive'),
	])
	pricing_time = models.CharField(max_length=5, default='08:00')
	pricing_frequency_days = models.IntegerField(default=3)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'sms_notification_settings'
		verbose_name = 'SMS Notification Settings'
		verbose_name_plural = 'SMS Notification Settings'

	def __str__(self):
		return f"SMS Settings (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')} )"

	@classmethod
	def get_settings(cls):
		"""Get or create the singleton settings instance with schema preflight"""
		try:
			with connection.cursor() as cursor:
				tables = connection.introspection.table_names()
				if cls._meta.db_table not in tables:
					raise RuntimeError('settings table missing')
				cols = [c.name for c in connection.introspection.get_table_description(cursor, cls._meta.db_table)]
			required = {
				'sales_enabled','sales_time','stock_enabled','stock_threshold',
				'pricing_enabled','pricing_sensitivity','pricing_time','pricing_frequency_days'
			}
			if not required.issubset(set(cols)):
				raise RuntimeError('settings columns missing')
		except Exception:
			return SimpleNamespace(
				sales_enabled=True,
				sales_time='20:00',
				stock_enabled=True,
				stock_threshold=10,
				pricing_enabled=True,
				pricing_sensitivity='moderate',
				pricing_time='08:00',
				pricing_frequency_days=3,
			)
		settings, _ = cls.objects.get_or_create(
			setting_id=1,
			defaults={
				'sales_enabled': True,
				'sales_time': '20:00',
				'stock_enabled': True,
				'stock_threshold': 10,
				'pricing_enabled': True,
				'pricing_sensitivity': 'moderate',
				'pricing_time': '08:00',
				'pricing_frequency_days': 3,
			}
		)
		return settings


class ReportProductSummary(models.Model):
	report_id = models.AutoField(primary_key=True)
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	period_start = models.DateTimeField()
	period_end = models.DateTimeField()
	granularity = models.CharField(max_length=10)

	generated_at = models.DateTimeField(auto_now_add=True)
	generated_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, blank=True)

	opening_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	added_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	sold_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
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
	accepted_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
	price_action = models.CharField(max_length=10, null=True, blank=True)
	demand_level = models.CharField(max_length=4, null=True, blank=True)

	first_sale_at = models.DateTimeField(null=True, blank=True)
	last_sale_at = models.DateTimeField(null=True, blank=True)

	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'report_product_summary'
		verbose_name = 'generated reports'
		verbose_name_plural = 'generated reports'


class ActionLog(models.Model):
    action_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(AppUser, null=True, blank=True, on_delete=models.SET_NULL)
    role = models.CharField(max_length=20, blank=True)
    action = models.CharField(max_length=150)
    details = models.TextField(blank=True)
    ip_address = models.CharField(max_length=45, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'action_logs'
        ordering = ('-created_at',)

    def __str__(self):
        base = self.action
        if self.user:
            base = f"{self.user.username}: {base}"
        return f"{base} @ {self.created_at:%Y-%m-%d %H:%M:%S}"


class PricingRecommendation(models.Model):
    """Store pricing recommendations with 3-day expiration"""
    recommendation_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    suggested_price = models.DecimalField(max_digits=10, decimal_places=2)
    change_pct = models.DecimalField(max_digits=6, decimal_places=2)
    action = models.CharField(max_length=10)  # INCREASE, DECREASE, HOLD
    reason = models.TextField()
    elasticity = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    r2 = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    confidence = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # 3 days from creation

    class Meta:
        db_table = 'pricing_recommendations'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['product', 'expires_at'], name='idx_pr_product_expires'),
            models.Index(fields=['expires_at'], name='idx_pr_expires'),
        ]

    def __str__(self):
        return f"{self.product.name}: {self.action} to {self.suggested_price}"

    def is_expired(self):
        """Check if recommendation has expired (older than 3 days)"""
        from django.utils import timezone
        return timezone.now() > self.expires_at


class Backup(models.Model):
    """Track system backups"""
    backup_id = models.AutoField(primary_key=True)
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField(help_text='File size in bytes')
    backup_type = models.CharField(max_length=20, default='full', choices=[
        ('full', 'Full Backup'),
        ('database', 'Database Only'),
        ('media', 'Media Only'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    is_verified = models.BooleanField(default=False, help_text='Whether backup file still exists and is valid')

    class Meta:
        db_table = 'backups'
        ordering = ['-created_at']
        verbose_name = 'Backup'
        verbose_name_plural = 'Backups'

    def __str__(self):
        return f"{self.filename} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    def get_file_size_mb(self):
        """Return file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)

    def verify_file_exists(self):
        """Check if backup file still exists"""
        from pathlib import Path
        exists = Path(self.file_path).exists()
        if exists != self.is_verified:
            self.is_verified = exists
            self.save(update_fields=['is_verified'])
        return exists
