"""Compatibility facade for Home Assistant helpers."""

from __future__ import annotations

from .ha_config import get_ha_config, refresh_ha_config_cache
from .ha_entities import get_ha_entities
from .ha_pairing import (
    fetch_discovered_flows,
    start_pairing_flow_request,
    submit_pairing_step_request,
)
from .ha_transport import (
    DEBUG_HA_TIMING,
    MOCK_MODE,
    REQUEST_TIMEOUT,
    VOLUME_MIN_INTERVAL_SECONDS,
    get_http_client,
    trigger_ha_action,
)


def get_discovered_flows() -> list[object]:
    """Fetch discovered Home Assistant flows using the shared client."""
    client = get_http_client()
    url, token = get_ha_config()
    return fetch_discovered_flows(url, token, client.session, client.timeout)


def start_pairing_flow(handler: str) -> dict[str, object]:
    """Start a Home Assistant pairing flow using the shared client."""
    client = get_http_client()
    url, token = get_ha_config()
    return start_pairing_flow_request(url, token, handler, client.session, client.timeout)


def submit_pairing_step(flow_id: str, user_input: dict[str, object]) -> dict[str, object]:
    """Submit a Home Assistant pairing step using the shared client."""
    client = get_http_client()
    url, token = get_ha_config()
    return submit_pairing_step_request(url, token, flow_id, user_input, client.session, client.timeout)