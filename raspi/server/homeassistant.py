import requests
import os
import threading
import time
from server.ha_client import HAClient
from server.ha_pairing import (
    fetch_discovered_flows,
    start_pairing_flow_request,
    submit_pairing_step_request,
)
from server.ha_services import get_domain_from_entity, parse_action_to_service
try:
    from server import file
except ImportError:
    import file

# MOCK MODE: Set this to False when your Home Assistant is actually running!
MOCK_MODE = False

# Keep HA calls short so network hiccups don't stall nearby workflows.
REQUEST_TIMEOUT = (0.8, 2.2)
VOLUME_MIN_INTERVAL_SECONDS = float(os.getenv("SENSEE_VOLUME_INTERVAL", "0.05"))
DEBUG_HA_TIMING = os.getenv("SENSEE_DEBUG_HA_TIMING", "0") == "1"
DEFAULT_HA_URL = os.getenv("SENSEE_HA_URL", "").strip()
DEFAULT_HA_TOKEN = os.getenv("SENSEE_HA_TOKEN", "").strip()
TV_WAKE_SCRIPT_ENTITY = os.getenv("SENSEE_TV_WAKE_SCRIPT", "script.sensee_tv_power_on").strip()
TV_WAKE_SWITCH_ENTITY = os.getenv("SENSEE_TV_WAKE_SWITCH", "").strip()
TV_WAKE_MAC = os.getenv("SENSEE_TV_WAKE_MAC", "").strip()
TURN_ON_VERIFY_DELAY_SECONDS = float(os.getenv("SENSEE_TURN_ON_VERIFY_DELAY", "0.35"))

_ha_config_cache = {"url": "", "token": ""}
_ha_config_cache_lock = threading.Lock()
_http_client = HAClient(timeout=REQUEST_TIMEOUT)

_volume_send_times = {}
_volume_send_lock = threading.Lock()

_entities_cache = []
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


def _filter_entities_by_type(devices, device_type_filter=None):
    if not device_type_filter:
        return list(devices)
    wanted = device_type_filter.lower()
    return [d for d in devices if d.get("type", "").lower() == wanted]


def _read_entities_cache(device_type_filter=None):
    with _entities_cache_lock:
        cached = list(_entities_cache)
    return _filter_entities_by_type(cached, device_type_filter)


def _write_entities_cache(devices, cache_time):
    global _entities_cache_time
    with _entities_cache_lock:
        _entities_cache[:] = list(devices)
        _entities_cache_time = cache_time


def _format_states_to_devices(all_states, device_type_filter=None):
    formatted_devices = []

    for state in all_states:
        entity_id = state.get("entity_id", "")
        domain = get_domain_from_entity(entity_id)
        sensee_type = _DOMAIN_TO_SENSEE_TYPE.get(domain)
        if not sensee_type:
            continue

        if device_type_filter and sensee_type.lower() != device_type_filter.lower():
            continue

        friendly_name = state.get("attributes", {}).get("friendly_name", entity_id)
        formatted_devices.append(
            {
                "entity_id": entity_id,
                "friendly_name": friendly_name,
                "type": sensee_type,
            }
        )

    return formatted_devices

def get_ha_config():
    """Load Home Assistant URL/token from saved config, with env fallback only."""
    with _ha_config_cache_lock:
        if _ha_config_cache["url"] and _ha_config_cache["token"]:
            return _ha_config_cache["url"], _ha_config_cache["token"]

        config = file.load_ha_config()
        url = config.get("url", "").strip()
        token = config.get("token", "").strip()

        # Env fallback keeps secrets out of source control.
        if not url:
            url = DEFAULT_HA_URL
        if not token:
            token = DEFAULT_HA_TOKEN

        _ha_config_cache["url"] = url
        _ha_config_cache["token"] = token
        return url, token


def refresh_ha_config_cache():
    with _ha_config_cache_lock:
        _ha_config_cache["url"] = ""
        _ha_config_cache["token"] = ""

def _get_runtime_config():
    return get_ha_config()


def _has_valid_runtime_config(url_base: str, token: str) -> bool:
    return bool(url_base and token)


def _entity_is_on(state: str) -> bool:
    return state in ("on", "playing", "idle", "paused")


