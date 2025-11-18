# Windows Printer Setup for POS58 Printer

Since your POS58 Printer appears in Device Manager under "Print queues" (not as a COM port), you can use **Windows printing mode** which works with your current setup.

## Quick Setup

### Step 1: Configure Settings

Edit `stockwise_py/settings.py` and set:

```python
THERMAL_PRINTER_TYPE = 'windows'
THERMAL_PRINTER_NAME = 'POS58 Printer'  # Must match exactly as shown in Device Manager
```

Or set environment variables:
```powershell
$env:THERMAL_PRINTER_TYPE="windows"
$env:THERMAL_PRINTER_NAME="POS58 Printer"
```

### Step 2: Verify Printer Name

Make sure the printer name matches exactly:
1. Open Windows Settings → Devices → Printers & scanners
2. Find "POS58 Printer" 
3. The name must match exactly (case-sensitive)

### Step 3: Test the Connection

```bash
python manage.py shell
```

```python
from core.thermal_printer import get_printer_service

printer = get_printer_service(connection_type='windows', printer_name='POS58 Printer')
if printer:
    success = printer.test_print()
    printer.close()
    print("✅ Success!" if success else "❌ Failed")
```

## Alternative: If COM Port Appears Later

If you later see a COM port in Device Manager → Ports (COM & LPT), you can switch to serial mode:

```python
THERMAL_PRINTER_TYPE = 'serial'
THERMAL_PRINTER_PORT = 'COM3'  # Your actual COM port
THERMAL_PRINTER_BAUDRATE = 9600
```

## Troubleshooting

**If Windows printing doesn't work:**
1. Make sure the printer name matches exactly (check Windows Settings)
2. Ensure the printer is set as default or available
3. Try unplugging and replugging the USB cable
4. Check if the printer appears in Windows Printers & scanners


