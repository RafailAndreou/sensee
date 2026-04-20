import asyncio
import json
import socket
from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser, AsyncServiceInfo

SERVICE_TYPE = "_sensee._tcp.local."
_DISCOVERY_PORT = 54321
_DISCOVERY_TOKEN = "SENSEE_DISCOVER"


class _DiscoveryResponder(asyncio.DatagramProtocol):
    def __init__(self, port: int):
        self.port = port
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        try:
            message = data.decode("utf-8").strip()
        except Exception:
            return

        if message != _DISCOVERY_TOKEN or self.transport is None:
            return

        ip_str, _ = get_local_ip()
        payload = json.dumps({"ip": ip_str, "port": self.port, "path": "/configuration"}).encode("utf-8")
        self.transport.sendto(payload, addr)

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


async def start_udp_discovery_service(port: int):
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: _DiscoveryResponder(port),
        local_addr=("0.0.0.0", _DISCOVERY_PORT),
        allow_broadcast=True,
    )
    print(f"✅ UDP discovery listening on port {_DISCOVERY_PORT}")
    try:
        await asyncio.Event().wait()
    finally:
        transport.close()
