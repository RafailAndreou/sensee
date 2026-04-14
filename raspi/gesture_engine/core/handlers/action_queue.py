"""Latest-only action queue helpers."""

from __future__ import annotations

from queue import Empty
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gesture_engine.runtime import GestureRuntime


def queue_latest_action(runtime: "GestureRuntime", entity_id: str, action: str) -> None:
    """Keep only the newest queued action to avoid stale backlog execution."""
    action_queue = getattr(runtime, "action_queue", runtime.ha_action_queue)

    if action_queue.full():
        try:
            action_queue.get_nowait()
        except Empty:
            pass

    action_queue.put_nowait((entity_id, action))