# advertiser.py
import socket
import asyncio
from zeroconf import ServiceInfo
from zeroconf.asyncio import AsyncZeroconf

SERVICE_TYPE = "_sensee._tcp.local."
INSTANCE_NAME = "Sensee Smart Controller._sensee._tcp.local."
PORT = 8000

def get_ipv4_bytes():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No packets sent; forces OS to pick outbound interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return socket.inet_aton(ip)

async def main():
    azc = AsyncZeroconf()
    info = ServiceInfo(
        type_=SERVICE_TYPE,
        name=INSTANCE_NAME,
        port=PORT,
        addresses=[get_ipv4_bytes()],
        properties={"api": "v1", "web": "/", "video": "/video", "config": "/configuration"},
        server="sensee.local.",
    )

    await azc.async_register_service(info)
    ip_text = socket.inet_ntoa(info.addresses[0])
    print(f"✅ Advertised {INSTANCE_NAME} at {ip_text}:{PORT} ({SERVICE_TYPE})")
    print("   TXT:", {k: v for k, v in info.properties.items()})

    try:
        # Keep process alive (Ctrl+C to stop)
        await asyncio.Event().wait()
    finally:
        await azc.async_unregister_service(info)
        await azc.async_close()
        print("🛑 Service unregistered.")

if __name__ == "__main__":
    asyncio.run(main())
