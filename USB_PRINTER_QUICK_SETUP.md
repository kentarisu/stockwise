# Quick Setup: USB Thermal Printer

## Step-by-Step Guide

### 1. Connect Your Printer
- Plug your thermal printer into your computer via USB
- Wait for Windows to install drivers (check Device Manager if needed)
- Make sure the printer is powered on

### 2. Find Your Printer's COM Port

**Option A: Using the Setup Script (Easiest)**
```bash
python setup_thermal_printer.py
```
This script will:
- Detect all available COM ports
- Test each one to find your printer
- Show you the correct configuration

**Option B: Manual Method**
1. Open **Device Manager** (Win + X → Device Manager)
2. Expand "Ports (COM & LPT)"
3. Look for your printer (might show as "USB Serial Port", "CH340", "CP210x", or your printer brand)
4. Note the COM port number (e.g., COM3, COM4, COM5)

### 3. Configure the System

**Method 1: Edit Settings File (Recommended for Development)**
Edit `stockwise_py/settings.py`:
```python
THERMAL_PRINTER_TYPE = 'serial'  # Use 'serial' for USB printers that appear as COM ports
THERMAL_PRINTER_PORT = 'COM3'    # Replace with your COM port (e.g., COM3, COM4)
THERMAL_PRINTER_BAUDRATE = 9600  # Common values: 9600, 19200, 38400, 115200
```

**Method 2: Environment Variables (Recommended for Production)**
In PowerShell:
```powershell
$env:THERMAL_PRINTER_TYPE="serial"
$env:THERMAL_PRINTER_PORT="COM3"
$env:THERMAL_PRINTER_BAUDRATE="9600"
```

### 4. Test the Connection

**Option A: Using Python Shell**
```bash
python manage.py shell
```
```python
from core.thermal_printer import get_printer_service

printer = get_printer_service(connection_type='serial', port='COM3', baudrate=9600)
if printer:
    success = printer.test_print()
    printer.close()
    print("✅ Success!" if success else "❌ Failed")
```

**Option B: Using the Setup Script**
```bash
python setup_thermal_printer.py
```

### 5. Print a Receipt
1. Go to the Sales page in your StockWise application
2. Find a completed sale
3. Click "Print Receipt"
4. The receipt should print on your thermal printer

## Important Notes

### USB Connection Types
- **Most USB thermal printers** appear as **COM ports** on Windows
  - Use `connection_type='serial'` with the COM port
  - Example: `COM3`, `COM4`, `COM5`
  
- **Some printers** connect as direct USB devices (less common)
  - Use `connection_type='usb'` with vendor_id and product_id
  - Requires finding VID/PID from Device Manager

### Common Issues

**"Failed to connect to printer"**
- Check printer is powered on
- Verify COM port number (may change after reconnection)
- Make sure no other program is using the printer
- Try a different USB port

**"Permission denied" or "Access denied"**
- Close any other programs using the printer
- Try running as administrator (if needed)
- Check Windows printer settings

**Printer prints garbled text**
- Try different baudrates: 9600, 19200, 38400, 115200
- Check printer manual for correct baudrate
- Verify printer supports ESC/POS commands

**COM port not found**
- Reconnect USB cable
- Check Device Manager for the port
- Install printer drivers from manufacturer

## Finding the Right Baudrate

If 9600 doesn't work, try these common baudrates:
- 9600 (most common)
- 19200
- 38400
- 115200

The setup script will test all common baudrates automatically.

## Next Steps

Once configured, you can:
- Print receipts from the Sales page
- Test printing using the setup script
- Adjust settings in `settings.py` as needed

For more details, see `THERMAL_PRINTER_SETUP.md`


