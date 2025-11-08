"""
Test script to verify mDNS/Bonjour and network connectivity.
Run this to diagnose connectivity issues.
"""
import socket
import sys

def get_local_ip():
    """Get the local IP address of this machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def test_port_binding():
    """Test if we can bind to port 8000."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", 8000))
        sock.close()
        return True, "Port 8000 is available"
    except Exception as e:
        return False, f"Cannot bind to port 8000: {e}"

def test_mdns_resolve():
    """Test if sensee.local can be resolved."""
    try:
        ip = socket.gethostbyname("sensee.local")
        return True, f"sensee.local resolves to {ip}"
    except Exception as e:
        return False, f"Cannot resolve sensee.local: {e}"

def test_zeroconf():
    """Test if zeroconf package is available."""
    try:
        import zeroconf
        return True, f"zeroconf {zeroconf.__version__} is installed"
    except ImportError as e:
        return False, f"zeroconf not installed: {e}"

def main():
    print("=" * 60)
    print("Sensee Network Diagnostics")
    print("=" * 60)
    print()
    
    # Get local IP
    local_ip = get_local_ip()
    print(f"✅ Local IP Address: {local_ip}")
    print(f"   Use this to connect: http://{local_ip}:8000")
    print()
    
    # Test port binding
    success, msg = test_port_binding()
    print(f"{'✅' if success else '❌'} Port 8000: {msg}")
    print()
    
    # Test zeroconf
    success, msg = test_zeroconf()
    print(f"{'✅' if success else '❌'} Zeroconf Package: {msg}")
    if not success:
        print("   → Install: pip install zeroconf")
    print()
    
    # Test mDNS resolution
    success, msg = test_mdns_resolve()
    print(f"{'✅' if success else '❌'} mDNS Resolution: {msg}")
    if not success:
        print("   → .local domains require Bonjour on Windows")
        print("   → Download: https://support.apple.com/kb/DL999")
        print("   → Or use IP address directly instead")
    print()
    
    # Test if we're on Windows
    if sys.platform == "win32":
        print("ℹ️  Windows Detected:")
        print("   • Bonjour is required for .local domain support")
        print("   • Install from: https://support.apple.com/kb/DL999")
        print("   • Or use direct IP address instead")
        print()
    
    # Network info
    print("=" * 60)
    print("Connection Methods:")
    print("=" * 60)
    print(f"1. Direct IP:  http://{local_ip}:8000")
    print(f"2. mDNS:       http://sensee.local:8000 {'(requires Bonjour)' if not test_mdns_resolve()[0] else ''}")
    print(f"3. UDP Discovery: Port 54321 (if enabled)")
    print()
    
    print("=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. If mDNS fails but IP works → Install Bonjour (optional)")
    print("2. Start server: python -m server.main")
    print(f"3. Connect from other devices using: http://{local_ip}:8000")
    print("=" * 60)

if __name__ == "__main__":
    main()
