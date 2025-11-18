"""
Simple script to list all available COM ports
Run this to see what COM ports are available on your system
"""
import serial.tools.list_ports

print("=" * 60)
print("Available COM Ports on Your System")
print("=" * 60)
print()

ports = list(serial.tools.list_ports.comports())

if not ports:
    print("❌ No COM ports found.")
    print()
    print("This could mean:")
    print("1. Your printer is not connected via USB")
    print("2. Your printer is using a Windows printer driver (not USB-to-serial)")
    print("3. The USB-to-serial driver is not installed")
    print()
    print("Next steps:")
    print("- Check Device Manager → Ports (COM & LPT)")
    print("- Install USB-to-serial driver for your printer")
    print("- Check if printer appears in Print queues (Windows printer mode)")
else:
    print(f"Found {len(ports)} COM port(s):\n")
    
    for i, port in enumerate(ports, 1):
        print(f"{i}. {port.device}")
        print(f"   Description: {port.description}")
        if port.manufacturer:
            print(f"   Manufacturer: {port.manufacturer}")
        if port.vid and port.pid:
            print(f"   VID: {hex(port.vid)}, PID: {hex(port.pid)}")
        print()
    
    print("=" * 60)
    print("If you see your printer listed above, note the COM port number")
    print("(e.g., COM3, COM4) and use it in settings.py")
    print("=" * 60)


