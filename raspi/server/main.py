# server/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
import json
import socket
import threading
import time
import cv2
import numpy as np
from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser, AsyncServiceInfo
import asyncio
import os
from server import file
from typing import List

app = FastAPI()

port = 8000

SERVICE_TYPE = "_sensee._tcp.local."

# ---------------- Models ----------------
class Configuration(BaseModel):
    id: str
    brand: str
    action: str
    gesture: str
    sound: str
    hand: str

# ---------------- Config store ----------------
current_config: dict = {}

# ---------------- Frame Hub ----------------
class FrameHub:
    """Thread-safe place to publish latest JPEG for MJPEG streaming."""
    def __init__(self):
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._latest_jpeg: bytes | None = None

    def set_bgr_frame(self, bgr: np.ndarray, jpeg_quality: int = 80):
        ok, jpg = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])
        if not ok:
            return
        with self._lock:
            self._latest_jpeg = jpg.tobytes()
            self._event.set()

    def mjpeg_generator(self):
        boundary = b"--frame"
        # Yield a frame whenever a new one arrives; send a keepalive if idle.
        while True:
            # Wait at most 1s for a new frame to avoid proxy timeouts.
            self._event.wait(timeout=1.0)
            with self._lock:
                frame_bytes = self._latest_jpeg
                self._event.clear()

            if frame_bytes is None:
                # Keep-alive empty JPEG if nothing yet
                time.sleep(0.05)
                continue

            headers = (
                boundary + b"\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(frame_bytes)).encode() + b"\r\n\r\n"
            )
            yield headers + frame_bytes + b"\r\n"

frame_hub = FrameHub()

def set_frame_from_bgr(frame_bgr):
    """Public function the capture loop can call."""
    frame_hub.set_bgr_frame(frame_bgr)

# ---------------- Events from gestures ----------------
_last_events: dict[str, float] = {}
_DEBOUNCE_S = 0.18

def send_msg(event: str):
    """Called by gesture loop; here you could map to IR/BLE/whatever."""
    now = time.monotonic()
    last = _last_events.get(event, 0.0)
    if now - last < _DEBOUNCE_S:
        return
    _last_events[event] = now
    print(f"[gesture] {event}")
    if event == "Thumb+Index":
        for i in file.load_configure_json():
            if i["gesture"]=="Thumb+Index":
                print(i["action"])
    # TODO: integrate with ESP32/IR here

# ---------------- Helpers ----------------
def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    s.close()
    
    return ip,socket.inet_aton(ip)


# ---------------- Discovery responder (UDP) ----------------
_DISCOVERY_PORT = 54321
_DISCOVERY_TOKEN = "SENSEE_DISCOVER"

