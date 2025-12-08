"""
Management command to test SMS sending functionality
Usage: python manage.py test_sms [phone_number] [message]
"""
from django.core.management.base import BaseCommand
from core.sms_service import sms_service
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Test SMS sending functionality with detailed logging'

    def add_arguments(self, parser):
        parser.add_argument(
            'phone_number',
            nargs='?',
            type=str,
            help='Phone number to send test SMS to (e.g., +639123456789)',
        )
        parser.add_argument(
            'message',
            nargs='?',
            type=str,
            default='Test SMS from StockWise - Automated feature test',
            help='Message to send (default: Test message)',
        )

    def handle(self, *args, **options):
        phone_number = options.get('phone_number')
        message = options.get('message', 'Test SMS from StockWise - Automated feature test')
        
        # Check API token configuration
        api_token = os.getenv('IPROG_API_TOKEN') or getattr(settings, 'IPROG_API_TOKEN', None)
        
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('SMS Service Configuration'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(f"API Token: {'*' * 20 if api_token else 'NOT CONFIGURED'}")
        self.stdout.write(f"API Token Length: {len(api_token) if api_token else 0}")
        self.stdout.write(f"Sender Name: {sms_service.sender_name}")
        self.stdout.write(f"API URL: {sms_service.api_url}")
        self.stdout.write('')
        
        if not api_token:
            self.stdout.write(self.style.ERROR('ERROR: IPROG_API_TOKEN is not configured!'))
            self.stdout.write(self.style.WARNING('Set it via:'))
            self.stdout.write('  - Environment variable: set IPROG_API_TOKEN=your_token')
            self.stdout.write('  - Or in settings.py: IPROG_API_TOKEN = "your_token"')
            return
        
        if not phone_number:
            self.stdout.write(self.style.ERROR('ERROR: Phone number is required!'))
            self.stdout.write(self.style.WARNING('Usage: python manage.py test_sms +639123456789 "Your message"'))
            return
        
        # Normalize phone number
        normalized = sms_service.normalize_phone_number(phone_number)
        self.stdout.write(f"Original phone: {phone_number}")
        self.stdout.write(f"Normalized phone: {normalized}")
        self.stdout.write('')
        
        if not normalized or not normalized.startswith('63') or len(normalized) not in (11, 12):
            self.stdout.write(self.style.ERROR(f'ERROR: Invalid phone number format: {phone_number} -> {normalized}'))
            return
        
        # Send test SMS
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('Sending Test SMS...'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(f"To: {normalized}")
        self.stdout.write(f"Message: {message}")
        self.stdout.write(f"Sender: {sms_service.sender_name}")
        self.stdout.write('')
        
        self.stdout.write(self.style.WARNING('Note: Check Django logs and console for detailed API request/response information'))
        self.stdout.write('')
        
        try:
            result = sms_service.send_sms(phone_number, message, allow_multipart=True)
            
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('Result:'))
            self.stdout.write(self.style.WARNING('=' * 60))
            
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS('✓ SMS sent successfully!'))
                self.stdout.write(f"Message: {result.get('message', 'N/A')}")
                if result.get('message_code'):
                    self.stdout.write(f"Message Code: {result.get('message_code')}")
                if result.get('responses'):
                    for idx, resp in enumerate(result.get('responses', []), 1):
                        self.stdout.write(f"  Response {idx}: {resp}")
            else:
                self.stdout.write(self.style.ERROR('✗ SMS sending failed!'))
                self.stdout.write(self.style.ERROR(f"Error: {result.get('message', 'Unknown error')}"))
                if result.get('responses'):
                    self.stdout.write(self.style.ERROR('Detailed responses:'))
                    for idx, resp in enumerate(result.get('responses', []), 1):
                        self.stdout.write(self.style.ERROR(f"  Response {idx}: {resp}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Exception occurred: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))

