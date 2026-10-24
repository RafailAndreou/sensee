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
    return _merge_tv_discoveries(flows, devices)


def _merge_tv_discoveries(flows, devices):
    def identity(value):
        return str(value or "").lower().replace(":", "").replace("-", "")

    def title(flow):
        context = flow.get("context", {})
        return (context.get("title_placeholders", {}).get("name") or context.get("title") or "").casefold()

    remaining = list(devices)
    merged = []
    for flow in flows:
        if flow.get("handler") == "androidtv_remote":
            unique_id = identity(flow.get("context", {}).get("unique_id") or flow.get("unique_id"))
            matches = [device for device in remaining if (
                unique_id and identity(device.get("unique_id")) == unique_id
            ) or (flow.get("host") and flow["host"] == device.get("host"))]
            if not matches and title(flow):
                named = [device for device in remaining if title(device) == title(flow)]
                if len(named) == 1:
                    matches = named
            if matches:
                flow = {**flow, "host": matches[0]["host"]}
                for device in matches:
                    remaining.remove(device)
        merged.append(flow)
    # One TV can announce multiple service names. Keep one entry per identity/address.
    seen = set()
    for device in remaining:
        key = identity(device.get("unique_id")) or device["host"]
        if key not in seen:
            merged.append(device)
            seen.add(key)
    return merged


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


def resume_pairing_flow(flow_id: str) -> dict[str, object]:
    client = get_http_client()
    url, token = get_ha_config()
    result = get_pairing_flow(flow_id)
    # Selecting a discovered TV explicitly requests pairing. HA's empty
    # zeroconf confirmation must be submitted before the TV displays a PIN.
    if (result.get("handler") == "androidtv_remote"
            and result.get("type") == "form"
            and result.get("step_id") == "zeroconf_confirm"
            and not result.get("data_schema") and not result.get("errors")):
        return submit_pairing_step_request(url, token, flow_id, {}, client.session, (3.0, 30.0))
    return result


def submit_pairing_step(flow_id: str, user_input: dict[str, object]) -> dict[str, object]:
    """Submit a Home Assistant pairing step using the shared client."""
    client = get_http_client()
    url, token = get_ha_config()
    return submit_pairing_step_request(url, token, flow_id, user_input, client.session, (3.0, 30.0))
