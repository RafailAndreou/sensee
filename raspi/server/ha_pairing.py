"""Home Assistant pairing flow helpers."""

from __future__ import annotations

from typing import Any
import json
from urllib.parse import quote, urlsplit, urlunsplit

import requests
from fastapi import HTTPException
from websockets.sync.client import connect
from websockets.exceptions import WebSocketException

from gesture_engine.log import get_logger

logger = get_logger(__name__)


def fetch_discovered_flows(url: str, token: str, http_session: Any, timeout: tuple[float, float]) -> list[Any]:
    """List pending discoveries through HA's authenticated WebSocket API."""
    parts = urlsplit(url.rstrip('/'))
    ws_url = urlunsplit(("wss" if parts.scheme == "https" else "ws", parts.netloc,
                        parts.path + "/api/websocket", "", ""))
    try:
        with connect(ws_url, open_timeout=timeout[0], close_timeout=1) as socket:
            if json.loads(socket.recv(timeout=timeout[1])).get("type") != "auth_required":
                raise ValueError("Unexpected Home Assistant authentication response")
            socket.send(json.dumps({"type": "auth", "access_token": token}))
            if json.loads(socket.recv(timeout=timeout[1])).get("type") != "auth_ok":
                raise HTTPException(502, "Home Assistant rejected the saved token. Reconnect Home Assistant.")
            socket.send(json.dumps({"id": 1, "type": "config_entries/flow/progress"}))
            result = json.loads(socket.recv(timeout=timeout[1]))
            if result.get("id") != 1 or not result.get("success"):
                raise HTTPException(502, "Home Assistant discovery requires an administrator account.")
            flows = result.get("result")
            if not isinstance(flows, list):
                raise ValueError("Invalid Home Assistant discovery response")
            return flows
    except (OSError, TimeoutError, ValueError, WebSocketException) as error:
        logger.warning("Home Assistant discovery connection failed: %s", type(error).__name__)
        raise HTTPException(502, "Cannot read Home Assistant discoveries. Check its address and network connection.") from error


def _flow_request(method: str, url: str, token: str, http_session: Any,
                  timeout: tuple[float, float], **kwargs: Any) -> dict[str, Any]:
    try:
        response = getattr(http_session, method)(
            url, headers={"Authorization": f"Bearer {token}"}, timeout=timeout, **kwargs)
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise ValueError("Invalid pairing response")
        return result
    except (requests.exceptions.RequestException, ValueError) as error:
        logger.warning("Home Assistant pairing request failed: %s", type(error).__name__)
        raise HTTPException(502, "Home Assistant pairing failed. Check connectivity and administrator permissions; the flow may have expired.") from error


def get_pairing_flow_request(url: str, token: str, flow_id: str, http_session: Any,
                             timeout: tuple[float, float]) -> dict[str, Any]:
    """Resume an existing discovery without creating a duplicate flow."""
    return _flow_request("get", f"{url.rstrip('/')}/api/config/config_entries/flow/{quote(flow_id, safe='')}",
                         token, http_session, timeout)


def start_pairing_flow_request(url: str, token: str, handler: str, http_session: Any, timeout: tuple[float, float]) -> dict[str, Any]:
    """Start a Home Assistant pairing flow for the given handler."""
    return _flow_request("post", f"{url.rstrip('/')}/api/config/config_entries/flow",
                         token, http_session, timeout, json={"handler": handler})


def submit_pairing_step_request(url: str, token: str, flow_id: str, user_input: dict[str, Any], http_session: Any, timeout: tuple[float, float]) -> dict[str, Any]:
    """Submit a Home Assistant pairing flow step."""
    return _flow_request("post", f"{url.rstrip('/')}/api/config/config_entries/flow/{quote(flow_id, safe='')}",
                         token, http_session, timeout, json=user_input)