def _try_tv_wake_fallback(url_base: str, token: str, target_entity_id: str) -> bool:
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
            print(f"⚠️ TV wake script failed ({response.status_code}): {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ TV wake script request failed: {e}")

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
            print(f"⚠️ TV wake switch failed ({response.status_code}): {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ TV wake switch request failed: {e}")

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
            print(f"⚠️ TV WOL failed ({response.status_code}): {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ TV WOL request failed: {e}")

    if not attempted:
        print("⚠️ No TV wake fallback configured. Set SENSEE_TV_WAKE_SCRIPT, SENSEE_TV_WAKE_SWITCH, or SENSEE_TV_WAKE_MAC.")

    return False

def trigger_ha_action(entity_id: str, action_type: str) -> bool:
    """
    Sends an HTTP POST to Home Assistant to trigger the device.
    """
    if not entity_id:
        print("❌ Home Assistant Trigger Failed: No entity_id provided.")
        return False

    service = parse_action_to_service(action_type)
    domain = get_domain_from_entity(entity_id)
    url_base, token = _get_runtime_config()

    if not _has_valid_runtime_config(url_base, token):
        print("❌ Home Assistant config missing. Save URL and token from the mobile app or set SENSEE_HA_URL/SENSEE_HA_TOKEN.")
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
        print("\n" + "="*50)
        print("🌐 MOCK HOME ASSISTANT TRIGGERED 🌐")
        print(f"📡 Target Device : {entity_id}")
        print(f"⚡  Action        : {action_type} (mapped to '{service}')")
        print("="*50 + "\n")
        return True

    try:
        response, elapsed_ms = _http_client.post_service(url_base, token, domain, service, data)
        if response.status_code == 200:
            if DEBUG_HA_TIMING:
                print(f"✅ Home Assistant accepted {entity_id} -> {service} in {elapsed_ms:.1f}ms")
            else:
                print(f"✅ Home Assistant accepted: {entity_id} -> {service}")

            # If TV remains unavailable/off after turn_on, fall back to a wake path.
            if domain == "media_player" and service == "turn_on":
                time.sleep(TURN_ON_VERIFY_DELAY_SECONDS)
                try:
                    state = _http_client.get_entity_state(url_base, token, entity_id)
                except requests.exceptions.RequestException:
                    state = None
                if state is None or not _entity_is_on(state):
                    print(f"⚠️ TV state after turn_on is '{state}'. Trying wake fallback...")
                    wake_ok = _try_tv_wake_fallback(url_base, token, entity_id)
                    if wake_ok:
                        return True

            return True
        else:
            print(f"❌ Home Assistant error {response.status_code}: {response.text}")

            if domain == "media_player" and service == "turn_on":
                print("⚠️ turn_on failed. Trying wake fallback...")
                wake_ok = _try_tv_wake_fallback(url_base, token, entity_id)
                if wake_ok:
                    return True

            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to reach Home Assistant at {url_base}: {e}")
        return False

def get_ha_entities(device_type_filter: str = None):
    """
    Fetches all entities from Home Assistant and formats them for the Sensee UI.
    """
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

    url_base, token = _get_runtime_config()
    if not _has_valid_runtime_config(url_base, token):
        print("❌ Home Assistant config missing. Cannot fetch entities.")
        return []

    try:
        response = _http_client.get_all_states(url_base, token)
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

def get_discovered_flows():
    """Fetches discovered devices from Home Assistant that haven't been added yet."""
    url, token = _get_runtime_config()
    if not _has_valid_runtime_config(url, token):
        print("❌ Home Assistant config missing. Cannot fetch discovered flows.")
        return []
    try:
        return fetch_discovered_flows(url, token, _http_client.session, _http_client.timeout)
    except Exception as e:
        print(f"❌ Error fetching discovered flows: {e}")
        return []

def start_pairing_flow(handler: str):
    """Starts a pairing process for a specific device type."""
    url, token = _get_runtime_config()
    if not _has_valid_runtime_config(url, token):
        return {"error": "Home Assistant config missing"}
    try:
        return start_pairing_flow_request(url, token, handler, _http_client.session, _http_client.timeout)
    except Exception as e:
        print(f"❌ Error starting pairing flow: {e}")
        return {"error": str(e)}

def submit_pairing_step(flow_id: str, user_input: dict):
    """Submits data (like a PIN) to an active pairing flow."""
    url, token = _get_runtime_config()
    if not _has_valid_runtime_config(url, token):
        return {"error": "Home Assistant config missing"}
    try:
        return submit_pairing_step_request(
            url,
            token,
            flow_id,
            user_input,
            _http_client.session,
            _http_client.timeout,
        )
    except Exception as e:
        print(f"❌ Error submitting pairing step: {e}")
        return {"error": str(e)}
