"""Home Assistant config loading and cache helpers."""

from __future__ import annotations

import os
import threading

from server import file

_ha_config_cache: dict[str, str] = {"url": "", "token": ""}
_ha_config_cache_lock = threading.Lock()
_ha_config_loaded = False
DEFAULT_HA_URL = os.getenv("SENSEE_HA_URL", "").strip()
DEFAULT_HA_TOKEN = os.getenv("SENSEE_HA_TOKEN", "").strip()


def get_ha_config() -> tuple[str, str]:
    """Return the cached Home Assistant URL and token."""
    global _ha_config_loaded
    with _ha_config_cache_lock:
        if _ha_config_loaded:
            return _ha_config_cache["url"], _ha_config_cache["token"]

        config = file.load_ha_config()
        url = config.get("url", "").strip()
        token = config.get("token", "").strip()

        if not url:
            url = DEFAULT_HA_URL
        if not token:
            token = DEFAULT_HA_TOKEN

        if url and not url.startswith(("http://", "https://")):
            url = "http://" + url

        _ha_config_cache["url"] = url
        _ha_config_cache["token"] = token
        _ha_config_loaded = True
        return url, token


def refresh_ha_config_cache() -> None:
    """Clear the cached Home Assistant URL and token."""
    global _ha_config_loaded
    with _ha_config_cache_lock:
        _ha_config_cache["url"] = ""
        _ha_config_cache["token"] = ""
        _ha_config_loaded = False
