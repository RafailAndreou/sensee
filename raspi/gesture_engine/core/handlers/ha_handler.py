# raspi/gesture_engine/core/handlers/ha_handler.py

from queue import Full
from typing import TYPE_CHECKING
from .action_queue import queue_latest_action

if TYPE_CHECKING:
    from gesture_engine.runtime import GestureRuntime

def handle_smart_device_action(
    runtime: "GestureRuntime",
    entity_id: str,
    action: str,
    is_volume: bool,
) -> None:
    """Dispatch smart-device actions with low-latency handling for volume."""
    if is_volume:
        try:
            # If the worker is free, hand it the action. 
            # If the worker is busy (Full), drop the frame instantly to save CPU.
            runtime.volume_queue.put_nowait((entity_id, action))
        except Full:
            pass
        return

    queue_latest_action(runtime, entity_id, action)