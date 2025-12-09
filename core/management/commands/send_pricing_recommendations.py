from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Sale, AppUser, Product, SMSNotificationSettings, SMS
from core.pricing_ai import DemandPricingAI, PolicyConfig
import pandas as pd


class Command(BaseCommand):
    help = 'Send demand-driven pricing recommendations to admin users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Send test pricing recommendation instead of real data',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze for pricing recommendations (default: 30)',
        )

    def handle(self, *args, **options):
        if options['test']:
            self.send_test_pricing_recommendation()
        else:
            self.send_pricing_recommendations(days=options['days'])

    def send_test_pricing_recommendation(self):
        """Send a test pricing recommendation"""
        admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
        if not admins.exists():
            self.stdout.write(self.style.WARNING('No admin phone numbers configured.'))
            return
        
        message = "STOCKWISE Pricing Recommendation\n\nTest Alert: This is a test pricing notification."
        
        for u in admins:
            if self.send_sms(u.phone_number, message):
                self.stdout.write(self.style.SUCCESS(f'Test pricing recommendation sent to {u.username} at {u.phone_number}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send test pricing recommendation to {u.username} at {u.phone_number}'))

    def send_pricing_recommendations(self, days=30):
        """Send pricing recommendations based on real sales data"""
        settings = SMSNotificationSettings.get_settings()
        if not settings.pricing_enabled:
            self.stdout.write(self.style.WARNING('Pricing SMS notifications are disabled in settings.'))
            return
        now = timezone.localtime()
        try:
            phh, pmm = [int(x) for x in str(getattr(settings, 'pricing_time', '08:00')).split(':')]
        except Exception:
            phh, pmm = 8, 0
        scheduled_dt = now.replace(hour=phh, minute=pmm, second=0, microsecond=0)
        if now < scheduled_dt:
            self.stdout.write(self.style.WARNING(f'Not yet time for pricing recommendations (scheduled at {getattr(settings, "pricing_time", "08:00")}).'))
            return
        # Cooldown check removed - pricing recommendations will send at scheduled time regardless of last send time
        admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
        if not admins.exists():
            self.stdout.write(self.style.WARNING('No admin phone numbers configured.'))
            return

        try:
            # Get sales data for the specified period
            end_date = timezone.now()
            start_date = end_date - timezone.timedelta(days=days)
            
            sales = Sale.objects.filter(
                recorded_at__gte=start_date,
                recorded_at__lte=end_date,
                status='completed'
            ).select_related('product')

            if not sales.exists():
                self.stdout.write(self.style.WARNING(f'No sales data found for the last {days} days.'))
                return

            # Convert to DataFrame for pricing AI
            sales_data = []
            for sale in sales:
                sales_data.append({
                    'product_id': sale.product.product_id,
                    'date': sale.recorded_at.date(),
                    'quantity': sale.quantity,
                    'units_sold': sale.quantity,
                    'price': sale.product.price,
                    'revenue': sale.total
                })
            
            sales_df = pd.DataFrame(sales_data)
            sales_df['date'] = pd.to_datetime(sales_df['date'])
            
            # Get product catalog
            products = Product.objects.all().values('product_id', 'name', 'price', 'cost')
            catalog_df = pd.DataFrame(list(products))
            catalog_df.columns = ['product_id', 'name', 'price', 'cost']
            catalog_df['last_change_date'] = None
            
            # Configure pricing AI
            cfg = PolicyConfig(
                min_margin_pct=0.10,         # 10% margin above cost
                max_move_pct=0.10,           # don't move more than 10% at once
                cooldown_days=3,             # respect 3-day cool-down
                planning_horizon_days=7,     # optimize for next 7 days
                min_obs_per_product=5,       # Lower threshold for smaller datasets
                default_elasticity=-1.0,
                hold_band_pct=0.02,          # small changes (<2%) become HOLD
            )
            
            # Generate recommendations
            engine = DemandPricingAI(cfg)
            proposals = engine.propose_prices(sales_df=sales_df, catalog_df=catalog_df)
            
            # Filter for actionable recommendations
            actionable = proposals[proposals['action'].isin(['INCREASE', 'DECREASE'])]
            
            if actionable.empty:
                self.stdout.write(self.style.SUCCESS('No actionable pricing recommendations found.'))
                return
            
            # Format the recommendation message
            message = self.format_pricing_recommendation(actionable, days)
            
            # Send SMS to all admins
            success_count = 0
            for u in admins:
                if self.send_sms(u.phone_number, message):
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Pricing recommendation sent to {u.username} at {u.phone_number}'))
                else:
                    self.stdout.write(self.style.ERROR(f'Failed to send pricing recommendation to {u.username} at {u.phone_number}'))
            
            self.stdout.write(
                self.style.SUCCESS(f'Pricing recommendations sent to {success_count} admin(s)')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating pricing recommendations: {str(e)}')
            )

    def format_pricing_recommendation(self, actionable_recommendations, days):
        """Format the pricing recommendation message using unified formatter"""
        from core.sms_formatter import format_pricing_recommendation
        return format_pricing_recommendation(actionable_recommendations)

    def send_sms(self, phone_number, message):
        """Send SMS using iProg SMS API"""
        try:
            from core.sms_service import sms_service
            
            result = sms_service.send_sms(phone_number, message, allow_multipart=False)
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS(result['message']))
                return True
            else:
                self.stdout.write(self.style.ERROR(result['message']))
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending SMS: {str(e)}')
            )
            return False
