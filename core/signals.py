from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from core.models import Sale, Product, AppUser, SMSNotificationSettings
from core.sms_service import sms_service
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

# Track recently alerted products to prevent spam
_recently_alerted = {}


@receiver(post_save, sender=Sale)
def check_low_stock_after_sale(sender, instance, created, **kwargs):
    """
    Automatically check for low stock alerts after a sale is completed
    """
    if instance.status == 'completed':
        try:
            from django.db import transaction
            def _notify():
                try:
                    product = Product.objects.get(product_id=instance.product_id)
                    if product.stock <= 10 and product.status.lower() == 'active':
                        send_low_stock_alert(product)
                except Exception:
                    pass
            transaction.on_commit(_notify)
        except Exception as e:
            logger.error(f"Error scheduling low stock check after sale: {str(e)}")


@receiver(post_save, sender=Product)
def check_low_stock_after_stock_update(sender, instance, created, **kwargs):
    """
    Automatically check for low stock alerts after stock is updated
    """
    if not created:
        try:
            logger.info(f"Product updated: {instance.name}, Stock: {instance.stock}, Status: {instance.status}")
            # Check for case-insensitive 'active' status
            if instance.stock <= 10 and instance.status.lower() == 'active':
                logger.info(f"Triggering low stock alert for {instance.name}")
                # Send low stock alert (with 24-hour cooldown to prevent spam)
                send_low_stock_alert(instance)
            else:
                logger.info(f"Not triggering alert: stock={instance.stock} > 10 or status={instance.status}")
        except Exception as e:
            logger.error(f"Error checking low stock after stock update: {str(e)}")


def send_low_stock_alert(product):
    """
    Send REAL-TIME low stock alert for a specific product
    Prevents duplicate alerts for the same product within 24 hours to prevent spam
    """
    try:
        # Check if stock notifications are enabled
        settings = SMSNotificationSettings.get_settings()
        if not settings.stock_enabled:
            logger.info("Stock SMS notifications are disabled in settings")
            return
        
        # Check if we've already alerted for this product recently (within 24 hours)
        # IMPORTANT: Use only product_id, not stock, to prevent duplicate alerts when stock changes
        now = timezone.now()
        product_key = str(product.product_id)  # Use only product_id, not stock level
        
        if product_key in _recently_alerted:
            last_alert_time = _recently_alerted[product_key]
            if now - last_alert_time < timedelta(hours=24):  # Changed from 5 minutes to 24 hours
                logger.info(f"Skipping duplicate alert for {product.name} (last alerted {(now - last_alert_time).seconds}s ago)")
                return
        
        admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
        if not admins.exists():
            return
        
        # Build multi-line SMS in the requested style
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

        label = _label(product.name, getattr(product, 'variant', None), getattr(product, 'quantity_unit', None))
        if product.stock == 0:
            message = (
                "STOCKWISE Stock Alert\n\n"
                "CRITICAL - OUT OF STOCK:\n"
                f"- {label}\n\n"
                "- STOCKWISE"
            )
        else:
            box_text = "box" if int(product.stock) == 1 else "boxes"
            message = (
                "STOCKWISE Stock Alert\n\n"
                "WARNING - LOW STOCK:\n"
                f"- {label}: {int(product.stock)} {box_text} left\n\n"
                "- STOCKWISE"
            )
        
        # Send SMS to all admins IMMEDIATELY (REAL-TIME)
        recipients = []
        message_codes = []
        for admin in admins:
            result = sms_service.send_sms(admin.phone_number, message, allow_multipart=False)
            if result.get('success'):
                logger.info(f"REAL-TIME low stock alert sent to {admin.username} at {admin.phone_number}")
                recipients.append(admin.username)
                code = result.get('message_code')
                if code:
                    message_codes.append(code)
            else:
                logger.error(f"Failed to send low stock alert to {admin.username}: {result.get('message')}")
        
        # Log to audit trail
        if recipients:
            from core.views import log_system_action
            quantity_info = f" ({product.quantity_unit})" if product.quantity_unit else ""
            alert_type = "OUT OF STOCK" if product.stock == 0 else "LOW STOCK"
            details = (
                f'Product: {product.name}{quantity_info}\n'
                f'Stock: {product.stock} boxes\n'
                f'Recipients: {", ".join(recipients)}'
            )
            if message_codes:
                details += f'\nMessage Codes: {", ".join(message_codes)}'
            log_system_action(
                action=f'Automatic SMS: {alert_type} Alert',
                details=details
            )
        
        # Record that we've sent an alert for this product
        _recently_alerted[product_key] = now
        
        # Clean up old entries (older than 48 hours) to prevent memory bloat
        cleanup_time = now - timedelta(hours=48)
        for k, v in list(_recently_alerted.items()):
            if v < cleanup_time:
                del _recently_alerted[k]
                
    except Exception as e:
        logger.error(f"Error sending low stock alert: {str(e)}")


def send_daily_sales_summary():
    """
    Send daily sales summary (called by cron job)
    """
    try:
        from core.management.commands.send_daily_sms import Command
        command = Command()
        command.send_daily_summary(use_today=True)
    except Exception as e:
        logger.error(f"Error sending daily sales summary: {str(e)}")


def send_pricing_recommendations():
    """
    Send pricing recommendations (called by cron job)
    """
    try:
        from core.management.commands.send_pricing_recommendations import Command
        command = Command()
        command.send_pricing_recommendations(days=30)
    except Exception as e:
        logger.error(f"Error sending pricing recommendations: {str(e)}")


def send_low_stock_alerts():
    """
    Send low stock alerts (called by cron job)
    """
    try:
        from core.management.commands.send_low_stock_alerts import Command
        command = Command()
        command.send_low_stock_alerts(threshold=10)
    except Exception as e:
        logger.error(f"Error sending low stock alerts: {str(e)}")
