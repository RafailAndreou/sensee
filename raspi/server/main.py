from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
import json
import asyncio
import os
from typing import List
from collections import defaultdict

from server import file
import utils
from server import homeassistant
from server.streamer import frame_hub, set_frame_from_bgr
from server.discovery import register_mdns_service, get_local_ip

app = FastAPI()

# ---------------- Models ----------------
class Configuration(BaseModel):
    id: str
    connectionType: str = "ir"
    entityId: str = ""
    brand: str
    action: str
    gesture: str
    sound: str
    hand: str

# ---------------- Config store ----------------
current_config: dict = {}

# ---------------- Events from gestures ----------------
_last_events: dict[str, float] = {}
_event_debouncers = defaultdict(lambda: utils.Debouncer(0.18))

def send_msg(event: str):
    """Called by gesture loop; here you could map to IR/BLE/whatever."""
    if not _event_debouncers[event].can_trigger():
        return
    print(f"[gesture] {event}")

# ---------------- App Lifecycle ----------------
mdns_task = None

@app.on_event("startup")
async def startup_event():
    global mdns_task
    port = int(os.environ.get("SENSEE_PORT", 8000))
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
    current_config = [s.model_dump() for s in settings]
    print(f"\n✅ Received {len(current_config)} configurations:")
    for conf in current_config:
        print(f"  - ID {conf['id']}: {conf['brand']} {conf['action']} ({conf['gesture']})")
    file.save_configure_json(current_config)
    file.loaded_config = file.load_configure_json()
    return {"status": "configured", "count": len(current_config)}

@app.get("/configuration")
def get_configuration_msg():
    return {"message": "Please use POST /configuration to configure settings"}

@app.get("/current")
def get_current_config():
    return current_config

@app.get("/smart-devices")
def get_smart_devices():
    # Fetch REAL devices from your Home Assistant
    devices = homeassistant.get_ha_entities()
    return {
        "status": "success",
        "devices": devices
    }

@app.get("/video")
def video():
    return StreamingResponse(
        frame_hub.mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.post("/event/{name}")
def post_event(name: str):
    send_msg(name)
    return JSONResponse({"ok": True, "event": name})

# -------------- Main --------------
if __name__ == "__main__":
    import uvicorn
    ip, _ = get_local_ip()
    
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

