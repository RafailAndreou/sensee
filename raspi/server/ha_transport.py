"""Home Assistant action transport and request handling."""

from __future__ import annotations

import os
import threading
import time

import requests

from gesture_engine.log import get_logger

from .ha_client import HAClient
from .ha_config import get_ha_config
from .ha_services import get_domain_from_entity, parse_action_to_service

logger = get_logger(__name__)

MOCK_MODE = False

# Keep HA calls short so network hiccups don't stall nearby workflows.
REQUEST_TIMEOUT = (0.8, 2.2)
VOLUME_MIN_INTERVAL_SECONDS = float(os.getenv("SENSEE_VOLUME_INTERVAL", "0.05"))
DEBUG_HA_TIMING = os.getenv("SENSEE_DEBUG_HA_TIMING", "0") == "1"
TV_WAKE_SCRIPT_ENTITY = os.getenv("SENSEE_TV_WAKE_SCRIPT", "script.sensee_tv_power_on").strip()
TV_WAKE_SWITCH_ENTITY = os.getenv("SENSEE_TV_WAKE_SWITCH", "").strip()
TV_WAKE_MAC = os.getenv("SENSEE_TV_WAKE_MAC", "").strip()
TURN_ON_VERIFY_DELAY_SECONDS = float(os.getenv("SENSEE_TURN_ON_VERIFY_DELAY", "0.35"))

_http_client = HAClient(timeout=REQUEST_TIMEOUT)
_volume_send_times: dict[str, float] = {}
_volume_send_lock = threading.Lock()


def get_http_client() -> HAClient:
    """Return the shared Home Assistant HTTP client."""
    return _http_client


def _has_valid_runtime_config(url_base: str, token: str) -> bool:
    """Check whether the Home Assistant runtime credentials are usable."""
    return bool(url_base and token)


def _entity_is_on(state: str) -> bool:
    """Treat common active Home Assistant states as on."""
    return state in ("on", "playing", "idle", "paused")


def _try_tv_wake_fallback(url_base: str, token: str, target_entity_id: str) -> bool:
    """Try alternate wake paths when a TV power-on request does not stick."""
    attempted = False

    if TV_WAKE_SCRIPT_ENTITY:
        attempted = True
        try:
            response, _ = _http_client.post_service(
                url_base,
                token,
                "script",
                "turn_on",
                {"entity_id": TV_WAKE_SCRIPT_ENTITY, "variables": {"target_entity_id": target_entity_id}},
            )
            if response.status_code == 200:
                return True
            logger.warning("TV wake script failed (%s): %s", response.status_code, response.text)
        except requests.exceptions.RequestException as e:
            logger.warning("TV wake script request failed: %s", e)

    if TV_WAKE_SWITCH_ENTITY:
        attempted = True
        try:
            response, _ = _http_client.post_service(
                url_base,
                token,
                "switch",
                "turn_on",
                {"entity_id": TV_WAKE_SWITCH_ENTITY},
            )
            if response.status_code == 200:
                return True
            logger.warning("TV wake switch failed (%s): %s", response.status_code, response.text)
        except requests.exceptions.RequestException as e:
            logger.warning("TV wake switch request failed: %s", e)

    if TV_WAKE_MAC:
        attempted = True
        try:
            response, _ = _http_client.post_service(
                url_base,
                token,
                "wake_on_lan",
                "send_magic_packet",
                {"mac": TV_WAKE_MAC},
            )
            if response.status_code == 200:
                return True
            logger.warning("TV WOL failed (%s): %s", response.status_code, response.text)
        except requests.exceptions.RequestException as e:
            logger.warning("TV WOL request failed: %s", e)

    if not attempted:
        logger.warning("No TV wake fallback configured. Set SENSEE_TV_WAKE_SCRIPT, SENSEE_TV_WAKE_SWITCH, or SENSEE_TV_WAKE_MAC.")

    return False


def trigger_ha_action(entity_id: str, action_type: str) -> bool:
    """Send a Home Assistant service request for the configured entity."""
    if not entity_id:
        logger.error("Home Assistant trigger failed: no entity_id provided.")
        return False

    service = parse_action_to_service(action_type)
    domain = get_domain_from_entity(entity_id)
    url_base, token = get_ha_config()

    if not _has_valid_runtime_config(url_base, token):
        logger.error("Home Assistant config missing. Save URL and token from the mobile app or set SENSEE_HA_URL/SENSEE_HA_TOKEN.")
        return False

    if service in ("volume_up", "volume_down"):
        now = time.monotonic()
        key = f"{entity_id}:{service}"
        with _volume_send_lock:
            last_sent = _volume_send_times.get(key, 0.0)
            if now - last_sent < VOLUME_MIN_INTERVAL_SECONDS:
                return True
            _volume_send_times[key] = now

    data = {"entity_id": entity_id}

    if MOCK_MODE:
        logger.info("MOCK HA: %s -> %s (mapped to '%s')", entity_id, action_type, service)
        return True

    try:
        response, elapsed_ms = _http_client.post_service(url_base, token, domain, service, data)
        if response.status_code == 200:
            if DEBUG_HA_TIMING:
                logger.info("HA accepted %s -> %s in %.1fms", entity_id, service, elapsed_ms)
            else:
                logger.info("HA accepted: %s -> %s", entity_id, service)

            if domain == "media_player" and service == "turn_on":
                _schedule_tv_wake_verify(url_base, token, entity_id)

            return True

        logger.error("HA error %s: %s", response.status_code, response.text)

        if domain == "media_player" and service == "turn_on":
            logger.warning("turn_on failed. Trying wake fallback...")
            _schedule_tv_wake_fallback(url_base, token, entity_id)

        return False
    except requests.exceptions.RequestException as e:
        logger.error("Failed to reach Home Assistant at %s: %s", url_base, e)
        return False


def _schedule_tv_wake_verify(url_base: str, token: str, entity_id: str) -> None:
    """Verify TV state after a delay and run fallback if still off; non-blocking."""
    def _run() -> None:
        time.sleep(TURN_ON_VERIFY_DELAY_SECONDS)
        try:
            state = _http_client.get_entity_state(url_base, token, entity_id)
        except requests.exceptions.RequestException:
            state = None
        if state is None or not _entity_is_on(state):
            logger.warning("TV state after turn_on is '%s'. Trying wake fallback...", state)
            _try_tv_wake_fallback(url_base, token, entity_id)

    threading.Thread(target=_run, name="tv-wake-verify", daemon=True).start()


def _schedule_tv_wake_fallback(url_base: str, token: str, entity_id: str) -> None:
    """Run TV wake fallback in a background thread."""
    threading.Thread(
        target=_try_tv_wake_fallback,
        args=(url_base, token, entity_id),
        name="tv-wake-fallback",
        daemon=True,
    ).start()