# Finding Your POS58 Printer COM Port

## Current Situation
Your POS58 Printer is showing in Device Manager under "Print queues", but we need to find it as a COM port for direct communication.

## Steps to Find COM Port

### Method 1: Check "Ports (COM & LPT)" in Device Manager
1. In Device Manager, look for **"Ports (COM & LPT)"** section
2. Expand it to see all COM ports
3. Look for entries like:
   - "USB Serial Port (COMx)"
   - "CH340 (COMx)" 
   - "CP210x USB to UART Bridge (COMx)"
   - "POS58 Printer (COMx)"
   - Or any other USB serial device

### Method 2: Check Printer Properties
1. Right-click "POS58 Printer" in Device Manager
2. Go to **"Details"** tab
3. In the dropdown, select **"Hardware Ids"** or **"Device instance path"**
4. Look for COM port information

### Method 3: Check Printer Settings
1. Go to Windows Settings → Devices → Printers & scanners
2. Click on "POS58 Printer" → "Manage"
3. Check "Printer properties" → "Ports" tab
4. See if it shows a COM port

## If No COM Port is Found

Your printer might be using a Windows printer driver instead of a USB-to-serial driver. You have two options:

### Option A: Install USB-to-Serial Driver (Recommended)
1. Download the USB-to-serial driver for your printer model
2. Common drivers: CH340, CP210x, FTDI
3. Install the driver
4. The printer should then appear as a COM port

### Option B: Use Windows Printing (Alternative)
If your printer works as a Windows printer, we can configure it to use Windows print spooler instead of direct COM port access.

## Next Steps
Once you find the COM port (e.g., COM3, COM4), update `stockwise_py/settings.py`:
```python
THERMAL_PRINTER_TYPE = 'serial'
THERMAL_PRINTER_PORT = 'COM3'  # Your actual COM port
THERMAL_PRINTER_BAUDRATE = 9600
```

Then run the setup script again:
```bash
python setup_thermal_printer.py
```


