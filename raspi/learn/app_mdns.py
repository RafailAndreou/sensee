# app_mdns.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from zeroconf import ServiceInfo
from zeroconf.asyncio import AsyncZeroconf
import socket
import uvicorn

SERVICE_TYPE = "_sensee._tcp.local."
INSTANCE_NAME = "Sensee Smart Controller._sensee._tcp.local."
PORT = 8000

def get_ipv4_bytes():
    """Return active LAN IPv4 as 4 bytes (network order), fallback to 127.0.0.1."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # forces OS to pick outbound iface/IP; no packets sent
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return socket.inet_aton(ip)

# Prepare the ServiceInfo (same as sync)
service_info = ServiceInfo(
    type_=SERVICE_TYPE,
    name=INSTANCE_NAME,
    port=PORT,
    addresses=[get_ipv4_bytes()],
    properties={
        "api": "v1",
        "web": "/",
        "video": "/video",
        "config": "/configuration",
    },
    server="sensee.local.",  # optional label
)

azc: AsyncZeroconf | None = None  # will be created in lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    global azc
    azc = AsyncZeroconf()
    # async register/unregister avoids EventLoopBlocked
    await azc.async_register_service(service_info)
    print(
        "mDNS: registered",
        socket.inet_ntoa(service_info.addresses[0]),
        PORT,
        SERVICE_TYPE,
    )
    try:
        yield
    finally:
        try:
            await azc.async_unregister_service(service_info)
        finally:
            await azc.async_close()
        print("mDNS: unregistered and closed")

app = FastAPI(lifespan=lifespan)

# ---- Sample endpoints ----
@app.get("/")
def root():
    return {"ok": True, "msg": "Sensee is alive", "api": "v1"}

@app.get("/video")
def video_stub():
    return {"note": "Stub /video endpoint - plug in your MJPEG stream here"}

@app.post("/configuration")
def configuration_stub(payload: dict):
    return {"received": payload, "status": "ok"}

if __name__ == "__main__":
    # Host 0.0.0.0 so LAN devices can reach it; PORT must match ServiceInfo.port
    uvicorn.run("app_mdns:app", host="0.0.0.0", port=PORT, reload=False)
