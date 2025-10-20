from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from core.models import Sale, AppUser
from core.sms_service import sms_service


class Command(BaseCommand):
    help = "Send today's sales summary by SMS to the admin phone number."

    def handle(self, *args, **options):
        today = timezone.localdate()
        sales_qs = Sale.objects.filter(recorded_at__date=today, status='Completed')

        total_tx = sales_qs.count()
        total_rev = sales_qs.aggregate(sum=Sum('total'))['sum'] or 0

        msg = (
            f"StockWise Daily Report – {today:%b %d}\n"
            f"Transactions: {total_tx}\n"
            f"Revenue: ₱{total_rev:,.2f}"
        )

        admin_obj = AppUser.objects.filter(role='admin').first()
        if not admin_obj or not admin_obj.phone_number:
            self.stderr.write("No admin phone number configured – SMS not sent.")
            return

        to_phone = admin_obj.phone_number

        # Send SMS using iProg API
        result = sms_service.send_sms(to_phone, msg)
        
        if result['success']:
            self.stdout.write(self.style.SUCCESS(f"SMS sent to {to_phone}"))
        else:
            self.stderr.write(f"Failed to send SMS: {result['message']}") 