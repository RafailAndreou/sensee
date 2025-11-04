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
from zeroconf.asyncio import AsyncZeroconf,AsyncServiceBrowser
import asyncio

app = FastAPI()

SERVICE_TYPE = "_sensee._tcp.local."

# ---------------- Models ----------------
class Configuration(BaseModel):
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

def _discovery_responder():
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

    local_ip = get_local_ip()
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
                payload = json.dumps({"ip": local_ip, "port": 8000}).encode()
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
def configure(settings: Configuration):
    global current_config
    current_config = settings.dict()
    print("\n✅ Received configuration:")
    for k, v in current_config.items():
        print(f"  {k}: {v}")
    return {"status": "configured", "received": current_config}

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
    print(f"\n🌐 Server running at http://{ip}:8000\n")
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000)

