from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import Sale, Product, SMS, AppUser, PricingRecommendation
from core.pricing_ai import DemandPricingAI, PolicyConfig
import pandas as pd


class Command(BaseCommand):
    help = 'Generate demand-driven pricing recommendations and send SMS notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Send test pricing notifications instead of real recommendations',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Automatically apply recommendations (use with caution)',
        )

    def handle(self, *args, **options):
        if options['test']:
            self.send_test_pricing_notifications()
        else:
            self.generate_and_notify_pricing_recommendations(auto_apply=options['apply'])

    def send_test_pricing_notifications(self):
        """Send test pricing notifications to all admins"""
        admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
        if not admins.exists():
            self.stdout.write(self.style.WARNING('No admin phone numbers configured.'))
            return

        message = "💰 Test Pricing Alert\nProduct: Apples\nCurrent: ₱150.00\nSuggested: ₱165.00 (+10%)\nReason: High demand detected\nConfidence: HIGH (R²=0.75)"
        
        for admin in admins:
            if self.send_sms(admin.phone_number, message):
                self.stdout.write(self.style.SUCCESS(f'Test pricing notification sent to {admin.username}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send test pricing notification to {admin.username}'))

    def generate_and_notify_pricing_recommendations(self, auto_apply=False):
        """Generate pricing recommendations and send notifications"""
        try:
            # Get sales data from last 120 days
            # Use local date to align with UI/reporting windows
            end_date = timezone.localdate()
            start_date = end_date - timedelta(days=120)
            
            sales_data = Sale.objects.filter(
                recorded_at__date__gte=start_date,
                recorded_at__date__lte=end_date,
                status__iexact='completed'
            ).values('recorded_at', 'product__product_id', 'quantity', 'price')
            
            if not sales_data.exists():
                self.stdout.write(self.style.WARNING('Insufficient sales data for pricing analysis.'))
                return
            
            # Convert to DataFrame
            sales_df = pd.DataFrame(list(sales_data))
            sales_df.columns = ['date', 'product_id', 'units_sold', 'price']
            
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
                min_obs_per_product=15,
                default_elasticity=-1.0,
                hold_band_pct=0.02,          # small changes (<2%) become HOLD
            )
            
            # Generate recommendations
            engine = DemandPricingAI(cfg)
            proposals = engine.propose_prices(sales_df=sales_df, catalog_df=catalog_df)
            
            # Filter actionable recommendations
            actionable = proposals[proposals['action'].isin(['INCREASE', 'DECREASE'])]
            
            # Filter by confidence: Only show MEDIUM or HIGH confidence (R² >= 0.3)
            if 'r2' in actionable.columns:
                reliable = actionable[actionable['r2'] >= 0.3]
                filtered_count = len(actionable) - len(reliable)
                if filtered_count > 0:
                    self.stdout.write(self.style.WARNING(f'Filtered out {filtered_count} LOW confidence recommendations (R² < 0.3)'))
                actionable = reliable
            
            if actionable.empty:
                self.stdout.write(self.style.SUCCESS('No reliable pricing recommendations at this time.'))
                return
            
            # Store recommendations in database with 3-day expiration
            try:
                now_ts = timezone.now()
                expires = now_ts + timezone.timedelta(days=3)
                # Clear existing non-expired to avoid duplicates
                PricingRecommendation.objects.filter(expires_at__gt=now_ts).delete()
                to_create = []
                for _, rec in actionable.iterrows():
                    try:
                        product = Product.objects.get(product_id=rec['product_id'])
                        to_create.append(PricingRecommendation(
                            product=product,
                            current_price=rec['current_price'],
                            suggested_price=rec['suggested_price'],
                            change_pct=rec['change_pct'],
                            action=rec['action'],
                            reason=rec['reason'],
                            elasticity=rec.get('elasticity'),
                            r2=rec.get('r2'),
                            confidence=rec.get('confidence'),
                            expires_at=expires
                        ))
                    except Product.DoesNotExist:
                        continue
                if to_create:
                    PricingRecommendation.objects.bulk_create(to_create)
                    self.stdout.write(self.style.SUCCESS(f'Stored {len(to_create)} recommendations in database'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error storing recommendations: {str(e)}'))
            
            # Send notifications to admins
            admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
            
            for _, rec in actionable.iterrows():
                # Create SMS record
                try:
                    product = Product.objects.get(product_id=rec['product_id'])
                    admin = admins.first()  # Use first admin for logging
                    if admin is None:
                        # If no admin user with phone exists, still count as processed
                        self.stdout.write(self.style.WARNING('No admin phone numbers configured.'))
                        continue
                    
                    SMS.objects.create(
                        product=product,
                        user_id=admin.user_id,
                        message_type='pricing_alert',
                        demand_level='high',
                        message_content=f"Pricing recommendation: {rec['name']} - {rec['action']} to ₱{rec['suggested_price']:.2f} ({rec['change_pct']:.1f}%)"
                    )
                    
                    # Send SMS to all admins
                    message = f"💰 Pricing Recommendation\nProduct: {rec['name']}\nCurrent: ₱{rec['current_price']:.2f}\nSuggested: ₱{rec['suggested_price']:.2f} ({rec['change_pct']:+.1f}%)\nReason: {rec['reason']}\nConfidence: {rec['confidence']}"
                    
                    for admin in admins:
                        if self.send_sms(admin.phone_number, message):
                            self.stdout.write(self.style.SUCCESS(f'Pricing notification sent to {admin.username} for {rec["name"]}'))
                        else:
                            self.stdout.write(self.style.ERROR(f'Failed to send pricing notification to {admin.username}'))
                    
                    # Auto-apply if requested (use with caution)
                    if auto_apply:
                        product.unit_price = rec['suggested_price']
                        product.save()
                        self.stdout.write(self.style.SUCCESS(f'Auto-applied pricing change for {rec["name"]}: ₱{rec["suggested_price"]:.2f}'))
                        
                except Product.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'Product {rec["product_id"]} not found'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing recommendation for {rec["name"]}: {str(e)}'))
            
            self.stdout.write(self.style.SUCCESS('Pricing recommendations generated'))
            self.stdout.write(self.style.SUCCESS(f'Processed {len(actionable)} pricing recommendations'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating pricing recommendations: {str(e)}'))

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
            self.stdout.write(self.style.ERROR(f'Failed to send SMS: {str(e)}'))
            return False
