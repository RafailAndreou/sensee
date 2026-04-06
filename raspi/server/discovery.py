import socket
import json
import asyncio
import os
from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser, AsyncServiceInfo

SERVICE_TYPE = "_sensee._tcp.local."
_DISCOVERY_PORT = 54321
_DISCOVERY_TOKEN = "SENSEE_DISCOVER"

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    s.close()
    
    return ip, socket.inet_aton(ip)

async def register_mdns_service(port: int):
    """Register this server as sensee.local on the network."""
    ip_str, ip_bytes = get_local_ip()
    
    # Create service info
    info = AsyncServiceInfo(
        SERVICE_TYPE,
        "Sensee Server._sensee._tcp.local.",
        addresses=[ip_bytes],
        port=port,
        properties={"path": "/configuration", "ip": ip_str},
        server="sensee.local.",
    )
    
    zc = AsyncZeroconf()
    try:
        await zc.async_register_service(info)
        print(f"✅ mDNS service registered as sensee.local at {ip_str}:{port}")
        # Keep it registered (block indefinitely)
        await asyncio.Event().wait()
    except Exception as e:
        print(f"❌ Failed to register mDNS service: {e}")
    finally:
        await zc.async_unregister_service(info)
        await zc.async_close()
