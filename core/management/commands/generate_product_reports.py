from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce, Cast
from django.utils import timezone
from datetime import timedelta, datetime
from core.models import Product, Sale, ReportProductSummary, AppUser
from decimal import Decimal

class Command(BaseCommand):
    help = 'Generates periodic product performance reports and saves them to ReportProductSummary model.'

    def add_arguments(self, parser):
        parser.add_argument('--period', type=str, default='daily',
                            help='Reporting period: daily, weekly, monthly (default: daily)')
        parser.add_argument('--start_date', type=str,
                            help='Start date for custom period (YYYY-MM-DD)')
        parser.add_argument('--end_date', type=str,
                            help='End date for custom period (YYYY-MM-DD)')
        parser.add_argument('--user_id', type=int,
                            help='ID of the AppUser who generated the report')

    def handle(self, *args, **options):
        period_type = options['period'].lower()
        start_date_str = options['start_date']
        end_date_str = options['end_date']
        user_id = options['user_id']

        end_of_period = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        start_of_period = end_of_period

        if start_date_str and end_date_str:
            try:
                start_of_period = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
                end_of_period = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d')).replace(hour=23, minute=59, second=59, microsecond=999999)
            except ValueError:
                raise CommandError('Invalid date format. Use YYYY-MM-DD.')
        else:
            if period_type == 'daily':
                start_of_period = end_of_period - timedelta(days=1)
            elif period_type == 'weekly':
                start_of_period = end_of_period - timedelta(weeks=1)
            elif period_type == 'monthly':
                start_of_period = end_of_period - timedelta(days=30) # Approx month
            else:
                raise CommandError('Invalid period type. Choose from daily, weekly, monthly, or provide custom dates.')

        self.stdout.write(f"Generating reports for period: {start_of_period.strftime('%Y-%m-%d')} to {end_of_period.strftime('%Y-%m-%d')}")

        generated_by_user = None
        if user_id:
            try:
                generated_by_user = AppUser.objects.get(pk=user_id)
            except AppUser.DoesNotExist:
                self.stdout.write(self.style.warning(f"Warning: User with ID {user_id} not found. Report will be generated without a linked user."))

        products = Product.objects.filter(status='Active')
        for product in products:
            # Sales data for the period
            sales_in_period = Sale.objects.filter(
                product=product,
                status='completed',
                recorded_at__range=(start_of_period, end_of_period)
            )

            # Aggregate sales metrics - fix field names  
            sales_agg = sales_in_period.aggregate(
                total_boxes_sold=Coalesce(Sum(Cast('quantity', DecimalField())), Decimal('0.00')),
                total_revenue=Coalesce(Sum('total'), Decimal('0.00'))  # Use 'total' field
            )

            sold_qty = sales_agg['total_boxes_sold']
            revenue = sales_agg['total_revenue']
            
            # Calculate COGS manually to avoid field type issues
            cogs = Decimal('0.00')
            total_cost = Decimal('0.00')
            total_qty_for_cost = Decimal('0.00')
            for sale in sales_in_period:
                cogs += Decimal(sale.quantity) * Decimal(product.cost or 0)
                total_cost += Decimal(sale.quantity) * Decimal(product.cost or 0)
                total_qty_for_cost += Decimal(sale.quantity)
            
            gross_profit = revenue - cogs
            gross_margin_pct = (gross_profit / revenue * Decimal('100.00')) if revenue > 0 else Decimal('0.00')
            
            # Calculate average sell price (average of 'total' divided by quantity)
            avg_sell_price = (revenue / sold_qty) if sold_qty > 0 else Decimal('0.00')
            
            # Calculate average unit cost
            avg_unit_cost = (total_cost / total_qty_for_cost) if total_qty_for_cost > 0 else Decimal(product.cost or 0)
            
            # Get first and last sale dates
            first_sale_at = None
            last_sale_at = None
            if sales_in_period.exists():
                first_sale = sales_in_period.order_by('recorded_at').first()
                last_sale = sales_in_period.order_by('-recorded_at').first()
                first_sale_at = first_sale.recorded_at if first_sale else None
                last_sale_at = last_sale.recorded_at if last_sale else None
            
            # Get last addition date (need to check if StockAddition model exists)
            last_addition_at = None
            # This would need to be implemented when StockAddition model is available
            # For now, we'll leave it as None

            # --- Calculate Opening, Added, Closing Quantities ---
            # This is a simplification. For precise historical inventory, a StockMovement/Transaction log is ideal.
            # 1. Closing Quantity: Current stock (most recent accurate snapshot)
            #    If reporting for a past period, this would ideally be stock *at* end_of_period.
            #    However, without a detailed movement log, we use current stock as an approximation for reports that end 'today'.
            #    For historical reports, this will be less accurate.
            closing_qty = Decimal(product.stock) # Current stock as of report generation time

            # 2. Sold Quantity: Already calculated from sales in the period
            #    sold_qty is correct for the specified period

            # 3. Opening Quantity: Estimate by adding back sales and subtracting additions during the period
            #    This assumes `closing_qty` is `opening_qty + added_qty - sold_qty`
            #    So, `opening_qty = closing_qty - added_qty + sold_qty`
            #    Without a dedicated StockAddition model, `added_qty` is hard to determine historically.
            #    For now, `added_qty` will be approximated based on changes, or remain 0 if no clear source.

            # 4. Added Quantity: This is the most difficult without a dedicated StockAdjustment/StockIn model.
            #    For now, we will leave it as 0 unless a clear source emerges from the existing models.
            #    If there's no explicit 'stock_added_date' in Product or a related model, it's hard to track historically.
            added_qty = Decimal('0.00') # Placeholder - needs actual stock addition tracking

            # If we assume no other movements besides sales, then opening_qty = closing_qty + sold_qty
            opening_qty = closing_qty + sold_qty - added_qty # This implies any stock not sold must have been present or added.

            # Adjust opening_qty if it goes negative due to approximation issues
            if opening_qty < 0: 
                opening_qty = Decimal('0.00')
            # ---------------------------------------------------

            # Placeholder for advanced metrics
            sell_through_pct = (sold_qty / opening_qty * Decimal('100.00')) if opening_qty > 0 else Decimal('0.00')
            avg_daily_sales = (sold_qty / ((end_of_period - start_of_period).days + 1)) if (end_of_period - start_of_period).days >= 0 else Decimal('0.00')
            days_of_cover_end = (closing_qty / avg_daily_sales) if avg_daily_sales > 0 else Decimal('0.00')
            
            # Simple low stock flag based on current stock (not period-specific)
            low_stock_flag = product.stock <= 10

            # Placeholder for price action and demand level (these often come from AI/pricing models)
            price_action = 'N/A'
            demand_level = 'N/A'
            last_price = product.price # Current price, not necessarily average for period
            suggested_price = product.price # Placeholder

            # Save the report summary
            ReportProductSummary.objects.create(
                product=product,
                period_start=start_of_period,
                period_end=end_of_period,
                granularity=period_type,
                generated_by=generated_by_user,
                opening_qty=opening_qty,
                added_qty=added_qty,
                sold_qty=sold_qty,
                closing_qty=closing_qty,
                last_addition_at=last_addition_at,
                avg_sell_price=avg_sell_price,
                revenue=revenue,
                avg_unit_cost=avg_unit_cost,
                cogs=cogs,
                gross_profit=gross_profit,
                gross_margin_pct=gross_margin_pct,
                sell_through_pct=sell_through_pct,
                avg_daily_sales=avg_daily_sales,
                days_of_cover_end=days_of_cover_end,
                low_stock_flag=low_stock_flag,
                last_price=last_price,
                suggested_price=suggested_price,
                price_action=price_action,
                demand_level=demand_level,
                first_sale_at=first_sale_at,
                last_sale_at=last_sale_at
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully generated report for product {product.name} ({product.size}) for {period_type} period.'))

        self.stdout.write(self.style.SUCCESS('Product performance reports generation complete.'))
