"""
Management command to automatically send AI pricing recommendations
Runs every 3 days to analyze sales and suggest optimal prices
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from core.models import Sale, Product, AppUser, SMSNotificationSettings, SMS
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
            # Check if pricing notifications are enabled
            settings = SMSNotificationSettings.get_settings()
            if not settings.pricing_enabled and not force:
                self.stdout.write(self.style.WARNING('Pricing SMS notifications are disabled in settings.'))
                return
            
            # Get all admins with phone numbers
            admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
            if not admins.exists():
                self.stdout.write(self.style.WARNING('No admin phone numbers configured'))
                return

            # Idempotency guard limited to same-minute only; allow multiple sends in the same day
            try:
                from core.models import ActionLog
                from django.utils import timezone as _tz
                now_local = _tz.localtime(_tz.now())
                recent_cutoff = now_local - _tz.timedelta(minutes=1)
                if ActionLog.objects.filter(action='Automatic SMS: Pricing Recommendations', created_at__gte=recent_cutoff).exists() and not force:
                    self.stdout.write(self.style.WARNING('Skip: Pricing recommendations recently logged (≤1 min); preventing duplicate send'))
                    return
            except Exception:
                pass

            # Cooperative lock: only one process proceeds for this minute
            lock_id = None
            try:
                from core.models import ActionLog
                from django.utils import timezone as _tz
                minute_key = _tz.localtime(_tz.now()).strftime('%Y%m%d%H%M')
                lock = ActionLog.objects.create(
                    action='Automatic SMS: Pricing Recommendations (LOCK)',
                    details=f'minute={minute_key}',
                    metadata='{}'
                )
                lock_id = lock.action_id
                # Determine the earliest lock in this minute
                earliest = ActionLog.objects.filter(
                    action='Automatic SMS: Pricing Recommendations (LOCK)',
                    details=f'minute={minute_key}'
                ).order_by('action_id').first()
                if earliest and earliest.action_id != lock_id and not force:
                    self.stdout.write(self.style.WARNING('Skip: Another process holds pricing send lock for this minute'))
                    return
            except Exception:
                pass
            
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
                
                # Generate recommendations
                cfg = PolicyConfig(
                    min_margin_pct=0.10,
                    max_move_pct=0.10,
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

                # Persist recommendations for dashboard/offcanvas consistency
                try:
                    from core.models import PricingRecommendation
                    from decimal import Decimal
                    from datetime import timedelta
                    unique_proposals = proposals.drop_duplicates(subset=['product_id'], keep='last')
                    from core.models import PricingRecommendation as _PR
                    _PR.objects.filter(expires_at__gt=timezone.now()).delete()
                    affected_ids = unique_proposals['product_id'].tolist()
                    expires_at = timezone.now() + timezone.timedelta(days=3)
                    for _, rec in unique_proposals.iterrows():
                        # Skip HOLD recommendations - they should not be stored
                        action_str = str(rec.get('action') or '').strip().upper()
                        if action_str == 'HOLD':
                            continue
                        
                        # Enforce maximum 10% change - skip if exceeds
                        change_pct_val = abs(float(rec.get('change_pct', 0) or 0))
                        if change_pct_val > 10.0:
                            continue  # Skip recommendations that exceed 10% change
                        
                        try:
                            product = Product.objects.get(product_id=rec['product_id'])
                        except Exception:
                            continue
                        # Normalize reason for parity (friendly, short)
                        sales_count = rec.get('sales_count', 0)
                        if sales_count > 0:
                            if rec['action'] == 'INCREASE':
                                friendly = 'Good sales trend in the past 3 days'
                            elif rec['action'] == 'DECREASE':
                                friendly = 'Low sales activity in the past 3 days'
                            else:
                                friendly = 'Price optimization'
                        else:
                            friendly = 'Price optimization'
                        PricingRecommendation.objects.create(
                            product=product,
                            current_price=Decimal(str(rec['current_price'])),
                            suggested_price=Decimal(str(rec['suggested_price'])),
                            change_pct=Decimal(str(rec['change_pct'])),
                            action=rec['action'],
                            reason=friendly,
                            elasticity=Decimal(str(rec['elasticity'])) if rec.get('elasticity') is not None else None,
                            r2=Decimal(str(rec['r2'])) if rec.get('r2') is not None else None,
                            confidence=rec.get('confidence', 'MED'),
                            expires_at=expires_at
                        )
                except Exception as e:
                    logger.warning(f"Failed to persist pricing recommendations: {e}")
                
                if actionable.empty and not force:
                    self.stdout.write(self.style.SUCCESS('No pricing changes needed - all products optimally priced'))
                    return
                
                # Build SMS from persisted actionable recommendations to match offcanvas exactly
                sent_count = 0
                recipients = []
                from core.models import PricingRecommendation
                from core.pricing_ai import format_pricing_sms_from_queryset, validate_pricing_sms_parity
                qs = PricingRecommendation.objects.filter(
                    expires_at__gt=timezone.now()
                ).select_related('product')
                actionable_qs = qs.filter(action__in=['INCREASE', 'DECREASE'])
                if not actionable_qs.exists() and not force:
                    message = self._format_no_recommendations_message()
                else:
                    message = format_pricing_sms_from_queryset(actionable_qs)
                # Validation parity check
                if actionable_qs.exists() and not validate_pricing_sms_parity(actionable_qs, message):
                    logger.warning('Parity validation failed: SMS content does not match persisted recommendations')
                for admin in admins:
                    try:
                        scheduled_at = timezone.localtime().strftime('%Y-%m-%d %I:%M%p')
                    except Exception:
                        from datetime import datetime as _dt
                        scheduled_at = _dt.now().strftime('%Y-%m-%d %I:%M%p')
                    result = sms_service.schedule_sms_reminder(admin.phone_number, message, scheduled_at)
                    if result['success']:
                        sent_count += 1
                        recipients.append(admin.username)
                        try:
                            product = Product.objects.filter(status='active').first() or Product.objects.first()
                            if product:
                                SMS.objects.create(
                                    product=product,
                                    user=admin,
                                    message_type='pricing_alert',
                                    demand_level='mid',
                                    message_content=message[:500]
                                )
                        except Exception:
                            pass
                        logger.info(f"Pricing recommendations sent to {admin.username}")
                    else:
                        logger.error(f"Failed to send to {admin.username}: {result['message']}")
                
                # Log to audit trail
                from core.views import log_system_action
                if recipients:
                    if actionable.empty:
                        details = 'Status: No changes recommended - all products optimally priced'
                    else:
                        details = f'Recommendations: {len(actionable)} products\n'
                        for idx, r in enumerate(actionable_qs[:10], 1):
                            action_symbol = "↑" if r.action == 'INCREASE' else "↓"
                            details += f'{idx}. {r.product.name}: ₱{float(r.current_price):.0f} → ₱{float(r.suggested_price):.0f} ({action_symbol}{abs(float(r.change_pct)):.0f}%)\n'
                    details += f'Recipients: {", ".join(recipients)}'
                    log_system_action(
                        action='Automatic SMS: Pricing Recommendations',
                        details=details
                    )
                else:
                    status = 'No recipients or feature disabled'
                    if actionable.empty:
                        details = 'Status: No changes recommended - all products optimally priced\n'
                    else:
                        details = f'Recommendations: {len(actionable)} products\n'
                    details += f'Status: {status}'
                    log_system_action(
                        action='Automatic SMS: Pricing Recommendations (Skipped)',
                        details=details
                    )
                
                self.stdout.write(self.style.SUCCESS(f'Pricing recommendations sent to {sent_count} admin(s)'))
                
            except Exception as e:
                logger.error(f"Error generating pricing recommendations: {str(e)}")
                self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
                
        except Exception as e:
            logger.error(f"Error in auto pricing command: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
    
    def _format_pricing_message(self, recommendations, total_count):
        message = "STOCKWISE Pricing Recommendation\n\n"

        for idx, (_, rec) in enumerate(recommendations.iterrows(), 1):
            action_symbol = "+" if rec['action'] == 'INCREASE' else "-"
            change_pct = abs(rec['change_pct'])

            try:
                product = Product.objects.get(product_id=rec.get('product_id'))
                variant_part = f" ({product.variant})" if getattr(product, 'variant', None) else ""
                unit_part = f" ({product.quantity_unit})" if getattr(product, 'quantity_unit', None) else ""
                label = f"{product.name}{variant_part}{unit_part}"
            except Exception:
                label = rec.get('name') or "Product"

            sales_count = rec.get('sales_count', 0)
            if sales_count > 0:
                if rec['action'] == 'INCREASE':
                    reason = "Good sales trend in the past 3 days"
                else:
                    reason = "Low sales activity"
            else:
                reason = "Price optimization"

            message += f"{label}\n"
            message += f"PHP {rec['current_price']:.0f} -> {rec['suggested_price']:.0f} ({action_symbol}{change_pct:.0f}%)\n"
            message += f"Reason: {reason}\n\n"

        return message
    
    def _format_no_recommendations_message(self):
        from core.sms_formatter import format_pricing_recommendation
        return format_pricing_recommendation([])
