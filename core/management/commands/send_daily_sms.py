from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from core.models import Sale, AppUser, SMSNotificationSettings


class Command(BaseCommand):
    help = 'Send daily sales summary SMS to admin users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Send test SMS instead of daily summary',
        )
        parser.add_argument(
            '--now',
            action='store_true',
            help='Send daily summary for today instead of yesterday',
        )

    def handle(self, *args, **options):
        if options['test']:
            self.send_test_sms()
        else:
            self.send_daily_summary(use_today=options['now'])

    def send_test_sms(self):
        """Send a test SMS to all admins with a configured phone number"""
        admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
        if not admins.exists():
            self.stdout.write(self.style.WARNING('No admin phone numbers configured.'))
            return
        message = "Test SMS from StockWise. Notifications are working."
        for u in admins:
            if self.send_sms(u.phone_number, message):
                self.stdout.write(self.style.SUCCESS(f'Test SMS sent to {u.username} at {u.phone_number}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send test SMS to {u.username} at {u.phone_number}'))

    def send_daily_summary(self, use_today=False):
        """Send daily sales summary SMS"""
        # Check if sales notifications are enabled
        settings = SMSNotificationSettings.get_settings()
        if not settings.sales_enabled:
            self.stdout.write(self.style.WARNING('Sales SMS notifications are disabled in settings.'))
            return
        
        admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
        if not admins.exists():
            self.stdout.write(self.style.WARNING('No admin phone numbers configured.'))
            return

        # Get sales data for today or yesterday
        if use_today:
            target_date = timezone.now().date()
            date_label = "Today"
        else:
            target_date = timezone.now().date() - timedelta(days=1)
            date_label = "Yesterday"
        
        # Get sales for target date
        sales_query = Sale.objects.filter(recorded_at__date=target_date, status='completed')
        
        # Calculate summary statistics
        total_sales = sales_query.count()
        total_revenue = sales_query.aggregate(total=Sum('total'))['total'] or 0
        total_boxes = sales_query.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Get top selling products
        top_products = (sales_query
            .values('product__name', 'product__variant', 'product__quantity_unit')
            .annotate(quantity=Sum('quantity'))
            .order_by('-quantity')[:3])
        
        # Format the message
        message = self.format_sales_summary(
            target_date, total_sales, total_revenue, total_boxes, top_products, date_label
        )
        
        # Send SMS to all active notifications
        success_count = 0
        recipients = []
        message_codes = []
        from core.sms_service import sms_service
        for u in admins:
            result = sms_service.send_sms(u.phone_number, message, allow_multipart=True)
            if result.get('success'):
                success_count += 1
                recipients.append(u.username)
                code = result.get('message_code')
                if code:
                    message_codes.append(code)
                self.stdout.write(self.style.SUCCESS(f'Daily summary sent to {u.username} at {u.phone_number}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send daily summary to {u.username} at {u.phone_number}: {result.get('message')}'))
        
        if recipients:
            from core.views import log_system_action
            date_str = target_date.strftime('%B %d, %Y')
            details = (
                f'Date: {date_str}\n'
                f'Revenue: ₱{total_revenue:,.2f}\n'
                f'Transactions: {total_sales}\n'
                f'Boxes Sold: {total_boxes}\n'
                f'Recipients: {", ".join(recipients)}'
            )
            if message_codes:
                details += f'\nMessage Codes: {", ".join(message_codes)}'
            log_system_action(
                action='Automatic SMS: Daily Sales Summary',
                details=details
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Daily SMS summary sent to {success_count} admin(s)')
        )

    def format_sales_summary(self, date, total_sales, total_revenue, total_boxes, top_products, date_label="Yesterday"):
        """Format the sales summary message (ASCII, professional, matches dashboard style)"""
        date_str = date.strftime('%B %d, %Y')
        
        message = "STOCKWISE Daily Sales Report\n"
        message += f"Date: {date_str}\n\n"
        message += "==== OVERALL SUMMARY ====\n"
        message += f"Total Revenue: PHP {total_revenue:,.2f}\n"
        message += f"Total Boxes Sold: {total_boxes}\n"
        message += f"Total Transactions: {total_sales}\n\n"
        
        if top_products:
            message += "==== TOP PRODUCTS TODAY ====\n"
            for i, product in enumerate(top_products, 1):
                name = product.get('product__name') or ''
                variant = product.get('product__variant') or ''
                unit = product.get('product__quantity_unit') or ''
                variant_part = f" ({variant})" if variant else ""
                unit_part = f" ({unit})" if unit else ""
                message += f"{i}. {name}{variant_part}{unit_part}\n"
                message += f"   Sold: {product['quantity']} boxes\n\n"
        else:
            message += "No sales recorded today.\n\n"
        
        message += "- STOCKWISE"
        
        return message

    def send_sms(self, phone_number, message):
        """Send SMS using iProg SMS API"""
        try:
            from core.sms_service import sms_service
            
            result = sms_service.send_sms(phone_number, message, allow_multipart=True)
            
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
