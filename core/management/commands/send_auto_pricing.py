"""
Management command to automatically send AI pricing recommendations
Runs every 3 days to analyze sales and suggest optimal prices
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from core.models import Sale, Product, AppUser
from core.sms_service import sms_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Automatically send AI pricing recommendations every 3 days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force send even if no recommendations',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        try:
            # Get all admins with phone numbers
            admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
            if not admins.exists():
                self.stdout.write(self.style.WARNING('No admin phone numbers configured'))
                return
            
            # Generate pricing recommendations using AI
            try:
                from core.pricing_ai import DemandPricingAI, PolicyConfig
                import pandas as pd
                
                # Get sales data from last 30 days
                end_date = timezone.now()
                start_date = end_date - timezone.timedelta(days=30)
                
                sales = Sale.objects.filter(
                    recorded_at__gte=start_date,
                    recorded_at__lte=end_date,
                    status='completed'
                ).select_related('product')
                
                if not sales.exists() and not force:
                    self.stdout.write(self.style.WARNING('No sales data available for analysis'))
                    return
                
                # Convert to DataFrame
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
                
                # Generate recommendations
                cfg = PolicyConfig(
                    min_margin_pct=0.10,
                    max_move_pct=0.20,
                    cooldown_days=3,
                    planning_horizon_days=7,
                    min_obs_per_product=3,
                    default_elasticity=-1.0,
                    hold_band_pct=0.02,
                )
                
                engine = DemandPricingAI(cfg)
                proposals = engine.propose_prices(sales_df=sales_df, catalog_df=catalog_df)
                
                # Get actionable recommendations
                actionable = proposals[proposals['action'].isin(['INCREASE', 'DECREASE'])]
                
                if actionable.empty and not force:
                    self.stdout.write(self.style.SUCCESS('No pricing changes needed - all products optimally priced'))
                    return
                
                # Send SMS to each admin
                sent_count = 0
                for admin in admins:
                    if actionable.empty:
                        message = self._format_no_recommendations_message()
                    else:
                        # Get top 3 recommendations
                        top_recs = actionable.head(3)
                        message = self._format_pricing_message(top_recs, len(actionable))
                    
                    result = sms_service.send_sms(admin.phone_number, message, allow_multipart=True)
                    if result['success']:
                        sent_count += 1
                        logger.info(f"Pricing recommendations sent to {admin.username}")
                    else:
                        logger.error(f"Failed to send to {admin.username}: {result['message']}")
                
                self.stdout.write(self.style.SUCCESS(f'Pricing recommendations sent to {sent_count} admin(s)'))
                
            except Exception as e:
                logger.error(f"Error generating pricing recommendations: {str(e)}")
                self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
                
        except Exception as e:
            logger.error(f"Error in auto pricing command: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
    
    def _format_pricing_message(self, recommendations, total_count):
        """Format pricing recommendations into SMS message (ultra-simplified for delivery)"""
        message = "STOCKWISE Pricing\n\n"
        
        for idx, (_, rec) in enumerate(recommendations.iterrows(), 1):
            action_symbol = "+" if rec['action'] == 'INCREASE' else "-"
            change_pct = abs(rec['change_pct'])
            
            # Create user-friendly reason
            sales_count = rec.get('sales_count', 0)
            if sales_count > 0:
                if rec['action'] == 'INCREASE':
                    reason = "Good sales trend"
                else:
                    reason = "Low sales activity"
            else:
                reason = "Price optimization"
            
            message += f"{rec['name']}\n"
            message += f"PHP {rec['current_price']:.0f} -> {rec['suggested_price']:.0f} ({action_symbol}{change_pct:.0f}%)\n"
            message += f"Reason: {reason}\n\n"
        
        message += "STOCKWISE"
        return message
    
    def _format_no_recommendations_message(self):
        """Format message when no recommendations"""
        message = "STOCKWISE AI Pricing Report\n"
        message += "Automatic 3-Day Analysis\n\n"
        message += "==== STATUS ====\n"
        message += "All products are optimally priced!\n\n"
        message += "No pricing changes recommended at this time.\n"
        message += "Your current prices are well-balanced.\n\n"
        message += "- STOCKWISE"
        return message

