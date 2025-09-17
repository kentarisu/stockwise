from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from twilio.rest import Client

from core.models import Sale, AppUser


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
        # normalise to +63xxxxxxxxxx
        to_phone = to_phone.strip()
        if to_phone.startswith('0'):
            to_phone = '+63' + to_phone.lstrip('0')
        elif not to_phone.startswith('+'):
            to_phone = '+63' + to_phone

        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(body=msg, from_=settings.TWILIO_FROM_PHONE, to=to_phone)
            self.stdout.write(self.style.SUCCESS(f"SMS sent to {to_phone}"))
        except Exception as exc:
            self.stderr.write(f"Failed to send SMS: {exc}") 