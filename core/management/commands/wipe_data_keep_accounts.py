from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.conf import settings
from pathlib import Path
import shutil

from core.models import (
    AppUser,
    SMSNotificationSettings,
    Sale,
    StockAddition,
    ReportProductSummary,
    SMS,
    PricingRecommendation,
    ActionLog,
    Backup,
    Product,
)


class Command(BaseCommand):
    help = (
        "Delete transactional data while keeping accounts and system settings.\n"
        "By default, deletes: Sales, StockAdditions, Reports, SMS, PricingRecommendations, ActionLogs, Backups.\n"
        "Optional: use --delete-products to also delete Products. Use --delete-media to clear MEDIA_ROOT/uploads."
    )

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
        parser.add_argument('--delete-products', action='store_true', help='Also delete Product catalog')
        parser.add_argument('--delete-media', action='store_true', help='Delete media/uploads files')
        parser.add_argument('--reset-sequences', action='store_true', help='Reset autoincrement sequences where supported')

    def handle(self, *args, **options):
        # Safety confirmation
        if not options['force']:
            self.stdout.write(self.style.WARNING(
                'This will delete transactional data. Accounts (AppUser) and settings will be preserved.'
            ))
            self.stdout.write('Proceed? Run again with --force to skip this prompt.')
            return

        delete_products = options['delete-products']
        delete_media = options['delete-media']
        reset_sequences = options['reset-sequences']

        with transaction.atomic():
            # Delete dependent tables first to avoid FK issues
            def purge(model, label):
                count = model.objects.count()
                model.objects.all().delete()
                self.stdout.write(f"Deleted {count} {label}")

            purge(SMS, 'SMS messages')
            purge(Sale, 'sales')
            purge(StockAddition, 'stock additions')
            purge(ReportProductSummary, 'product summary reports')
            purge(PricingRecommendation, 'pricing recommendations')
            purge(ActionLog, 'action logs')
            purge(Backup, 'backup records')

            if delete_products:
                purge(Product, 'products')
            else:
                self.stdout.write(self.style.WARNING('Products were kept (use --delete-products to remove them).'))

            # Never delete accounts or settings
            self.stdout.write(self.style.SUCCESS(f"Accounts preserved: {AppUser.objects.count()} user(s)"))
            try:
                self.stdout.write(self.style.SUCCESS('System settings preserved'))
            except Exception:
                pass

            if delete_media:
                media_root = Path(getattr(settings, 'MEDIA_ROOT', Path(settings.BASE_DIR) / 'media'))
                legacy_uploads = Path(settings.BASE_DIR.parent) / 'uploads'
                for src in (media_root, legacy_uploads):
                    if src.exists():
                        self.stdout.write(f"Deleting media directory: {src}")
                        try:
                            shutil.rmtree(src)
                            self.stdout.write(self.style.SUCCESS(f"✓ Deleted: {src}"))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Error deleting {src}: {e}"))
                    else:
                        self.stdout.write(f"Media directory not found: {src}")

            if reset_sequences:
                # Best-effort reset for SQLite
                try:
                    if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                        with connection.cursor() as cursor:
                            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN (\n"
                                           "'sales','stock_additions','report_product_summary',\n"
                                           "'sms','action_logs','pricing_recommendations','backups','products'\n"
                                           ")")
                        self.stdout.write(self.style.SUCCESS('✓ SQLite autoincrement sequences reset'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Sequence reset skipped: {e}"))

        self.stdout.write(self.style.SUCCESS('✓ Data wipe completed (accounts and settings preserved)'))

