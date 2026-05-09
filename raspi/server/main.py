from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import os
from dataclasses import dataclass, field
from typing import Any, List

from gesture_engine.log import get_logger
from server import config_cache, file
from server import homeassistant
from server.config_validation import validate_configuration_payload
from server.events import send_msg

logger = get_logger(__name__)
from server.models import (
    CameraSettings,
    Configuration,
    HAConfigRequest,
    HAPairStartRequest,
    HAPairSubmitRequest,
    GestureSettings,
)
from server.startup import run_uvicorn_with_port_retry
from server.streamer import frame_hub
from server.discovery import register_mdns_service, get_local_ip


@dataclass
class AppState:
    """Lightweight in-memory app state shared by route handlers."""

    current_config: list[dict[str, Any]] = field(default_factory=list)
    gesture_settings: dict[str, Any] = field(default_factory=dict)


def _validate_configuration_or_raise(configs: list[dict[str, Any]]) -> None:
    validation_error = validate_configuration_payload(configs)
    if validation_error:
        raise HTTPException(status_code=400, detail=validation_error)


def _persist_configuration(configs: list[dict[str, Any]]) -> None:
    file.save_configure_json(configs)
    config_cache.set_loaded_config(configs)


def _log_received_configurations(configs: list[dict[str, Any]]) -> None:
    logger.info("Received %s configurations:", len(configs))
    for conf in configs:
        logger.info("  - ID %s: %s %s (%s)", conf["id"], conf["brand"], conf["action"], conf["gesture"])


def _mask_token(token: str) -> str:
    """Mask sensitive token values while still exposing enough for verification."""
    if len(token) > 12:
        return token[:5] + "..." + token[-5:]
    if token:
        return "***"
    return ""

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sensee = AppState()
    port = int(os.environ.get("SENSEE_PORT", 8000))
    app.state.mdns_task = asyncio.create_task(register_mdns_service(port))
    yield
    mdns_task = getattr(app.state, "mdns_task", None)
    if mdns_task:
        logger.info("Stopping mDNS service...")
        mdns_task.cancel()
        try:
            await mdns_task
        except asyncio.CancelledError:
            pass
        logger.info("mDNS service stopped.")

app = FastAPI(lifespan=lifespan)

# Serve web dashboard (web folder lives one level above the server package)
_web_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "web"))
if os.path.isdir(_web_dir):
    app.mount("/web", StaticFiles(directory=_web_dir), name="web")

# ---------------- Routes ----------------
@app.get("/")
def index():
    web_index = os.path.join(_web_dir, "index.html")
    if os.path.exists(web_index):
        with open(web_index, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("""
    <html>
      <body style="margin:0;background:#111;display:flex;justify-content:center;align-items:center;height:100vh">
        <img src="/video" style="max-width:100%;height:auto;"/>
      </body>
    </html>
    """)


@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.post("/configuration")
def configure(settings: List[Configuration]):
    incoming_config = [s.model_dump() for s in settings]
    _validate_configuration_or_raise(incoming_config)

    app.state.sensee.current_config = incoming_config
    _log_received_configurations(incoming_config)
    _persist_configuration(incoming_config)
    return {"status": "configured", "count": len(incoming_config)}

@app.get("/configuration")
def get_configuration():
    return config_cache.get_active_configs()

@app.get("/current")
def get_current_config():
    return app.state.sensee.current_config

@app.get("/smart-devices")
def get_smart_devices():
    devices = homeassistant.get_ha_entities()
    return {"status": "success", "devices": devices}

@app.get("/ha/cameras")
def get_ha_cameras():
    cameras = homeassistant.get_ha_cameras()
    return {"status": "success", "cameras": cameras}

@app.get("/ha/config")
def get_ha_config():
    config = file.load_ha_config()
    return {
        "url": config.get("url", ""),
        "token": _mask_token(config.get("token", "")),
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

@app.post("/gesture-settings")
def post_gesture_settings(settings: GestureSettings):
    logger.info("Received gesture settings: %s", settings.model_dump())
    app.state.sensee.gesture_settings = settings.model_dump()
    
    if not settings.wakeEnabled:
        file.delete_gesture_settings()
        return {"status": "disabled"}
    
    file.save_gesture_settings(settings.model_dump())
    return {"status": "saved"}

@app.get("/gesture-settings")
def get_gesture_settings():
    return file.load_gesture_settings()

@app.post("/camera-settings")
def post_camera_settings(settings: CameraSettings):
    file.save_camera_settings(settings.model_dump())
    return {"status": "saved"}

@app.get("/camera-settings")
def get_camera_settings():
    return file.load_camera_settings()

# -------------- Main --------------
if __name__ == "__main__":
    ip, _ = get_local_ip()
    run_uvicorn_with_port_retry(
        app_import_path="server.main:app",
        ip=ip,
        context_label="Server running at",
    )

