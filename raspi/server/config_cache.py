"""In-memory cache of the active gesture configuration.

Kept separate from server.file so that persistence (JSON I/O) and
runtime cache management have distinct responsibilities.
"""

from __future__ import annotations

import threading

from server.file import load_configure_json

_lock = threading.Lock()
_loaded_config: list = load_configure_json()


def get_loaded_config() -> list:
    with _lock:
        return list(_loaded_config)


def set_loaded_config(configuration: list) -> None:
    global _loaded_config
    with _lock:
        _loaded_config = list(configuration) if isinstance(configuration, list) else []


def reload_config_cache() -> list:
    global _loaded_config
    fresh = load_configure_json()
    with _lock:
        _loaded_config = fresh
        return list(_loaded_config)


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
        snapshot = list(_loaded_config)
    return [item for item in snapshot if _is_valid_config_item(item)]
