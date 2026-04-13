import threading
from queue import Empty
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gesture_engine.runtime import GestureRuntime


def queue_latest_ha_action(runtime: "GestureRuntime", entity_id: str, action: str) -> None:
    """Keep only the latest HA queue item to avoid stale backlog execution.

    Args:
        runtime: Runtime that owns the Home Assistant action queue.
        entity_id: Home Assistant entity id.
        action: Home Assistant action/service value.
    """
    if runtime.ha_action_queue.full():
        try:
            runtime.ha_action_queue.get_nowait()
        except Empty:
            pass

    runtime.ha_action_queue.put_nowait((entity_id, action))


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

    queue_latest_ha_action(runtime, entity_id, action)
