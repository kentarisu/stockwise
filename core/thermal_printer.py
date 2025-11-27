"""
Thermal Printer Service for 58mm Receipt Printing
Supports USB and Bluetooth connections via ESC/POS commands
"""
import logging
import io
import os
import time
import textwrap
from typing import Optional, Dict, List, Any
from decimal import Decimal
from PIL import Image

logger = logging.getLogger(__name__)

LINE_WIDTH = 32
DESC_WIDTH = 18
QTY_WIDTH = 4
AMOUNT_WIDTH = LINE_WIDTH - DESC_WIDTH - QTY_WIDTH


def format_line(left: str = "", right: str = "") -> str:
    """Return a left/right aligned line within LINE_WIDTH characters."""
    left = (left or "").strip()
    right = (right or "").strip()
    available = LINE_WIDTH - len(right)
    if available <= 0:
        return right.rjust(LINE_WIDTH)
    return f"{left[:available].ljust(available)}{right.rjust(len(right))}"


def wrap_text(text: str, width: int = LINE_WIDTH) -> List[str]:
    """Wrap text to fit within the specified width."""
    if not text:
        return []
    return textwrap.wrap(text.strip(), width=width) or [text[:width]]

try:
    from escpos.printer import Usb, Serial, Network, File
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
            connection_type: 'usb', 'serial', 'bluetooth', 'network', or 'windows'
            **kwargs: Connection parameters (port, baudrate, printer_name, etc.)
        """
        self.connection_type = connection_type.lower()
        self.printer = None
        self.connected = False
        self.last_error = None
        self.last_error = None
        
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
                
            elif self.connection_type == 'windows':
                printer_name = kwargs.get('printer_name', 'POS58 Printer')
                import tempfile
                import platform
                if platform.system() != 'Windows':
                    raise EnvironmentError("Windows printer type is only supported on Windows hosts")
                self._temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.prn')
                self._temp_file_path = self._temp_file.name
                self._temp_file.close()
                self.printer = File(devfile=self._temp_file_path)
                self._printer_name = printer_name
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
        self.last_error = None
        
        if not self.connected or not self.printer:
            logger.error("Printer not connected")
            self.last_error = "Printer not connected"
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
            self.printer.text(f"{company_name[:LINE_WIDTH].center(LINE_WIDTH)}\n")
            
            self.printer.set(bold=False, font='a')
            company_address = receipt_data.get('company_address', 'Mabini Street - Libertad, Bacolod City')
            for line in wrap_text(company_address, width=LINE_WIDTH):
                self.printer.text(f"{line.center(LINE_WIDTH)}\n")
            
            company_phone = receipt_data.get('company_phone', '')
            if company_phone:
                self.printer.text(f"{('Tel: ' + company_phone)[:LINE_WIDTH].center(LINE_WIDTH)}\n")
            
            self.printer.text("=" * LINE_WIDTH + "\n")
            
            # ===== TITLE =====
            self.printer.set(bold=True, align='center')
            self.printer.text("SALES RECEIPT\n")
            self.printer.text("=" * LINE_WIDTH + "\n")
            
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
            
            self.printer.text("-" * LINE_WIDTH + "\n")
            
            # ===== CUSTOMER INFO =====
            customer_name = receipt_data.get('customer_name')
            self.printer.text(f"Customer: {' ' if not customer_name or customer_name == 'N/A' else customer_name}\n")
            
            customer_contact = receipt_data.get('customer_contact', '')
            self.printer.text(f"Contact: {customer_contact if customer_contact and customer_contact != 'N/A' else ''}\n")
            
            customer_address = receipt_data.get('customer_address', '')
            if customer_address and customer_address != 'N/A':
                wrapped_address = wrap_text(customer_address, width=LINE_WIDTH - 10)
                for idx, line in enumerate(wrapped_address):
                    label = "Address: " if idx == 0 else "          "
                    self.printer.text(f"{label}{line}\n")
            else:
                self.printer.text("Address:\n")
            
            self.printer.text("-" * LINE_WIDTH + "\n")
            
            # ===== ITEMS TABLE =====
            items = receipt_data.get('items', [])
            if items:
                # Table header
                self.printer.set(bold=True)
                self.printer.text(f"{'Description':<{DESC_WIDTH}}{'Qty':>{QTY_WIDTH}}{'Amount':>{AMOUNT_WIDTH}}\n")
                self.printer.set(bold=False)
                self.printer.text("-" * LINE_WIDTH + "\n")
                
                # Items
                for item in items:
                    name = item.get('name', '').strip()
                    if not name:
                        name = 'Item'
                    name_lines = wrap_text(name, width=DESC_WIDTH)
                    first_line = name_lines[0]
                    remaining_lines = name_lines[1:]
                    
                    quantity = int(item.get('quantity', 0))
                    price = float(item.get('price', 0))
                    amount = float(item.get('amount', 0))
                    
                    amount_str = f"{amount:,.2f}"
                    
                    # Product name (with wrapping)
                    self.printer.text(
                        f"{first_line:<{DESC_WIDTH}}{str(quantity):>{QTY_WIDTH}}{amount_str:>{AMOUNT_WIDTH}}\n"
                    )
                    for line in remaining_lines:
                        self.printer.text(f"{line:<{LINE_WIDTH}}\n")
                    
                    # Price and amount
                    price_str = f"@ {price:,.2f}"
                    self.printer.text(format_line("", price_str) + "\n")
            
            self.printer.text("=" * LINE_WIDTH + "\n")
            
            # ===== TOTALS =====
            subtotal = float(receipt_data.get('subtotal', 0))
            vat = float(receipt_data.get('vat', 0))
            total = float(receipt_data.get('total', 0))
            amount_paid = float(receipt_data.get('amount_paid', 0))
            change = float(receipt_data.get('change', 0))
            discount = float(receipt_data.get('discount', 0))
            discount_pct = float(receipt_data.get('discount_pct', 0))
            
            self.printer.text(format_line("Subtotal:", f"{subtotal:,.2f}") + "\n")
            if vat > 0:
                self.printer.text(format_line("VAT 12%:", f"{vat:,.2f}") + "\n")
            if discount > 0:
                pct_raw = f"{discount_pct:.2f}" if discount_pct > 0 else ""
                pct_clean = pct_raw.rstrip('0').rstrip('.') if pct_raw else ""
                pct_label = f" ({pct_clean}%)" if pct_clean else ""
                self.printer.text(format_line(f"Discount{pct_label}:", f"-{discount:,.2f}") + "\n")
            
            self.printer.set(bold=True)
            self.printer.text(format_line("TOTAL:", f"{total:,.2f}") + "\n")
            self.printer.set(bold=False)
            
            self.printer.text("-" * LINE_WIDTH + "\n")
            self.printer.text(format_line("Amount Paid:", f"{amount_paid:,.2f}") + "\n")
            self.printer.text(format_line("Change:", f"{change:,.2f}") + "\n")
            
            # ===== FOOTER =====
            self.printer.text("=" * 32 + "\n")
            self.printer.set(align='center')
            self.printer.text("Thank you for your purchase!\n")
            self.printer.text("This is not an official receipt.\n")
            
            # Add a single blank line before cutting
            self.printer.text("\n")
            
            # For Windows printing, add proper termination commands
            if self.connection_type == 'windows':
                # Send a partial cut to finish the receipt cleanly
                try:
                    self.printer._raw(b'\x1d\x56\x00')
                except:
                    pass
            else:
                # For direct connections, use full cut
                self.printer.cut()
            
            # Close connection and flush - CRITICAL for Windows printing
            try:
                if hasattr(self.printer, 'flush'):
                    self.printer.flush()
                # Force flush the underlying file if it exists
                if hasattr(self.printer, 'devfile') and hasattr(self.printer.devfile, 'flush'):
                    self.printer.devfile.flush()
            except:
                pass
            
            # Close the file/connection
            self.printer.close()
            
            if self.connection_type == 'windows':
                if not self._send_windows_job():
                    return False
            
            logger.info(f"Successfully printed receipt: {transaction_number}")
            return True
            
        except EscposError as e:
            logger.error(f"ESC/POS error while printing: {e}")
            self.last_error = str(e)
            return False
        except Exception as e:
            logger.error(f"Unexpected error while printing: {e}")
            self.last_error = str(e)
            return False
        finally:
            # Try to close connection
            try:
                if self.printer:
                    self.printer.close()
            except:
                pass
    
    def print_qr_sticker(self, sticker_data: Dict[str, Any]) -> bool:
        """
        Print a QR code sticker with product details.
        
        sticker_data keys:
            - product_name
            - variant
            - quantity
            - qr_image_bytes (PNG bytes)
        """
        if not self.connected or not self.printer:
            logger.error("Printer not connected")
            self.last_error = "Printer not connected"
            return False
        
        try:
            self.printer.set(align='center', bold=True, width=2, height=2)
            self.printer.text(f"{sticker_data.get('product_name', 'Product')}\n")
            
            self.printer.set(width=1, height=1, bold=False)
            variant = sticker_data.get('variant')
            if variant:
                self.printer.text(f"Variant: {variant}\n")
            
            quantity = sticker_data.get('quantity')
            if quantity:
                self.printer.text(f"Quantity: {quantity}\n")
            
            self.printer.text("-" * 32 + "\n")
            
            # Print QR image if provided
            qr_bytes = sticker_data.get('qr_image_bytes')
            if qr_bytes:
                try:
                    image = Image.open(io.BytesIO(qr_bytes))
                    self.printer.set(align='center')
                    self.printer.image(image, impl="bitImageRaster")
                except Exception as e:
                    logger.warning(f"Failed to print QR image: {e}")
                    self.last_error = f"Failed to print QR image: {e}"
            
            self.printer.text("\n")
            self.printer.text("Scan to record sale or add stock\n")
            self.printer.text("STOCKWISE\n")
            self.printer.text("\n")
            
            # Cut/finish
            if self.connection_type == 'windows':
                try:
                    self.printer._raw(b'\x1d\x56\x00')
                except:
                    pass
            else:
                self.printer.cut()
            
            # Flush/close similar to receipt
            try:
                if hasattr(self.printer, 'flush'):
                    self.printer.flush()
                if hasattr(self.printer, 'devfile') and hasattr(self.printer.devfile, 'flush'):
                    self.printer.devfile.flush()
            except:
                pass
            
            self.printer.close()
            
            if self.connection_type == 'windows':
                return False if not self._send_windows_job() else True
            
            return True
        except Exception as e:
            logger.error(f"Error printing QR sticker: {e}")
            self.last_error = str(e)
            return False
        finally:
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
    
    def _send_windows_job(self) -> bool:
        """Helper to send buffered print job when using Windows spooler"""
        windows_success = False
        if self.connection_type == 'windows' and hasattr(self, '_temp_file_path') and self._temp_file_path:
            windows_success = False
            try:
                import os
                import time
                time.sleep(0.2)
                if os.path.exists(self._temp_file_path):
                    with open(self._temp_file_path, 'rb') as f:
                        raw_data = f.read()
                    if raw_data:
                        try:
                            try:
                                import win32print
                            except ImportError:
                                self.last_error = "pywin32 is not installed. Run 'pip install pywin32'."
                                raise
                            printer_name = self._printer_name or win32print.GetDefaultPrinter()
                            handle = win32print.OpenPrinter(printer_name)
                            try:
                                info = win32print.GetPrinter(handle, 2)
                                status_flags = info.get('Status', 0)
                                offline_status = getattr(win32print, 'PRINTER_STATUS_OFFLINE', 0x80)
                                error_status = getattr(win32print, 'PRINTER_STATUS_ERROR', 0x02)
                                paused_status = getattr(win32print, 'PRINTER_STATUS_PAUSED', 0x01)
                                paper_out_status = getattr(win32print, 'PRINTER_STATUS_OUT_OF_PAPER', 0x40)
                                work_offline_attr = getattr(win32print, 'PRINTER_ATTRIBUTE_WORK_OFFLINE', 0x400)
                                if status_flags & (offline_status | error_status | paused_status | paper_out_status):
                                    self.last_error = f"Printer '{printer_name}' is offline or unavailable. Please check the device."
                                    windows_success = False
                                elif info.get('Attributes', 0) & work_offline_attr:
                                    self.last_error = f"Printer '{printer_name}' is set to work offline. Please connect it to this device."
                                    windows_success = False
                                else:
                                    job_id = win32print.StartDocPrinter(handle, 1, ("StockWise Print", None, "RAW"))
                                    win32print.StartPagePrinter(handle)
                                    win32print.WritePrinter(handle, raw_data)
                                    win32print.EndPagePrinter(handle)
                                    win32print.EndDocPrinter(handle)
                                    time.sleep(0.2)
                                    try:
                                        job_info = win32print.GetJob(handle, job_id, 1)
                                        job_status = job_info.get('Status', 0)
                                        job_error_flags = (
                                            getattr(win32print, 'JOB_STATUS_ERROR', 0x0002) |
                                            getattr(win32print, 'JOB_STATUS_OFFLINE', 0x0010) |
                                            getattr(win32print, 'JOB_STATUS_PAPEROUT', 0x0020) |
                                            getattr(win32print, 'JOB_STATUS_BLOCKED_DEVQ', 0x2000) |
                                            getattr(win32print, 'JOB_STATUS_RESTART', 0x0008)
                                        )
                                        if job_status & job_error_flags:
                                            self.last_error = f"Printer '{printer_name}' reported an error. Please check the device status."
                                            windows_success = False
                                        else:
                                            windows_success = True
                                    except Exception:
                                        windows_success = True
                            finally:
                                win32print.ClosePrinter(handle)
                        except Exception as win_err:
                            logger.warning(f"win32print failed: {win_err}")
                            self.last_error = f"Windows printing error: {win_err}"
                            windows_success = False
                    else:
                        logger.warning("Windows print file empty; skipping job")
                        self.last_error = "Generated print file was empty."
                try:
                    if os.path.exists(self._temp_file_path):
                        os.unlink(self._temp_file_path)
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Error in Windows print job handling: {e}")
                if not self.last_error:
                    self.last_error = f"Windows print job failed: {e}"
                windows_success = False
        else:
            self.last_error = self.last_error or "Windows spooler job unavailable on this host"
            windows_success = False
        return windows_success
    
    def close(self):
        """Close printer connection"""
        try:
            if self.printer:
                # Flush before closing
                if hasattr(self.printer, 'flush'):
                    self.printer.flush()
                self.printer.close()
            
            # Clean up temp file if it exists
            if hasattr(self, '_temp_file_path') and self._temp_file_path:
                try:
                    import os
                    if os.path.exists(self._temp_file_path):
                        os.unlink(self._temp_file_path)
                except:
                    pass
            
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
