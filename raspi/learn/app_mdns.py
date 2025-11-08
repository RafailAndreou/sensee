import socket
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from zeroconf import ServiceInfo
from zeroconf.asyncio import AsyncZeroconf # Correct Async import
import uvicorn

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# --- CONFIGURATION ---
SERVICE_TYPE = "_sensee._tcp.local."
INSTANCE_NAME = "Sensee Smart Controller"
PORT = 8000
SERVER_HOSTNAME = "sensee.local." # The name used for sensee.local:8000

# --- HELPER FUNCTION ---
def get_ipv4_bytes():
    """Return active LAN IPv4 as 4 bytes (network order), fallback to 127.0.0.1."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Forces OS to pick outbound iface/IP; no packets sent
        s.connect(("8.8.8.8", 80)) 
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return socket.inet_aton(ip)

# --- FASTAPI LIFESPAN MANAGER (STARTUP/SHUTDOWN) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- FastAPI Startup: Registering mDNS Service ---")

    # 1. Define ServiceInfo
    service_info = ServiceInfo(
        type_=SERVICE_TYPE,
        name=f"{INSTANCE_NAME}.{SERVICE_TYPE}", # Full service instance name
        port=PORT,
        addresses=[get_ipv4_bytes()],
        properties={
            "api": "v1",
            "web": "/",
            "video": "/video",
            "config": "/configuration",
        },
        server=SERVER_HOSTNAME, 
    )

    # 2. Start AsyncZeroconf and Register Service
    azc = AsyncZeroconf() 
    # Use the correct asynchronous method: async_register_service
    await azc.async_register_service(service_info) 
    print(f"✅ Registered mDNS service {SERVER_HOSTNAME} on port {PORT}")
    
    # 3. Yield to run the FastAPI server
    yield
    
    # 4. FastAPI Shutdown: Unregister mDNS Service
    print("--- FastAPI Shutdown: Unregistering mDNS Service ---")
    await azc.async_unregister_service(service_info) # Correct async method
    await azc.async_close()                          # Correct async method
    print("❌ mDNS service unregistered and AsyncZeroconf closed.")


# Initialize FastAPI with the lifespan manager
app = FastAPI(lifespan=lifespan)


# --- FASTAPI ENDPOINTS ---
@app.get("/")
def root():
    return {"ok": True, "msg": "Sensee is alive", "api": "v1"}

@app.get("/video")
def video_stub():
    return {"note": "Stub /video endpoint - plug in your MJPEG stream here"}

@app.post("/configuration")
def configuration_stub(payload: dict):
    return {"received": payload, "status": "ok"}


# --- RUN THE SERVER ---
if __name__ == "__main__":
    # Host 0.0.0.0 so LAN devices can reach it; PORT matches ServiceInfo.port
    # Uvicorn handles the lifespan context manager automatically.
    uvicorn.run("app_mdns:app", host="0.0.0.0", port=PORT, reload=False)