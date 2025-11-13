"""
Thermal Printer Service for 58mm Receipt Printing
Supports USB and Bluetooth connections via ESC/POS commands
"""
import logging
from typing import Optional, Dict, List, Any
from decimal import Decimal

logger = logging.getLogger(__name__)

try:
    from escpos.printer import Usb, Serial, Network
    from escpos.exceptions import Error as EscposError
    ESCPOS_AVAILABLE = True
except ImportError:
    ESCPOS_AVAILABLE = False
    logger.warning("python-escpos not installed. Thermal printing will not work.")


class ThermalPrinterService:
    """Service for connecting to and printing to 58mm thermal printers"""
    
    def __init__(self, connection_type: str = 'usb', **kwargs):
        """
        Initialize printer connection
        
        Args:
            connection_type: 'usb', 'serial', 'bluetooth', or 'network'
            **kwargs: Connection parameters (port, baudrate, etc.)
        """
        self.connection_type = connection_type.lower()
        self.printer = None
        self.connected = False
        
        if not ESCPOS_AVAILABLE:
            raise ImportError("python-escpos library not installed. Install with: pip install python-escpos")
        
        self._connect(**kwargs)
    
    def _connect(self, **kwargs):
        """Establish connection to printer based on connection type"""
        try:
            if self.connection_type == 'usb':
                # USB connection - need vendor_id and product_id
                vendor_id = kwargs.get('vendor_id', 0x04f9)  # Default Brother printer (common)
                product_id = kwargs.get('product_id', 0x2040)
                self.printer = Usb(vendor_id, product_id)
                
            elif self.connection_type == 'serial':
                # Serial/USB Serial connection
                port = kwargs.get('port', 'COM3')  # Windows default
                baudrate = kwargs.get('baudrate', 9600)
                self.printer = Serial(port, baudrate=baudrate)
                
            elif self.connection_type == 'bluetooth':
                # Bluetooth via Serial (RFCOMM)
                port = kwargs.get('port', 'COM4')  # Common BT serial port on Windows
                baudrate = kwargs.get('baudrate', 9600)
                self.printer = Serial(port, baudrate=baudrate)
                
            elif self.connection_type == 'network':
                # Network printer (if printer has network interface)
                host = kwargs.get('host', '192.168.1.100')
                port = kwargs.get('port', 9100)
                self.printer = Network(host, port=port)
            else:
                raise ValueError(f"Unsupported connection type: {self.connection_type}")
            
            self.connected = True
            logger.info(f"Successfully connected to printer via {self.connection_type}")
            
        except EscposError as e:
            logger.error(f"Failed to connect to printer: {e}")
            self.connected = False
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to printer: {e}")
            self.connected = False
            raise
    
    def print_receipt(self, receipt_data: Dict[str, Any]) -> bool:
        """
        Print a formatted receipt
        
        Args:
            receipt_data: Dictionary containing receipt information:
                - company_name: str
                - company_address: str
                - company_phone: str
                - transaction_number: str
                - or_number: str
                - date: str
                - customer_name: str
                - customer_contact: str
                - customer_address: str
                - items: List[Dict] with keys: name, quantity, price, amount, batch_ids
                - subtotal: Decimal/float
                - vat: Decimal/float
                - total: Decimal/float
                - amount_paid: Decimal/float
                - change: Decimal/float
                - processed_by: str (optional)
        
        Returns:
            bool: True if print successful, False otherwise
        """
        if not self.connected or not self.printer:
            logger.error("Printer not connected")
            return False
        
        try:
            # Initialize printer
            self.printer.set(
                align='center',
                font='a',
                width=1,
                height=1,
                bold=True,
                double_height=False,
                double_width=False
            )
            
            # ===== HEADER =====
            self.printer.text("\n")
            self.printer.set(bold=True, align='center')
            company_name = receipt_data.get('company_name', 'FruitMaster Marketing')
            self.printer.text(f"{company_name}\n")
            
            self.printer.set(bold=False, font='a')
            company_address = receipt_data.get('company_address', 'Mabini Street - Libertad, Bacolod City')
            if company_address:
                self.printer.text(f"{company_address}\n")
            
            company_phone = receipt_data.get('company_phone', '')
            if company_phone:
                self.printer.text(f"Tel: {company_phone}\n")
            
            self.printer.text("=" * 32 + "\n")
            
            # ===== TITLE =====
            self.printer.set(bold=True, align='center')
            self.printer.text("SALES RECEIPT\n")
            self.printer.text("=" * 32 + "\n")
            
            # ===== TRANSACTION INFO =====
            self.printer.set(bold=False, align='left')
            transaction_number = receipt_data.get('transaction_number', 'N/A')
            self.printer.text(f"Transaction No.: {transaction_number}\n")
            
            or_number = receipt_data.get('or_number', 'N/A')
            self.printer.text(f"OR No.: {or_number}\n")
            
            date = receipt_data.get('date', 'N/A')
            self.printer.text(f"Date: {date}\n")
            
            processed_by = receipt_data.get('processed_by')
            if processed_by:
                self.printer.text(f"Processed by: {processed_by}\n")
            
            self.printer.text("-" * 32 + "\n")
            
            # ===== CUSTOMER INFO =====
            customer_name = receipt_data.get('customer_name', 'Walk-in Customer')
            self.printer.text(f"Customer: {customer_name}\n")
            
            customer_contact = receipt_data.get('customer_contact', '')
            if customer_contact and customer_contact != 'N/A':
                self.printer.text(f"Contact: {customer_contact}\n")
            
            customer_address = receipt_data.get('customer_address', '')
            if customer_address and customer_address != 'N/A':
                # Truncate long addresses for 58mm width
                addr = customer_address[:30] if len(customer_address) > 30 else customer_address
                self.printer.text(f"Address: {addr}\n")
            
            self.printer.text("-" * 32 + "\n")
            
            # ===== ITEMS TABLE =====
            items = receipt_data.get('items', [])
            if items:
                # Table header
                self.printer.set(bold=True)
                self.printer.text(f"{'Description':<18} {'Qty':>4} {'Amount':>10}\n")
                self.printer.set(bold=False)
                self.printer.text("-" * 32 + "\n")
                
                # Items
                for item in items:
                    name = item.get('name', '')
                    # Truncate product name if too long
                    if len(name) > 18:
                        name = name[:15] + "..."
                    
                    quantity = int(item.get('quantity', 0))
                    price = float(item.get('price', 0))
                    amount = float(item.get('amount', 0))
                    
                    # Product name (with line break if needed for batch IDs)
                    self.printer.text(f"{name:<18} {quantity:>4}\n")
                    
                    # Batch IDs on next line (if available)
                    batch_ids = item.get('batch_ids', [])
                    if batch_ids:
                        batch_str = ', '.join([str(b) for b in batch_ids[:3]])  # Max 3 batch IDs
                        if len(batch_ids) > 3:
                            batch_str += "..."
                        self.printer.set(font='b')  # Smaller font for batch IDs
                        self.printer.text(f"  Batch: {batch_str}\n")
                        self.printer.set(font='a')
                    
                    # Price and amount
                    self.printer.text(f"  @{price:>8.2f} {amount:>10.2f}\n")
            
            self.printer.text("=" * 32 + "\n")
            
            # ===== TOTALS =====
            subtotal = float(receipt_data.get('subtotal', 0))
            vat = float(receipt_data.get('vat', 0))
            total = float(receipt_data.get('total', 0))
            amount_paid = float(receipt_data.get('amount_paid', 0))
            change = float(receipt_data.get('change', 0))
            
            self.printer.text(f"{'Subtotal:':<20} {subtotal:>10.2f}\n")
            if vat > 0:
                self.printer.text(f"{'VAT 12%:':<20} {vat:>10.2f}\n")
            
            self.printer.set(bold=True)
            self.printer.text(f"{'TOTAL:':<20} {total:>10.2f}\n")
            self.printer.set(bold=False)
            
            self.printer.text("-" * 32 + "\n")
            self.printer.text(f"{'Amount Paid:':<20} {amount_paid:>10.2f}\n")
            if change > 0:
                self.printer.text(f"{'Change:':<20} {change:>10.2f}\n")
            
            # ===== FOOTER =====
            self.printer.text("=" * 32 + "\n")
            self.printer.set(align='center')
            self.printer.text("Thank you for your purchase!\n")
            self.printer.text("This serves as your Official Receipt.\n")
            
            # Add some blank lines and cut paper
            self.printer.text("\n\n\n")
            self.printer.cut()
            
            # Close connection
            self.printer.close()
            
            logger.info(f"Successfully printed receipt: {transaction_number}")
            return True
            
        except EscposError as e:
            logger.error(f"ESC/POS error while printing: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while printing: {e}")
            return False
        finally:
            # Try to close connection
            try:
                if self.printer:
                    self.printer.close()
            except:
                pass
    
    def test_print(self) -> bool:
        """Print a test receipt to verify printer connection"""
        test_data = {
            'company_name': 'StockWise Test',
            'company_address': 'Test Address',
            'transaction_number': 'TEST001',
            'or_number': 'OR001',
            'date': '2025-01-01 12:00',
            'customer_name': 'Test Customer',
            'items': [
                {'name': 'Test Product', 'quantity': 1, 'price': 100.00, 'amount': 100.00}
            ],
            'subtotal': 100.00,
            'vat': 12.00,
            'total': 112.00,
            'amount_paid': 112.00,
            'change': 0.00
        }
        return self.print_receipt(test_data)
    
    def close(self):
        """Close printer connection"""
        try:
            if self.printer:
                self.printer.close()
            self.connected = False
        except:
            pass


def get_printer_service(connection_type: str = None, **kwargs) -> Optional[ThermalPrinterService]:
    """
    Factory function to create a printer service instance
    
    Args:
        connection_type: 'usb', 'serial', 'bluetooth', or 'network'
        **kwargs: Connection parameters
    
    Returns:
        ThermalPrinterService instance or None if connection fails
    """
    if not ESCPOS_AVAILABLE:
        logger.error("python-escpos library not available")
        return None
    
    # Get default connection type from settings or use provided
    from django.conf import settings
    default_connection = getattr(settings, 'THERMAL_PRINTER_TYPE', 'usb')
    connection_type = connection_type or default_connection
    
    try:
        return ThermalPrinterService(connection_type=connection_type, **kwargs)
    except Exception as e:
        logger.error(f"Failed to initialize printer service: {e}")
        return None

