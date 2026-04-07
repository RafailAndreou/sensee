from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
import asyncio
import os
from typing import List
from collections import defaultdict

from server import file
import utils
from server import homeassistant
from server.config_validation import validate_configuration_payload
from server.models import (
    Configuration,
    HAConfigRequest,
    HAPairStartRequest,
    HAPairSubmitRequest,
)
from server.streamer import frame_hub, set_frame_from_bgr
from server.discovery import register_mdns_service, get_local_ip

app = FastAPI()

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
    incoming_config = [s.model_dump() for s in settings]

    validation_error = validate_configuration_payload(incoming_config)
    if validation_error:
        raise HTTPException(
            status_code=400,
            detail=validation_error,
        )

    current_config = incoming_config
    print(f"\n✅ Received {len(current_config)} configurations:")
    for conf in current_config:
        print(f"  - ID {conf['id']}: {conf['brand']} {conf['action']} ({conf['gesture']})")
    file.save_configure_json(current_config)
    file.loaded_config = file.load_configure_json()
    return {"status": "configured", "count": len(current_config)}

@app.get("/configuration")
def get_configuration():
    return file.get_active_configs()

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

@app.get("/ha/config")
def get_ha_config():
    config = file.load_ha_config()
    # Mask the token for security
    masked_token = config.get("token", "")
    if len(masked_token) > 10:
        masked_token = masked_token[:5] + "..." + masked_token[-5:]
    return {
        "url": config.get("url", ""),
        "token": masked_token
    }

@app.post("/ha/config")
def post_ha_config(req: HAConfigRequest):
    file.save_ha_config({"url": req.url, "token": req.token})
    homeassistant.refresh_ha_config_cache()
    return {"status": "success"}

@app.get("/ha/discovered")
def get_ha_discovered():
    flows = homeassistant.get_discovered_flows()
    return {"status": "success", "flows": flows}

@app.post("/ha/pair/start")
def post_ha_pair_start(req: HAPairStartRequest):
    result = homeassistant.start_pairing_flow(req.handler)
    return {"status": "success", "result": result}

@app.post("/ha/pair/submit")
def post_ha_pair_submit(req: HAPairSubmitRequest):
    result = homeassistant.submit_pairing_step(req.flow_id, req.user_input)
    return {"status": "success", "result": result}

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

