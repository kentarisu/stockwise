from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Sale, AppUser, Product
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
        
        message = "💰 StockWise Pricing Recommendation\n\nTest Alert: This is a test pricing notification.\n\n📱 Sent by StockWise System"
        
        for u in admins:
            if self.send_sms(u.phone_number, message):
                self.stdout.write(self.style.SUCCESS(f'Test pricing recommendation sent to {u.username} at {u.phone_number}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send test pricing recommendation to {u.username} at {u.phone_number}'))

    def send_pricing_recommendations(self, days=30):
        """Send pricing recommendations based on real sales data"""
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
                max_move_pct=0.20,           # don't move more than 20% at once
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
        """Format the pricing recommendation message"""
        message = f"💰 StockWise Pricing Recommendation\n"
        message += f"📊 Based on {days} days of sales data\n\n"
        
        # Add top recommendations (limit to 3)
        top_recommendations = actionable_recommendations.head(3)
        
        for i, (_, rec) in enumerate(top_recommendations.iterrows(), 1):
            action_emoji = "📈" if rec['action'] == 'INCREASE' else "📉"
            change_pct = abs(rec['change_pct'])
            
            message += f"{i}. {action_emoji} {rec['name']}\n"
            message += f"   Current: ₱{rec['current_price']:.2f}\n"
            message += f"   Suggested: ₱{rec['suggested_price']:.2f} ({change_pct:.1f}% {rec['action'].lower()})\n"
            message += f"   Reason: {rec['reason']}\n\n"
        
        # Add summary
        increase_count = len(actionable_recommendations[actionable_recommendations['action'] == 'INCREASE'])
        decrease_count = len(actionable_recommendations[actionable_recommendations['action'] == 'DECREASE'])
        
        message += f"📋 Summary: {increase_count} increases, {decrease_count} decreases\n"
        message += f"💡 Total actionable recommendations: {len(actionable_recommendations)}\n\n"
        message += "📱 Sent by StockWise System"
        
        return message

    def send_sms(self, phone_number, message):
        """Send SMS using iProg SMS API"""
        try:
            from core.sms_service import sms_service
            
            result = sms_service.send_sms(phone_number, message)
            
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
