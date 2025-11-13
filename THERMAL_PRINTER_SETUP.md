# Thermal Printer Setup Guide

This guide explains how to connect and configure your 58mm portable thermal printer (wireless USB & Bluetooth) to the StockWise system.

## Prerequisites

1. **Install Required Libraries**
   ```bash
   pip install -r requirements.txt
   ```
   This will install:
   - `python-escpos==3.1` - ESC/POS command library for thermal printers
   - `pyserial==3.5` - Serial communication library

2. **Install Printer Drivers**
   - Install the printer drivers provided by your manufacturer
   - For Windows: Check Device Manager after connecting the printer
   - For Linux: The printer should be auto-detected

## Connection Methods

### Option 1: USB Connection (Recommended)

**Steps:**
1. Connect the printer to your computer via USB
2. Wait for Windows to install drivers (check Device Manager)
3. Find the COM port assigned (e.g., COM3, COM4)
4. In Django settings (`stockwise_py/settings.py`), set:
   ```python
   THERMAL_PRINTER_TYPE = 'usb'  # or 'serial' for USB Serial
   THERMAL_PRINTER_PORT = 'COM3'  # Your COM port
   THERMAL_PRINTER_BAUDRATE = 9600  # Usually 9600 for thermal printers
   ```

**Finding USB Vendor/Product ID (if needed):**
- Windows: Open Device Manager → Find your printer → Properties → Details → Hardware Ids
- Look for VID_xxxx and PID_xxxx values
- Example: `VID_04F9&PID_2040` means vendor_id=0x04f9, product_id=0x2040

### Option 2: Bluetooth Connection

**Steps:**
1. Pair your printer with your computer via Bluetooth
2. In Windows, Bluetooth devices often create a virtual COM port
   - Settings → Devices → Bluetooth → Find your printer → More Bluetooth options
   - Check "COM Ports" tab to see assigned port (e.g., COM4, COM5)
3. In Django settings, set:
   ```python
   THERMAL_PRINTER_TYPE = 'bluetooth'
   THERMAL_PRINTER_PORT = 'COM4'  # The Bluetooth COM port
   THERMAL_PRINTER_BAUDRATE = 9600
   ```

**Note:** Some Bluetooth thermal printers require a specific pairing mode. Check your printer's manual.

### Option 3: Network Connection (If Supported)

If your printer has Wi-Fi/Ethernet capability:
```python
THERMAL_PRINTER_TYPE = 'network'
THERMAL_PRINTER_HOST = '192.168.1.100'  # Printer IP address
THERMAL_PRINTER_NETWORK_PORT = 9100  # Common raw printing port
```

## Configuration

### Method 1: Environment Variables (Recommended for Production)

Set these environment variables before running Django:
```bash
# Windows (PowerShell)
$env:THERMAL_PRINTER_TYPE="usb"
$env:THERMAL_PRINTER_PORT="COM3"
$env:THERMAL_PRINTER_BAUDRATE="9600"

# Linux/Mac
export THERMAL_PRINTER_TYPE=usb
export THERMAL_PRINTER_PORT=/dev/ttyUSB0
export THERMAL_PRINTER_BAUDRATE=9600
```

### Method 2: Django Settings File

Edit `stockwise_py/settings.py` directly:
```python
THERMAL_PRINTER_TYPE = 'usb'
THERMAL_PRINTER_PORT = 'COM3'
THERMAL_PRINTER_BAUDRATE = 9600
```

### Method 3: Frontend Configuration (Per-Session)

The frontend can also send printer settings with each print request. Settings are stored in browser localStorage:
```javascript
// In browser console
localStorage.setItem('thermalPrinterConnectionType', 'usb');
localStorage.setItem('thermalPrinterPort', 'COM3');
localStorage.setItem('thermalPrinterBaudrate', '9600');
```

## Testing the Printer

### Backend Test

1. **Test Printer Connection:**
   ```python
   python manage.py shell
   ```
   ```python
   from core.thermal_printer import get_printer_service
   
   # Test USB connection
   printer = get_printer_service(connection_type='usb')
   if printer:
       success = printer.test_print()
       print("Test print successful!" if success else "Test print failed")
       printer.close()
   ```

2. **Via API (if server is running):**
   - Make a POST request to `/api/printer/test/` with connection parameters

### Frontend Test

1. Go to Sales page
2. Find any completed sale
3. Click "Print Receipt"
4. Choose "OK" for thermal printer
5. The receipt should print

### Finding Available Ports

**Via API:**
```
GET /api/printer/ports/
```
Returns list of available COM ports with their details.

**Via Python:**
```python
import serial.tools.list_ports
for port in serial.tools.list_ports.comports():
    print(f"{port.device} - {port.description}")
```

## Common Issues and Solutions

### Issue: "Failed to connect to printer"

**Solutions:**
1. Check if printer is powered on
2. Verify COM port number (may change after reconnection)
3. Check if another program is using the printer
4. Try a different USB port
5. For Bluetooth: Re-pair the device

### Issue: "Permission denied" (Linux)

**Solution:**
```bash
sudo usermod -a -G dialout $USER
# Then logout and login again
```

### Issue: Printer prints garbled text

**Solutions:**
1. Check baudrate (try 9600, 19200, 38400, 115200)
2. Verify printer supports ESC/POS commands
3. Check printer's character encoding settings

### Issue: "python-escpos not installed"

**Solution:**
```bash
pip install python-escpos pyserial
```

### Issue: USB not detected

**Solutions:**
1. Check Device Manager (Windows) or `lsusb` (Linux)
2. Try different USB cable
3. Install manufacturer's drivers
4. Some printers need to be set to "USB" mode manually

## Printer-Specific Notes

### Common 58mm Thermal Printer Brands

- **Epson TM-T20/TM-T82**: Usually works with default USB settings
- **Star Micronics TSP100/TSP650**: May need specific drivers
- **Bixolon SRP-350**: Supports USB and Bluetooth well
- **Zjiang/ZJ-80**: Generic Chinese printers - usually works via Serial/USB

**Tip:** If your printer brand isn't listed, try:
1. USB connection with `connection_type='serial'` and appropriate COM port
2. Standard baudrate of 9600
3. Check printer manual for ESC/POS compatibility

## API Endpoints

### Print Receipt
```
POST /api/printer/receipt/<sale_id>/
Body:
  connection_type: usb|serial|bluetooth|network
  port: COM3 (for serial/bluetooth)
  baudrate: 9600 (for serial/bluetooth)
  vendor_id: 0x04f9 (optional, for USB)
  product_id: 0x2040 (optional, for USB)
  host: 192.168.1.100 (for network)
```

### Test Printer
```
POST /api/printer/test/
Body: (same as above)
```

### Get Available Ports
```
GET /api/printer/ports/
Response: { "success": true, "ports": [...] }
```

## Next Steps

1. Configure printer settings in `settings.py` or via environment variables
2. Test connection using the test endpoint
3. Print a receipt from the Sales page
4. Adjust settings as needed based on your printer model

For additional help, check:
- python-escpos documentation: https://github.com/python-escpos/python-escpos
- Your printer's manual for specific ESC/POS command support

