"""
StockWise SMS Notification Scheduler
Runs in the background and automatically sends SMS notifications based on schedule
"""
import os
import sys
import time
import logging
from datetime import datetime, time as dt_time
from pathlib import Path

# Setup Django
import django
from django.conf import settings as _dj_settings
if not getattr(_dj_settings, 'configured', False):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise_py.settings')
    django.setup()

from django.core.management import call_command
from core.models import SMSNotificationSettings
from types import SimpleNamespace
from django.db import connection
from django.db.utils import OperationalError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sms_scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SMSScheduler:
    def __init__(self):
        self.last_sales_date = None
        self.last_pricing_date = None
        self.last_sales_time_sent = None
        self.last_pricing_time_sent = None
        self.last_pricing_minute_sent = None  # Track last minute pricing was sent to prevent duplicates
        logger.info("StockWise SMS Scheduler initialized")
        logger.info("Note: Low stock alerts are sent IMMEDIATELY when stock drops, not on schedule")
        
        # Verify SMS service configuration
        try:
            from core.sms_service import sms_service
            logger.info(f"SMS Service Configuration:")
            logger.info(f"  - Sender Name: {sms_service.sender_name}")
            logger.info(f"  - API Token: {'CONFIGURED' if sms_service.api_token else 'NOT CONFIGURED'}")
            logger.info(f"  - API URL: {sms_service.api_url}")
            if not sms_service.api_token:
                logger.warning("WARNING: IPROG_API_TOKEN is not configured! SMS will not work.")
            if sms_service.sender_name != 'kaprets':
                logger.warning(f"WARNING: Sender name is '{sms_service.sender_name}', expected 'kaprets'")
        except Exception as e:
            logger.error(f"Error verifying SMS service config: {e}")
    
    def parse_time(self, time_str):
        """Parse time string in HH:MM format"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return dt_time(hour, minute)
        except:
            return dt_time(20, 0)  # Default to 8:00 PM
    
    def should_send_daily_sales(self, settings, now):
        """
        Check if we should send daily sales summary.
        BYPASS: Always sends if within 2 minutes of scheduled time (no duplicate check).
        """
        if not settings.sales_enabled:
            return False
        
        scheduled_time = self.parse_time(settings.sales_time)
        current_time = now.time()
        current_minutes = current_time.hour * 60 + current_time.minute
        scheduled_minutes = scheduled_time.hour * 60 + scheduled_time.minute
        
        # Check if we're within 2 minutes of scheduled time (allows for scheduler timing)
        time_diff = abs(current_minutes - scheduled_minutes)
        is_within_window = time_diff <= 2  # Within 2 minutes of scheduled time
        
        # BYPASS: Always send if within window - no duplicate date check
        return is_within_window
    
    # NOTE: Low stock alerts are REAL-TIME (event-driven), not scheduled
    # They are sent automatically via Django signals when stock drops below threshold
    # No scheduled check needed here
    
    def should_send_pricing(self, settings, now):
        """
        Check if we should send pricing recommendations.
        Prevents duplicate sends within the same minute.
        """
        if not settings.pricing_enabled:
            logger.debug("Pricing recommendations disabled in settings")
            return False
        
        local_now = now
        try:
            from django.utils import timezone as dj_tz
            local_now = dj_tz.localtime(dj_tz.now())
        except Exception:
            pass
        try:
            st = (getattr(settings, 'pricing_time', None) or '08:00').strip()
            scheduled_hour, scheduled_minute = [int(x) for x in st.split(':')]
        except Exception:
            try:
                scheduled_hour = int(os.getenv('PRICING_HOUR', '8'))
            except Exception:
                scheduled_hour = 8
            try:
                scheduled_minute = int(os.getenv('PRICING_MINUTE', '0'))
            except Exception:
                scheduled_minute = 0
        
        current_time = local_now.time()
        current_minutes = current_time.hour * 60 + current_time.minute
        scheduled_minutes = scheduled_hour * 60 + scheduled_minute
        
        # Check if we're at or past the scheduled minute
        # The command itself checks if now >= scheduled_dt, so we need to ensure current time >= scheduled time
        time_diff = current_minutes - scheduled_minutes
        
        # Trigger if we're at or past the scheduled time (time_diff >= 0)
        # Allow a window of up to 5 minutes after scheduled time to account for scheduler delays
        # Duplicate prevention is handled by minute key and database cooldown checks
        is_at_or_past_scheduled = time_diff >= 0 and time_diff <= 5
        
        # Additional check: prevent duplicate sends within the same minute using minute key
        # This is the primary duplicate prevention mechanism
        current_minute_key = f"{local_now.year}{local_now.month:02d}{local_now.day:02d}{local_now.hour:02d}{local_now.minute:02d}"
        if self.last_pricing_minute_sent == current_minute_key:
            logger.info(f"Pricing recommendations already sent this minute ({current_minute_key}), skipping duplicate")
            return False
        
        # Log for debugging when we're at scheduled time
        if is_at_or_past_scheduled:
            logger.info(f"Pricing recommendations scheduled time reached: {scheduled_hour:02d}:{scheduled_minute:02d}, current time: {current_time.hour:02d}:{current_time.minute:02d}:{current_time.second:02d}, time_diff: {time_diff}")
        
        # Only send if at or past scheduled time (within 5 minute window) AND not already sent this minute
        return is_at_or_past_scheduled
    
    def send_daily_sales(self):
        """Send daily sales summary"""
        try:
            logger.info("Sending daily sales summary...")
            # Determine if we should allow re-send today due to modified time
            allow_resend = False
            try:
                settings = SMSNotificationSettings.get_settings()
                hh, mm = [int(x) for x in str(getattr(settings, 'sales_time', '20:00')).split(':')]
                if self.last_sales_date is not None:
                    from django.utils import timezone as dj_tz
                    today_local = dj_tz.localtime(dj_tz.now()).date()
                    if self.last_sales_date == today_local:
                        last_tuple = self.last_sales_time_sent
                        if (last_tuple is None) or (last_tuple != (hh, mm)):
                            allow_resend = True
                cmd_args = ['--type', 'daily_sales']
                if allow_resend:
                    cmd_args.append('--allow-resend-today')
                call_command('send_notifications', *cmd_args)
                self.last_sales_time_sent = (hh, mm)
            except Exception:
                call_command('send_notifications', '--type', 'daily_sales')
                self.last_sales_time_sent = None
            try:
                settings = SMSNotificationSettings.get_settings()
                hh, mm = [int(x) for x in str(getattr(settings, 'sales_time', '20:00')).split(':')]
                self.last_sales_time_sent = (hh, mm)
            except Exception:
                self.last_sales_time_sent = None
            try:
                from django.utils import timezone as dj_tz
                self.last_sales_date = dj_tz.localtime(dj_tz.now()).date()
            except Exception:
                self.last_sales_date = datetime.now().date()
            logger.info("Daily sales summary sent successfully")
        except Exception as e:
            logger.error(f"Error sending daily sales summary: {e}", exc_info=True)
    
    # send_low_stock() removed - Low stock alerts are REAL-TIME via Django signals
    
    def send_pricing(self):
        """Send pricing recommendations with duplicate prevention"""
        try:
            # Only check if we already sent in this exact minute to prevent duplicate sends from rapid scheduler checks
            try:
                from django.utils import timezone as dj_tz
                local_now = dj_tz.localtime(dj_tz.now())
                current_minute_key = f"{local_now.year}{local_now.month:02d}{local_now.day:02d}{local_now.hour:02d}{local_now.minute:02d}"
            except Exception:
                current_minute_key = datetime.now().strftime('%Y%m%d%H%M')
            
            # Check if we already sent in this minute (prevent duplicate sends within same minute)
            if self.last_pricing_minute_sent == current_minute_key:
                logger.info(f"Pricing recommendations already sent this minute, skipping duplicate")
                return
            
            logger.info("Sending pricing recommendations...")
            call_command('send_notifications', '--type', 'pricing', '--allow-resend-today')
            
            # Update tracking to prevent duplicates
            self.last_pricing_minute_sent = current_minute_key
            try:
                settings = SMSNotificationSettings.get_settings()
                st = (getattr(settings, 'pricing_time', None) or '08:00').strip()
                phh, pmm = [int(x) for x in st.split(':')]
                self.last_pricing_time_sent = (phh, pmm)
            except Exception:
                self.last_pricing_time_sent = None
            try:
                from django.utils import timezone as dj_tz
                self.last_pricing_date = dj_tz.localtime(dj_tz.now()).date()
            except Exception:
                self.last_pricing_date = datetime.now().date()
            logger.info("Pricing recommendations scheduled successfully")
        except Exception as e:
            logger.error(f"Error sending pricing recommendations: {e}", exc_info=True)
    
    def run(self):
        """Main scheduler loop"""
        logger.info("StockWise SMS Scheduler started. Checking every minute...")
        logger.info("Press Ctrl+C to stop")
        
        while True:
            try:
                # Ensure database is ready and table exists
                try:
                    tables = connection.introspection.table_names()
                    if 'sms_notification_settings' not in tables:
                        logger.warning('Scheduler: DB not ready (sms_notification_settings missing); retrying in 60s')
                        time.sleep(60)
                        continue
                except OperationalError:
                    logger.warning('Scheduler: database operational error; retrying in 60s')
                    time.sleep(60)
                    continue

                # Verify required columns exist; if missing, use safe defaults
                try:
                    with connection.cursor() as cursor:
                        cols = [c.name for c in connection.introspection.get_table_description(cursor, 'sms_notification_settings')]
                except Exception:
                    cols = []

                required_cols = {'pricing_time', 'pricing_frequency_days'}
                has_required = required_cols.issubset(set(cols))

                if not has_required:
                    logger.error('Scheduler: sms_notification_settings missing pricing columns; using defaults. Apply database migrations to add pricing_time and pricing_frequency_days.')
                    settings = SimpleNamespace(
                        sales_enabled=True,
                        sales_time=os.getenv('SALES_TIME', '20:00'),
                        stock_enabled=True,
                        stock_threshold=int(os.getenv('STOCK_THRESHOLD', '10')),
                        pricing_enabled=True,
                        pricing_sensitivity=os.getenv('PRICING_SENSITIVITY', 'moderate'),
                        pricing_time=os.getenv('PRICING_TIME', '08:00'),
                        pricing_frequency_days=int(os.getenv('PRICING_FREQUENCY_DAYS', '3')),
                    )
                else:
                    # Get current settings (safe once schema matches model)
                    settings = SMSNotificationSettings.get_settings()
                try:
                    from django.utils import timezone as dj_tz
                    now = dj_tz.localtime(dj_tz.now())
                except Exception:
                    now = datetime.now()
                
                # Check each notification type
                if self.should_send_daily_sales(settings, now):
                    self.send_daily_sales()
                
                # Low stock alerts are REAL-TIME (not scheduled)
                # They trigger automatically when stock drops via Django signals
                
                if self.should_send_pricing(settings, now):
                    self.send_pricing()
                
                # Wait 60 seconds before next check
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in scheduler: {e}")
                time.sleep(60)


if __name__ == "__main__":
    scheduler = SMSScheduler()
    scheduler.run()

