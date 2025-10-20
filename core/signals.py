from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from core.models import Sale, Product, AppUser
from core.sms_service import sms_service
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Sale)
def check_low_stock_after_sale(sender, instance, created, **kwargs):
    """
    Automatically check for low stock alerts after a sale is completed
    """
    if instance.status == 'completed':
        try:
            # Get the product and check if it's now low stock
            product = instance.product
            if product.stock <= 10 and product.status == 'active':
                # Send low stock alert
                send_low_stock_alert(product)
        except Exception as e:
            logger.error(f"Error checking low stock after sale: {str(e)}")


@receiver(post_save, sender=Product)
def check_low_stock_after_stock_update(sender, instance, created, **kwargs):
    """
    Automatically check for low stock alerts after stock is updated
    """
    if not created and instance.status == 'active':
        try:
            if instance.stock <= 10:
                # Send low stock alert
                send_low_stock_alert(instance)
        except Exception as e:
            logger.error(f"Error checking low stock after stock update: {str(e)}")


def send_low_stock_alert(product):
    """
    Send low stock alert for a specific product
    """
    try:
        admins = AppUser.objects.filter(role__iexact='admin').exclude(phone_number='')
        if not admins.exists():
            return
        
        # Format the alert message
        if product.stock == 0:
            message = f"🚨 StockWise Out of Stock Alert\n\n"
            message += f"Product: {product.name} ({product.size})\n"
            message += f"Status: OUT OF STOCK\n"
            message += f"Action: Restock immediately!\n\n"
        else:
            message = f"⚠️ StockWise Low Stock Alert\n\n"
            message += f"Product: {product.name} ({product.size})\n"
            message += f"Current Stock: {product.stock} boxes\n"
            message += f"Threshold: 10 boxes\n"
            message += f"Action: Consider restocking soon.\n\n"
        
        message += "📱 Sent by StockWise System"
        
        # Send SMS to all admins
        for admin in admins:
            result = sms_service.send_sms(admin.phone_number, message)
            if result['success']:
                logger.info(f"Low stock alert sent to {admin.username} at {admin.phone_number}")
            else:
                logger.error(f"Failed to send low stock alert to {admin.username}: {result['message']}")
                
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
