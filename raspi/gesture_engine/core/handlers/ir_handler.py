from typing import TYPE_CHECKING

from .ha_handler import queue_latest_ha_action

if TYPE_CHECKING:
    from gesture_engine.runtime import GestureRuntime


def handle_ir_device_action(runtime: "GestureRuntime", entity_id: str, action: str) -> None:
    """Route IR actions through the serialized queue used by non-PC actions.

    Args:
        runtime: Runtime carrying shared action queue state.
        entity_id: Device/entity id from config.
        action: Action to execute.
    """
    queue_latest_ha_action(runtime, entity_id, action)
