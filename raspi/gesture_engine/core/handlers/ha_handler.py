import threading
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
    """Dispatch smart-device actions with low-latency handling for volume.

    Args:
        runtime: Runtime carrying Home Assistant callbacks.
        entity_id: Home Assistant entity id.
        action: Action to execute.
        is_volume: Whether the action is a volume control.
    """
    if is_volume:
        threading.Thread(
            target=runtime.trigger_ha_action,
            args=(entity_id, action),
            daemon=True,
        ).start()
        return

    queue_latest_action(runtime, entity_id, action)
