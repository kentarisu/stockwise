"""
Check for Windows printers and COM ports
"""
import sys
import os

# Try to import win32print for Windows printer detection
try:
    import win32print
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("Note: win32print not available. Install with: pip install pywin32")

import serial.tools.list_ports

print("=" * 60)
print("Checking for Printers and COM Ports")
print("=" * 60)
print()

# Check COM ports
print("COM Ports:")
print("-" * 60)
ports = list(serial.tools.list_ports.comports())
if ports:
    for port in ports:
        print(f"  {port.device}: {port.description}")
        if port.manufacturer:
            print(f"    Manufacturer: {port.manufacturer}")
else:
    print("  ❌ No COM ports found")
print()

# Check Windows printers
if WIN32_AVAILABLE:
    print("Windows Printers:")
    print("-" * 60)
    printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
    if printers:
        for printer in printers:
            print(f"  {printer[2]}")
            if 'POS58' in printer[2] or 'POS' in printer[2]:
                print(f"    ⭐ This might be your thermal printer!")
    else:
        print("  No local printers found")
else:
    print("Windows Printers:")
    print("-" * 60)
    print("  (Install pywin32 to list Windows printers)")
    print("  Run: pip install pywin32")

print()
print("=" * 60)
print("Next Steps:")
print("=" * 60)
if ports:
    print("✅ COM ports found! Use one of these in settings.py:")
    print(f"   THERMAL_PRINTER_TYPE = 'serial'")
    print(f"   THERMAL_PRINTER_PORT = '{ports[0].device}'")
else:
    print("❌ No COM ports found.")
    print("   If you installed the USB-to-serial driver:")
    print("   1. Unplug and replug the USB cable")
    print("   2. Check Device Manager → Ports (COM & LPT)")
    print("   3. Restart your computer if needed")
    print()
    print("   Or use Windows printing mode:")
    print("   THERMAL_PRINTER_TYPE = 'windows'")
    print("   THERMAL_PRINTER_NAME = 'POS58 Printer'")


