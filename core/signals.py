from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from core.models import Sale, Product, AppUser
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
            # Reload the product from database to get updated stock
            product = Product.objects.get(product_id=instance.product_id)
            logger.info(f"Sale completed for product: {product.name}, Stock after: {product.stock}")
            if product.stock <= 10 and product.status.lower() == 'active':
                logger.info(f"Triggering low stock alert for {product.name} after sale")
                # Send low stock alert
                send_low_stock_alert(product)
            else:
                logger.info(f"Not triggering alert: stock={product.stock} > 10")
        except Exception as e:
            logger.error(f"Error checking low stock after sale: {str(e)}")


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
                # Send low stock alert
                send_low_stock_alert(instance)
            else:
                logger.info(f"Not triggering alert: stock={instance.stock} > 10 or status={instance.status}")
        except Exception as e:
            logger.error(f"Error checking low stock after stock update: {str(e)}")


def send_low_stock_alert(product):
    """
    Send REAL-TIME low stock alert for a specific product
    Prevents duplicate alerts for the same product within 5 minutes
    """
    try:
        # Check if we've already alerted for this product recently (within 5 minutes)
        now = timezone.now()
        product_key = f"{product.product_id}_{product.stock}"
        
        if product_key in _recently_alerted:
            last_alert_time = _recently_alerted[product_key]
            if now - last_alert_time < timedelta(minutes=5):
                logger.info(f"Skipping duplicate alert for {product.name} (last alerted {(now - last_alert_time).seconds}s ago)")
                return
        
        admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
        if not admins.exists():
            return
        
        # Format the alert message with proper spacing
        if product.stock == 0:
            message = f"STOCKWISE Stock Alert\n\n"
            message += f"CRITICAL - OUT OF STOCK:\n"
            message += f"- {product.name} ({product.size})\n\n"
            message += f"- STOCKWISE"
        else:
            box_text = "box" if product.stock == 1 else "boxes"
            message = f"STOCKWISE Stock Alert\n\n"
            message += f"WARNING - LOW STOCK:\n"
            message += f"- {product.name} ({product.size}): {product.stock} {box_text} left\n\n"
            message += f"- STOCKWISE"
        
        # Send SMS to all admins IMMEDIATELY (REAL-TIME)
        for admin in admins:
            result = sms_service.send_sms(admin.phone_number, message)
            if result['success']:
                logger.info(f"REAL-TIME low stock alert sent to {admin.username} at {admin.phone_number}")
            else:
                logger.error(f"Failed to send low stock alert to {admin.username}: {result['message']}")
        
        # Record that we've sent an alert for this product
        _recently_alerted[product_key] = now
        
        # Clean up old entries (older than 1 hour) to prevent memory bloat
        cleanup_time = now - timedelta(hours=1)
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