def _discovery_responder(port):
    """Listen for discovery UDP probes and reply with server IP/port as JSON.

    Simple protocol:
      Client sends: b"SENSEE_DISCOVER"
      Server replies: b"{\"ip\": "<ip>", \"port\": 8000}" to sender addr
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # allow reuse
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception:
        pass

    try:
        sock.bind(("0.0.0.0", _DISCOVERY_PORT))
    except Exception as e:
        print(f"[discovery] ❌ Failed to bind UDP port {_DISCOVERY_PORT}: {e}")
        return

    local_ip, _ = get_local_ip()  # Unpack the tuple correctly
    print(f"[discovery] ✅ Responder listening on UDP port {_DISCOVERY_PORT}")
    print(f"[discovery] Server IP: {local_ip}")
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if not data:
                continue
            print(f"[discovery] 📡 Received {len(data)} bytes from {addr}")
            try:
                txt = data.decode().strip()
                print(f"[discovery] Message: '{txt}'")
            except Exception as e:
                print(f"[discovery] ⚠️ Decode error: {e}")
                continue
            
            if txt == _DISCOVERY_TOKEN:
                payload = json.dumps({"ip": local_ip, "port": port}).encode()
                print(f"[discovery] ✅ Sending response to {addr}: {payload.decode()}")
                try:
                    sock.sendto(payload, addr)
                    print(f"[discovery] ✅ Response sent successfully")
                except Exception as e:
                    print(f"[discovery] ❌ Failed to send reply to {addr}: {e}")
            else:
                print(f"[discovery] ⚠️ Token mismatch. Expected '{_DISCOVERY_TOKEN}', got '{txt}'")
        except Exception as e:
            # keep responder alive
            print(f"[discovery] ❌ Error: {e}")
# Start discovery responder in background so the Flutter app can discover the server
# try:
#     t = threading.Thread(target=_discovery_responder, daemon=True)
#     t.start()
# except Exception as e:
#     print(f"[discovery] failed to start responder thread: {e}")
    
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
        
async def discovery_responder_async():
    
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

# try:
#     asyncio.run(discovery_responder_async())
# except Exception as e:
#     print(f"[discovery] ❌ Error in discovery responder: {e}")

async def register_mdns_service(port: int):
    """Register this server as sensee.local on the network."""
    ip_str, ip_bytes = get_local_ip()
    
    # Create service info
    info = AsyncServiceInfo(
        SERVICE_TYPE,
        "Sensee Server._sensee._tcp.local.",
        addresses=[ip_bytes],  # Use the bytes from get_local_ip()
        port=port,
        properties={"path": "/configuration", "ip": ip_str},  # Add IP to properties for easy discovery
        server="sensee.local.",
    )
    
    zc = AsyncZeroconf()
    try:
        await zc.async_register_service(info)
        print(f"✅ mDNS service registered as sensee.local at {ip_str}:{port}")
        print(f"   Other devices can connect using: http://{ip_str}:{port}")
        print(f"   Or using mDNS: http://sensee.local:{port} (requires Bonjour on Windows)")
        # Keep it registered (block indefinitely)
        await asyncio.Event().wait()
    except Exception as e:
        print(f"❌ Failed to register mDNS service: {e}")
        print(f"   Server is still accessible at: http://{ip_str}:{port}")
    finally:
        await zc.async_unregister_service(info)
        await zc.async_close()

mdns_task = None

@app.on_event("startup")
async def startup_event():
    global mdns_task
    port = int(os.environ.get("SENSEE_PORT", 8000))
    # Start mDNS registration in background task
    mdns_task = asyncio.create_task(register_mdns_service(port))

@app.on_event("shutdown")
async def shutdown_event():
    global mdns_task
    if mdns_task:
        print("Stopping mDNS service...")
        mdns_task.cancel()
        try:
            await mdns_task
        except asyncio.CancelledError:
            pass
        print("mDNS service stopped.")

# ---------------- Routes ----------------
@app.get("/")
def index():
    return HTMLResponse("""
    <html>
      <body style="margin:0;background:#111;display:flex;justify-content:center;align-items:center;height:100vh">
        <img src="/video" style="max-width:100%;height:auto;"/>
      </body>
    </html>
    """)

@app.post("/configuration")
def configure(settings: List[Configuration]):
    global current_config
    current_config = [s.model_dump () for s in settings]
    print(f"\n✅ Received {len(current_config)} configurations:")
    for conf in current_config:
        print(f"  - ID {conf['id']}: {conf['brand']} {conf['action']} ({conf['gesture']})")
    file.save_configure_json(current_config)
        
    return {"status": "configured", "count": len(current_config)}

@app.get("/configuration")
def get_configuration_msg():
    return {"message": "Please use POST /configuration to configure settings"}

@app.get("/current")
def get_current_config():
    return current_config

@app.get("/video")
def video():
    return StreamingResponse(
        frame_hub.mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# Optional: simple HTTP endpoint to poke gestures from outside (debug)
@app.post("/event/{name}")
def post_event(name: str):
    send_msg(name)
    return JSONResponse({"ok": True, "event": name})

# -------------- Main --------------
if __name__ == "__main__":
    import uvicorn
    ip, bytes = get_local_ip()
    
    ports_to_try = [8000, 8001, 8002, 8003, 8004]
    started = False
    
    for attempt_port in ports_to_try:
        try:
            print(f"\n🌐 Server running at http://{ip}:{attempt_port}\n")
            os.environ["SENSEE_PORT"] = str(attempt_port)
            uvicorn.run("server.main:app", host="0.0.0.0", port=attempt_port)
            started = True
            break
        except OSError as e:
            error_str = str(e)
            if "10048" in error_str or "Address already in use" in error_str:
                if attempt_port == ports_to_try[-1]:
                    print(f"❌ All ports {ports_to_try} are already in use!")
                    print("   Please kill the background process or restart your system.")
                    exit(1)
                else:
                    print(f"⚠️  Port {attempt_port} in use, trying {attempt_port + 1}...")
            else:
                raise
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            raise
    
    if not started:
        print("❌ Failed to start server")
        exit(1)

