import requests
import json
import os
import threading
import time
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
TV_WAKE_SCRIPT_ENTITY = os.getenv("SENSEE_TV_WAKE_SCRIPT", "script.sensee_tv_power_on").strip()
TV_WAKE_SWITCH_ENTITY = os.getenv("SENSEE_TV_WAKE_SWITCH", "").strip()
TV_WAKE_MAC = os.getenv("SENSEE_TV_WAKE_MAC", "").strip()
TURN_ON_VERIFY_DELAY_SECONDS = float(os.getenv("SENSEE_TURN_ON_VERIFY_DELAY", "0.35"))

_ha_config_cache = {"url": "", "token": ""}
_ha_config_cache_lock = threading.Lock()
_http_session = requests.Session()

_volume_send_times = {}
_volume_send_lock = threading.Lock()

_entities_cache = []
_entities_cache_time = 0.0
_entities_cache_lock = threading.Lock()
_ENTITIES_CACHE_TTL_SECONDS = 2.0

def get_ha_config():
    """Loads the URL and Token dynamically from the config file."""
    with _ha_config_cache_lock:
        if _ha_config_cache["url"] and _ha_config_cache["token"]:
            return _ha_config_cache["url"], _ha_config_cache["token"]

        config = file.load_ha_config()
        url = config.get("url", "").strip()
        token = config.get("token", "").strip()

        # Fall back to hardcoded values if the config file is empty
        if not url:
            url = "http://172.28.106.37:8123"
        if not token:
            token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI1ZTI0MTk3YjNjZmE0OWY0ODViMWVhNzNkYjY0ODNmOCIsImlhdCI6MTc3NTQ0NDM4NiwiZXhwIjoyMDkwODA0Mzg2fQ.RUSQ82UgKsvM9zQe-YxmkXdXVWCxOL9ZKY0YIV2l8q4"

        _ha_config_cache["url"] = url
        _ha_config_cache["token"] = token
        return url, token


def refresh_ha_config_cache():
    with _ha_config_cache_lock:
        _ha_config_cache["url"] = ""
        _ha_config_cache["token"] = ""

def _get_runtime_config():
    return get_ha_config()

def parse_action_to_service(action: str) -> str:
    """Converts Sensee UI actions into Home Assistant service calls."""
    action_lower = action.lower().strip()
    if "turn on" in action_lower:
        return "turn_on"
    elif "turn off" in action_lower:
        return "turn_off"
    elif "increase volume" in action_lower or "volume up" in action_lower:
        return "volume_up"
    elif "decrease volume" in action_lower or "volume down" in action_lower:
        return "volume_down"
    elif "toggle" in action_lower:
        return "toggle"
    else:
        return "turn_on" # default safe fallback

def get_domain_from_entity(entity_id: str) -> str:
    """Extracts the domain (e.g. 'light' from 'light.bedroom')"""
    if "." in entity_id:
        return entity_id.split(".")[0]
    return "homeassistant"


def _post_service(url_base: str, token: str, domain: str, service: str, data: dict):
    url = f"{url_base}/api/services/{domain}/{service}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    started = time.perf_counter()
    response = _http_session.post(url, headers=headers, json=data, timeout=REQUEST_TIMEOUT)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return response, elapsed_ms


def _get_entity_state(url_base: str, token: str, entity_id: str):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = _http_session.get(
            f"{url_base}/api/states/{entity_id}",
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            return None
        return response.json().get("state")
    except requests.exceptions.RequestException:
        return None


def _entity_is_on(state: str) -> bool:
    return state in ("on", "playing", "idle", "paused")


def _try_tv_wake_fallback(url_base: str, token: str, target_entity_id: str) -> bool:
    attempted = False

    if TV_WAKE_SCRIPT_ENTITY:
        attempted = True
        try:
            response, _ = _post_service(
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
            response, _ = _post_service(
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
            response, _ = _post_service(
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
        response, elapsed_ms = _post_service(url_base, token, domain, service, data)
        if response.status_code == 200:
            if DEBUG_HA_TIMING:
                print(f"✅ Home Assistant accepted {entity_id} -> {service} in {elapsed_ms:.1f}ms")
            else:
                print(f"✅ Home Assistant accepted: {entity_id} -> {service}")

            # If TV remains unavailable/off after turn_on, fall back to a wake path.
            if domain == "media_player" and service == "turn_on":
                time.sleep(TURN_ON_VERIFY_DELAY_SECONDS)
                state = _get_entity_state(url_base, token, entity_id)
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
            if device_type_filter:
                return [d for d in _entities_cache if d.get("type", "").lower() == device_type_filter.lower()]
            return list(_entities_cache)

    url_base, token = _get_runtime_config()
    url = f"{url_base}/api/states"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = _http_session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            print(f"❌ HA Fetch Error {response.status_code}: {response.text}")
            with _entities_cache_lock:
                cached = list(_entities_cache)
            if device_type_filter:
                return [d for d in cached if d.get("type", "").lower() == device_type_filter.lower()]
            return cached

        all_states = response.json()
        formatted_devices = []

        # Map HA domains to Sensee Device Types
        domain_map = {
            "media_player": "Tv",
            "light": "Light",
            "switch": "Light",
            "climate": "Ac",
            "fan": "Fan"
        }

        for state in all_states:
            entity_id = state["entity_id"]
            domain = get_domain_from_entity(entity_id)
            
            if domain in domain_map:
                friendly_name = state.get("attributes", {}).get("friendly_name", entity_id)
                sensee_type = domain_map[domain]
                
                # Check if it matches the filter (e.g. if we only want 'Tv')
                if device_type_filter and sensee_type.lower() != device_type_filter.lower():
                    continue

                formatted_devices.append({
                    "entity_id": entity_id,
                    "friendly_name": friendly_name,
                    "type": sensee_type
                })
        
        with _entities_cache_lock:
            _entities_cache[:] = formatted_devices
            _entities_cache_time = now

        if device_type_filter:
            return [d for d in formatted_devices if d.get("type", "").lower() == device_type_filter.lower()]
        return formatted_devices

    except Exception as e:
        print(f"❌ Exception fetching entities from Home Assistant: {e}")
        with _entities_cache_lock:
            cached = list(_entities_cache)
        if device_type_filter:
            return [d for d in cached if d.get("type", "").lower() == device_type_filter.lower()]
        return cached

def get_discovered_flows():
    """Fetches discovered devices from Home Assistant that haven't been added yet."""
    url, token = _get_runtime_config()
    api_url = f"{url}/api/config/config_entries/flow"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        response = _http_session.get(api_url, headers=headers, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"❌ Error fetching discovered flows: {e}")
        return []

def start_pairing_flow(handler: str):
    """Starts a pairing process for a specific device type."""
    url, token = _get_runtime_config()
    api_url = f"{url}/api/config/config_entries/flow"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"handler": handler}

    try:
        response = _http_session.post(api_url, headers=headers, json=data, timeout=REQUEST_TIMEOUT)
        return response.json()
    except Exception as e:
        print(f"❌ Error starting pairing flow: {e}")
        return {"error": str(e)}

def submit_pairing_step(flow_id: str, user_input: dict):
    """Submits data (like a PIN) to an active pairing flow."""
    url, token = _get_runtime_config()
    api_url = f"{url}/api/config/config_entries/flow/{flow_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        response = _http_session.post(api_url, headers=headers, json=user_input, timeout=REQUEST_TIMEOUT)
        return response.json()
    except Exception as e:
        print(f"❌ Error submitting pairing step: {e}")
        return {"error": str(e)}
