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
        logger.info("StockWise SMS Scheduler initialized")
        logger.info("Note: Low stock alerts are sent IMMEDIATELY when stock drops, not on schedule")
    
    def parse_time(self, time_str):
        """Parse time string in HH:MM format"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return dt_time(hour, minute)
        except:
            return dt_time(20, 0)  # Default to 8:00 PM
    
    def should_send_daily_sales(self, settings, now):
        """Check if daily sales summary should be sent"""
        if not settings.sales_enabled:
            return False
        
        # Check if already sent today
        today = now.date()
        if self.last_sales_date == today:
            return False
        
        # Check if current time matches scheduled time
        scheduled_time = self.parse_time(settings.sales_time)
        current_time = now.time()
        
        # Send if current time is within 1 minute of scheduled time
        time_diff = abs((current_time.hour * 60 + current_time.minute) - 
                       (scheduled_time.hour * 60 + scheduled_time.minute))
        
        if time_diff <= 1:
            return True
        
        return False
    
    # NOTE: Low stock alerts are REAL-TIME (event-driven), not scheduled
    # They are sent automatically via Django signals when stock drops below threshold
    # No scheduled check needed here
    
    def should_send_pricing(self, settings, now):
        """Check if pricing recommendations should be sent"""
        if not settings.pricing_enabled:
            return False
        
        # Check if already sent today
        today = now.date()
        if self.last_pricing_date == today:
            return False
        
        local_now = now  # naive fallback
        try:
            from django.utils import timezone as dj_tz
            local_now = dj_tz.localtime(dj_tz.now())
        except Exception:
            pass
        try:
            # Prefer DB settings if available
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
        is_after_scheduled = (current_time.hour * 60 + current_time.minute) >= (scheduled_hour * 60 + scheduled_minute)
        try:
            frequency_days = int(getattr(settings, 'pricing_frequency_days', 3))
        except Exception:
            try:
                frequency_days = int(os.getenv('PRICING_FREQUENCY_DAYS', '3'))
            except Exception:
                frequency_days = 3
        is_eligible_day = (self.last_pricing_date is None) or ((today - self.last_pricing_date).days >= frequency_days)
        if is_eligible_day and is_after_scheduled:
            return True
        
        return False
    
    def send_daily_sales(self):
        """Send daily sales summary"""
        try:
            logger.info("Sending daily sales summary...")
            call_command('send_daily_sms', '--now')
            try:
                from django.utils import timezone as dj_tz
                self.last_sales_date = dj_tz.localtime(dj_tz.now()).date()
            except Exception:
                self.last_sales_date = datetime.now().date()
            logger.info("Daily sales summary sent successfully")
        except Exception as e:
            logger.error(f"Error sending daily sales summary: {e}")
    
    # send_low_stock() removed - Low stock alerts are REAL-TIME via Django signals
    
    def send_pricing(self):
        """Send pricing recommendations"""
        try:
            logger.info("Sending pricing recommendations...")
            call_command('send_auto_pricing')
            try:
                from django.utils import timezone as dj_tz
                self.last_pricing_date = dj_tz.localtime(dj_tz.now()).date()
            except Exception:
                self.last_pricing_date = datetime.now().date()
            logger.info("Pricing recommendations sent successfully")
        except Exception as e:
            logger.error(f"Error sending pricing recommendations: {e}")
    
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

                # Get current settings (safe once table exists)
                settings = SMSNotificationSettings.get_settings()
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

