"""Shared voice-model loading status.

Both voice_controller (writer) and server/main (reader + preload trigger)
import this module so they share state without circular imports.
"""
import threading

_lock = threading.Lock()
_status: str = "idle"   # "idle" | "loading" | "ready"
_model: str | None = None

_preload_fn = None


def register_preload(fn) -> None:
    global _preload_fn
    _preload_fn = fn


def request_preload(model_name: str) -> None:
    if _preload_fn:
        _preload_fn(model_name)


def set_loading(model_name: str) -> None:
    global _status, _model
    with _lock:
        _status = "loading"
        _model = model_name


def set_ready(model_name: str) -> None:
    global _status, _model
    with _lock:
        _status = "ready"
        _model = model_name


def set_idle() -> None:
    global _status
    with _lock:
        _status = "idle"


def get() -> dict:
    with _lock:
        return {"status": _status, "model": _model}
