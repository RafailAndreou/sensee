# raspi/gesture_engine/core/handlers/ha_handler.py

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gesture_engine.runtime import GestureRuntime

def handle_smart_device_action(
    runtime: "GestureRuntime",
    entity_id: str,
    action: str,
    is_volume: bool,
    event_ts_ms=None,
) -> bool:
    """Dispatch smart-device actions with low-latency handling for volume."""
    return runtime.enqueue_action(entity_id, action, is_volume=is_volume, event_ts_ms=event_ts_ms)
