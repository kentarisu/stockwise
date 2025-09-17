from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from core.models import Sale, AppUser
from django.conf import settings
import requests
import os
from django.conf import settings


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
        admins = AppUser.objects.filter(role='Admin').exclude(phone_number='')
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
            .values('product__name')
            .annotate(quantity=Sum('quantity'))
            .order_by('-quantity')[:3])
        
        # Format the message
        message = self.format_sales_summary(
            target_date, total_sales, total_revenue, total_boxes, top_products, date_label
        )
        
        # Send SMS to all active notifications
        success_count = 0
        for u in admins:
            if self.send_sms(u.phone_number, message):
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f'Daily summary sent to {u.username} at {u.phone_number}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send daily summary to {u.username} at {u.phone_number}'))
        
        self.stdout.write(
            self.style.SUCCESS(f'Daily SMS summary sent to {success_count} admin(s)')
        )

    def format_sales_summary(self, date, total_sales, total_revenue, total_boxes, top_products, date_label="Yesterday"):
        """Format the sales summary message"""
        date_str = date.strftime('%B %d, %Y')
        
        message = f"📊 StockWise {date_label} Sales Summary\n"
        message += f"📅 Date: {date_str}\n\n"
        message += f"💰 Total Revenue: ₱{total_revenue:,.2f}\n"
        message += f"📦 Total Boxes Sold: {total_boxes}\n"
        message += f"🛒 Total Transactions: {total_sales}\n\n"
        
        if top_products:
            message += "🏆 Top Selling Products:\n"
            for i, product in enumerate(top_products, 1):
                message += f"{i}. {product['product__name']}: {product['quantity']} boxes\n"
        
        message += "\n📱 Sent by StockWise System"
        
        return message

    def send_sms(self, phone_number, message):
        """Send SMS using Twilio (you can replace with other SMS providers)"""
        try:
            # Using Twilio as the SMS provider
            # You'll need to install: pip install twilio
            # And configure these in Django settings or environment variables:
            # TWILIO_ACCOUNT_SID
            # TWILIO_AUTH_TOKEN
            # TWILIO_FROM_PHONE
            
            from twilio.rest import Client
            
            # Try environment variables first, then Django settings
            account_sid = os.getenv('TWILIO_ACCOUNT_SID') or getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            auth_token = os.getenv('TWILIO_AUTH_TOKEN') or getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            twilio_phone = os.getenv('TWILIO_FROM_PHONE') or os.getenv('TWILIO_PHONE_NUMBER') or getattr(settings, 'TWILIO_FROM_PHONE', None)
            
            if not all([account_sid, auth_token, twilio_phone]):
                self.stdout.write(
                    self.style.ERROR('Twilio credentials not configured. Please set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_PHONE in Django settings or environment variables.')
                )
                return False
            
            # Normalize phone number to E.164 format. Default to +63 if no country code
            normalized = (phone_number or '').strip()
            # remove spaces, hyphens, and parentheses commonly typed by users
            normalized = normalized.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if normalized.startswith('00'):
                normalized = '+' + normalized[2:]
            if normalized.startswith('0'):
                normalized = '+63' + normalized.lstrip('0')
            elif not normalized.startswith('+'):
                # If no explicit country code, assume Philippines by default
                normalized = '+63' + normalized

            client = Client(account_sid, auth_token)

            message_obj = client.messages.create(
                body=message,
                from_=twilio_phone,
                to=normalized
            )
            
            self.stdout.write(f'SMS sent successfully. SID: {message_obj.sid}')
            return True
            
        except ImportError:
            self.stdout.write(
                self.style.ERROR('Twilio not installed. Please install with: pip install twilio')
            )
            return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending SMS: {str(e)}')
            )
            return False
