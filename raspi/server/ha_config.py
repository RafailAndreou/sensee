"""Home Assistant config loading and cache helpers."""

from __future__ import annotations

import os
import threading

from server import file

_ha_config_cache: dict[str, str] = {"url": "", "token": ""}
_ha_config_cache_lock = threading.Lock()
DEFAULT_HA_URL = os.getenv("SENSEE_HA_URL", "").strip()
DEFAULT_HA_TOKEN = os.getenv("SENSEE_HA_TOKEN", "").strip()


def get_ha_config() -> tuple[str, str]:
    """Return the cached Home Assistant URL and token."""
    with _ha_config_cache_lock:
        if _ha_config_cache["url"] and _ha_config_cache["token"]:
            return _ha_config_cache["url"], _ha_config_cache["token"]

        config = file.load_ha_config()
        url = config.get("url", "").strip()
        token = config.get("token", "").strip()

        if not url:
            url = DEFAULT_HA_URL
        if not token:
            token = DEFAULT_HA_TOKEN

        _ha_config_cache["url"] = url
        _ha_config_cache["token"] = token
        return url, token


def refresh_ha_config_cache() -> None:
    """Clear the cached Home Assistant URL and token."""
    with _ha_config_cache_lock:
        _ha_config_cache["url"] = ""
        _ha_config_cache["token"] = ""