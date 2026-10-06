"""Bounded action queue helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gesture_engine.runtime import GestureRuntime


def queue_latest_action(runtime: "GestureRuntime", entity_id: str, action: str, event_ts_ms=None, source=None) -> bool:
    """Retain bounded one-shot commands without overwriting another target."""
    return runtime.enqueue_action(entity_id, action, event_ts_ms=event_ts_ms, source=source)
