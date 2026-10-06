"""In-memory cache of the active gesture configuration.

Kept separate from server.file so that persistence (JSON I/O) and
runtime cache management have distinct responsibilities.
"""

from __future__ import annotations

import threading

from server.file import load_configure_json
from gesture_engine.core.matching import canonical_gesture_name, canonical_hand_name

_lock = threading.Lock()
_loaded_config: list = load_configure_json()
_active_config: tuple = ()
_mapping_index: dict = {}


def get_loaded_config() -> list:
    with _lock:
        return list(_loaded_config)


def set_loaded_config(configuration: list) -> None:
    global _loaded_config, _active_config, _mapping_index
    snapshot = list(configuration) if isinstance(configuration, list) else []
    active = tuple(item for item in snapshot if _is_valid_config_item(item))
    index = {}
    for position, item in enumerate(active):
        key = (canonical_gesture_name(item["gesture"]),
               canonical_hand_name(str(item.get("hand", ""))))
        index.setdefault(key, (position, item))
    with _lock:
        _loaded_config, _active_config, _mapping_index = snapshot, active, index


def reload_config_cache() -> list:
    fresh = load_configure_json()
    set_loaded_config(fresh)
    return get_loaded_config()


def _is_valid_config_item(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    if str(item.get("id", "")).strip() in ("", "-1"):
        return False
    if not str(item.get("gesture", "")).strip():
        return False
    if not str(item.get("action", "")).strip():
        return False
    return True


def get_active_configs() -> list:
    with _lock:
        return list(_active_config)


def find_config(gesture_name, detected_hand="Unknown"):
    gesture = canonical_gesture_name(gesture_name)
    hand = canonical_hand_name(str(detected_hand))
    with _lock:
        exact = _mapping_index.get((gesture, hand)) if hand in ("left hand", "right hand") else None
        wildcard = _mapping_index.get((gesture, "both hands"))
        if exact is not None and (wildcard is None or exact[0] < wildcard[0]):
            return exact[1]
        return wildcard[1] if wildcard is not None else None


set_loaded_config(_loaded_config)
