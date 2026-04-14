"""Home Assistant entity fetching and formatting helpers."""

from __future__ import annotations

import threading
import time
from typing import Any, Mapping, Sequence

from .ha_services import get_domain_from_entity
from .ha_transport import MOCK_MODE, get_http_client
from .ha_config import get_ha_config

_entities_cache: list[dict[str, str]] = []
_entities_cache_time = 0.0
_entities_cache_lock = threading.Lock()
_ENTITIES_CACHE_TTL_SECONDS = 2.0

_DOMAIN_TO_SENSEE_TYPE = {
    "media_player": "Tv",
    "light": "Light",
    "switch": "Light",
    "climate": "Ac",
    "fan": "Fan",
}


def _filter_entities_by_type(devices: Sequence[dict[str, str]], device_type_filter: str | None = None) -> list[dict[str, str]]:
    """Filter cached entities by the requested Sensee device type."""
    if not device_type_filter:
        return list(devices)
    wanted = device_type_filter.lower()
    return [device for device in devices if device.get("type", "").lower() == wanted]


def _read_entities_cache(device_type_filter: str | None = None) -> list[dict[str, str]]:
    """Read the entity cache with optional type filtering."""
    with _entities_cache_lock:
        cached = list(_entities_cache)
    return _filter_entities_by_type(cached, device_type_filter)


def _write_entities_cache(devices: Sequence[dict[str, str]], cache_time: float) -> None:
    """Replace the entity cache with a new snapshot."""
    global _entities_cache_time
    with _entities_cache_lock:
        _entities_cache[:] = list(devices)
        _entities_cache_time = cache_time


def _format_states_to_devices(all_states: Sequence[Mapping[str, Any]], device_type_filter: str | None = None) -> list[dict[str, str]]:
    """Convert Home Assistant entity states into Sensee device records."""
    formatted_devices: list[dict[str, str]] = []

    for state in all_states:
        entity_id = str(state.get("entity_id", ""))
        domain = get_domain_from_entity(entity_id)
        sensee_type = _DOMAIN_TO_SENSEE_TYPE.get(domain)
        if not sensee_type:
            continue

        if device_type_filter and sensee_type.lower() != device_type_filter.lower():
            continue

        attributes = state.get("attributes", {})
        friendly_name = entity_id
        if isinstance(attributes, Mapping):
            friendly_name = str(attributes.get("friendly_name", entity_id))

        formatted_devices.append(
            {
                "entity_id": entity_id,
                "friendly_name": friendly_name,
                "type": sensee_type,
            }
        )

    return formatted_devices


def _has_valid_runtime_config(url_base: str, token: str) -> bool:
    """Check whether the Home Assistant connection settings are present."""
    return bool(url_base and token)


def get_ha_entities(device_type_filter: str | None = None) -> list[dict[str, str]]:
    """Fetch and format entities for the Sensee UI."""
    global _entities_cache_time

    if MOCK_MODE:
        return [
            {"entity_id": "media_player.living_room_tv", "friendly_name": "Mock Living Room TV", "type": "Tv"},
            {"entity_id": "light.bedroom_lamp", "friendly_name": "Mock Bedroom Lamp", "type": "Light"},
            {"entity_id": "climate.downstairs_ac", "friendly_name": "Mock Living Room AC", "type": "Ac"},
            {"entity_id": "fan.kitchen_fan", "friendly_name": "Mock Kitchen Fan", "type": "Fan"},
        ]

    now = time.monotonic()
    with _entities_cache_lock:
        if now - _entities_cache_time < _ENTITIES_CACHE_TTL_SECONDS:
            return _filter_entities_by_type(_entities_cache, device_type_filter)

    url_base, token = get_ha_config()
    if not _has_valid_runtime_config(url_base, token):
        print("❌ Home Assistant config missing. Cannot fetch entities.")
        return []

    try:
        http_client = get_http_client()
        response = http_client.get_all_states(url_base, token)
        if response.status_code != 200:
            print(f"❌ HA Fetch Error {response.status_code}: {response.text}")
            return _read_entities_cache(device_type_filter)

        all_states = response.json()
        formatted_devices = _format_states_to_devices(all_states, device_type_filter)

        _write_entities_cache(formatted_devices, now)
        return list(formatted_devices)
    except Exception as e:
        print(f"❌ Exception fetching entities from Home Assistant: {e}")
        return _read_entities_cache(device_type_filter)