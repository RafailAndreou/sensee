# discover.py
import socket
import asyncio
from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser

SERVICE_TYPE = "_sensee._tcp.local."

class Listener:
    def __init__(self):
        self.found = {}

    async def add_service(self, zc: AsyncZeroconf, type_: str, name: str) -> None:
        info = await zc.async_get_service_info(type_, name, timeout=2000)
        if not info:
            print(f"⚠️ Discovered {name} but could not resolve yet.")
            return
        ips = [socket.inet_ntoa(a) for a in info.addresses]
        props = {k.decode(): v.decode() for k, v in info.properties.items()}
        self.found[name] = {"ips": ips, "port": info.port, "props": props}
        print("✅ Service found:")
        print(f"   Name: {name}")
        print(f"   IPs:  {ips}")
        print(f"   Port: {info.port}")
        print(f"   TXT:  {props}")

    async def remove_service(self, _zc, _type, name):
        print(f"❌ Service removed: {name}")
        self.found.pop(name, None)

async def main():
    zc = AsyncZeroconf()
    listener = Listener()
    browser = AsyncServiceBrowser(zc.zeroconf, SERVICE_TYPE, handlers=[listener.add_service, listener.remove_service])
    try:
        # Listen for a few seconds, then print a snapshot
        await asyncio.sleep(5)
        print("\n📦 Snapshot:")
        for name, data in listener.found.items():
            print(f"- {name} @ {data['ips']}:{data['port']} TXT={data['props']}")
        # Keep running if you want continuous discovery:
        # await asyncio.Event().wait()
    finally:
        await browser.async_cancel()
        await zc.async_close()

if __name__ == "__main__":
    asyncio.run(main())
    