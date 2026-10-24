"""Compatibility facade for Home Assistant helpers."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException

from .ha_discovery import discover_android_tvs

from .ha_config import get_ha_config, refresh_ha_config_cache
from .ha_entities import get_ha_cameras, get_ha_entities
from .ha_pairing import (
    fetch_discovered_flows,
    get_pairing_flow_request,
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
    """Combine HA discoveries with an Android TV scan on Sensee's own LAN."""
    client = get_http_client()
    url, token = get_ha_config()
    with ThreadPoolExecutor(max_workers=1) as executor:
        native_scan = executor.submit(discover_android_tvs)
        try:
            flows = fetch_discovered_flows(url, token, client.session, (1.5, 2.0))
        except HTTPException:
            devices = native_scan.result()
            if devices:
                return devices
            raise
        devices = native_scan.result()
    # Prefer an existing flow for the same named TV, keeping other local TVs.
    known_titles = {
        (flow.get("context", {}).get("title") or
         flow.get("context", {}).get("title_placeholders", {}).get("name") or "").casefold()
        for flow in flows if flow.get("handler") == "androidtv_remote"
    }
    return flows + [device for device in devices
                    if device["context"]["title"].casefold() not in known_titles]


def start_pairing_flow(handler: str, host: str | None = None) -> dict[str, object]:
    """Start a Home Assistant pairing flow using the shared client."""
    client = get_http_client()
    url, token = get_ha_config()
    result = start_pairing_flow_request(url, token, handler, client.session, (3.0, 30.0))
    if host and handler == "androidtv_remote" and result.get("type") == "form" and result.get("step_id") == "user":
        return submit_pairing_step_request(url, token, result["flow_id"], {"host": host},
                                           client.session, (3.0, 30.0))
    return result


def get_pairing_flow(flow_id: str) -> dict[str, object]:
    client = get_http_client()
    url, token = get_ha_config()
    return get_pairing_flow_request(url, token, flow_id, client.session, (3.0, 30.0))


def submit_pairing_step(flow_id: str, user_input: dict[str, object]) -> dict[str, object]:
    """Submit a Home Assistant pairing step using the shared client."""
    client = get_http_client()
    url, token = get_ha_config()
    return submit_pairing_step_request(url, token, flow_id, user_input, client.session, (3.0, 30.0))
