from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Product, AppUser


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

    def send_test_low_stock_alert(self):
        """Send a test low stock alert"""
        admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
        if not admins.exists():
            self.stdout.write(self.style.WARNING('No admin phone numbers configured.'))
            return
        
        message = "⚠️ StockWise Low Stock Alert\n\nTest Alert: This is a test notification.\n\n📱 Sent by StockWise System"
        
        for u in admins:
            if self.send_sms(u.phone_number, message):
                self.stdout.write(self.style.SUCCESS(f'Test low stock alert sent to {u.username} at {u.phone_number}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send test low stock alert to {u.username} at {u.phone_number}'))

    def send_low_stock_alerts(self, threshold=10):
        """Send low stock alerts based on real inventory data"""
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

        # Format the alert message
        message = self.format_low_stock_alert(low_stock_products, out_of_stock_products, threshold)
        
        # Send SMS to all admins
        success_count = 0
        for u in admins:
            if self.send_sms(u.phone_number, message):
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f'Low stock alert sent to {u.username} at {u.phone_number}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send low stock alert to {u.username} at {u.phone_number}'))
        
        self.stdout.write(
            self.style.SUCCESS(f'Low stock alerts sent to {success_count} admin(s)')
        )

    def format_low_stock_alert(self, low_stock_products, out_of_stock_products, threshold):
        """Format the low stock alert message"""
        message = "⚠️ StockWise Low Stock Alert\n\n"
        
        # Add out of stock items first
        if out_of_stock_products.exists():
            message += "🚨 OUT OF STOCK:\n"
            for product in out_of_stock_products[:5]:  # Limit to 5 items
                message += f"• {product.name} ({product.size})\n"
            message += "\n"
        
        # Add low stock items
        if low_stock_products.exists():
            message += f"📉 LOW STOCK (≤{threshold}):\n"
            for product in low_stock_products[:5]:  # Limit to 5 items
                message += f"• {product.name} ({product.size}): {product.stock} boxes\n"
            message += "\n"
        
        # Add action recommendation
        if out_of_stock_products.exists():
            message += "🔴 Action: Restock immediately!\n"
        elif low_stock_products.exists():
            message += "🟡 Action: Consider restocking soon.\n"
        
        message += "\n📱 Sent by StockWise System"
        
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
