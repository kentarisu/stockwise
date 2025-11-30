from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Product, AppUser, SMSNotificationSettings


class Command(BaseCommand):
    help = 'Send low stock alerts to admin users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=int,
            default=10,
            help='Stock threshold for low stock alerts (default: 10)',
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Send test low stock alert instead of real data',
        )

    def handle(self, *args, **options):
        if options['test']:
            self.send_test_low_stock_alert()
        else:
            self.send_low_stock_alerts(threshold=options['threshold'])

    def _label(self, product):
        n = (getattr(product, 'name', '') or '')
        v = (getattr(product, 'variant', '') or '').strip()
        u = (getattr(product, 'quantity_unit', '') or '').strip()
        ln = n.lower()
        def has(t):
            return t and f"({t.lower()})" in ln
        parts = [n]
        if v and not has(v) and v != u:
            parts.append(f" ({v})")
        if u and not has(u) and u != v:
            parts.append(f" ({u})")
        return "".join(parts)

    def send_test_low_stock_alert(self):
        """Send a test low stock alert"""
        admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
        if not admins.exists():
            self.stdout.write(self.style.WARNING('No admin phone numbers configured.'))
            return
        
        message = "STOCKWISE Stock Alert\n\nTest Alert: This is a test notification."
        
        for u in admins:
            if self.send_sms(u.phone_number, message):
                self.stdout.write(self.style.SUCCESS(f'Test low stock alert sent to {u.username} at {u.phone_number}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send test low stock alert to {u.username} at {u.phone_number}'))

    def send_low_stock_alerts(self, threshold=None):
        """Send low stock alerts based on real inventory data"""
        # Check if stock notifications are enabled
        settings = SMSNotificationSettings.get_settings()
        if not settings.stock_enabled:
            self.stdout.write(self.style.WARNING('Stock SMS notifications are disabled in settings.'))
            return
        
        # Use threshold from settings if not provided
        if threshold is None:
            threshold = settings.stock_threshold
        
        admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
        if not admins.exists():
            self.stdout.write(self.style.WARNING('No admin phone numbers configured.'))
            return

        # Get products with low stock
        low_stock_products = Product.objects.filter(
            stock__lte=threshold,
            stock__gt=0,  # Exclude out of stock items
            status='active'
        ).order_by('stock')

        out_of_stock_products = Product.objects.filter(
            stock=0,
            status='active'
        ).order_by('name')

        if not low_stock_products.exists() and not out_of_stock_products.exists():
            self.stdout.write(self.style.SUCCESS('No low stock or out of stock items found.'))
            return

        message = self.format_low_stock_alert(low_stock_products, out_of_stock_products, threshold)

        success_count = 0
        recipients = []
        message_codes = []
        from core.sms_service import sms_service
        for u in admins:
            result = sms_service.send_sms(u.phone_number, message, allow_multipart=False)
            if result.get('success'):
                success_count += 1
                recipients.append(u.username)
                code = result.get('message_code')
                if code:
                    message_codes.append(code)
                self.stdout.write(self.style.SUCCESS(f'Low stock alert sent to {u.username} at {u.phone_number}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send low stock alert to {u.username} at {u.phone_number}: {result.get("message")}'))
        
        self.stdout.write(
            self.style.SUCCESS(f'Low stock alerts sent to {success_count} admin(s)')
        )
        
        # Log to audit logs
        try:
            from core.views import log_system_action
            total_low_stock = low_stock_products.count()
            total_out_of_stock = out_of_stock_products.count()
            if recipients:
                details = f'Threshold: {threshold} boxes\n'
                details += f'Low Stock Items: {total_low_stock}\n'
                details += f'Out of Stock Items: {total_out_of_stock}\n'
                details += f'Recipients: {", ".join(recipients)}\n'
                if message_codes:
                    details += f'Message Codes: {", ".join(message_codes)}'
                log_system_action(
                    action='Automatic SMS: Low Stock Alert (Scheduled)',
                    details=details
                )
            else:
                status = 'No recipients or no qualifying products'
                details = f'Threshold: {threshold} boxes\n'
                details += f'Low Stock Items: {total_low_stock}\n'
                details += f'Out of Stock Items: {total_out_of_stock}\n'
                details += f'Status: {status}'
                log_system_action(
                    action='Automatic SMS: Low Stock Alert (Skipped)',
                    details=details
                )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Failed to log to audit: {e}'))

    def format_low_stock_alert(self, low_stock_products, out_of_stock_products, threshold):
        message = "STOCKWISE Stock Alert\n\n"

        def _label(name, variant, quantity_unit):
            n = (name or "")
            v = (variant or "").strip()
            u = (quantity_unit or "").strip()
            ln = n.lower()
            def has(t):
                return t and f"({t.lower()})" in ln
            parts = [n]
            if v and not has(v) and v != u:
                parts.append(f" ({v})")
            if u and not has(u) and u != v:
                parts.append(f" ({u})")
            return "".join(parts)

        if out_of_stock_products.exists():
            message += "CRITICAL - OUT OF STOCK:\n"
            for product in out_of_stock_products:
                label = _label(product.name, getattr(product, 'variant', None), getattr(product, 'quantity_unit', None))
                message += f"- {label}\n"
            message += "\n"

        if low_stock_products.exists():
            message += "WARNING - LOW STOCK:\n"
            for product in low_stock_products:
                box_text = "box" if product.stock == 1 else "boxes"
                label = _label(product.name, getattr(product, 'variant', None), getattr(product, 'quantity_unit', None))
                message += f"- {label}: {product.stock} {box_text} left\n"
            message += "\n"

        if not out_of_stock_products.exists() and not low_stock_products.exists():
            message += "All products have sufficient stock.\n\n"
        return message

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
