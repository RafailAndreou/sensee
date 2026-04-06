import requests
import json
import os
try:
    from server import file
except ImportError:
    import file

# MOCK MODE: Set this to False when your Home Assistant is actually running!
MOCK_MODE = False

def get_ha_config():
    """Loads the URL and Token dynamically from the config file."""
    config = file.load_ha_config()
    url = config.get("url", "").strip()
    token = config.get("token", "").strip()
    # Fall back to hardcoded values if the config file is empty
    if not url:
        url = "http://172.28.106.37:8123"
    if not token:
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI1ZTI0MTk3YjNjZmE0OWY0ODViMWVhNzNkYjY0ODNmOCIsImlhdCI6MTc3NTQ0NDM4NiwiZXhwIjoyMDkwODA0Mzg2fQ.RUSQ82UgKsvM9zQe-YxmkXdXVWCxOL9ZKY0YIV2l8q4"
    return url, token

# Initial load (can be refreshed by calling get_ha_config again)
HA_URL, HA_TOKEN = get_ha_config()

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

def trigger_ha_action(entity_id: str, action_type: str) -> bool:
    """
    Sends an HTTP POST to Home Assistant to trigger the device.
    """
    if not entity_id:
        print("❌ Home Assistant Trigger Failed: No entity_id provided.")
        return False

    service = parse_action_to_service(action_type)
    domain = get_domain_from_entity(entity_id)

    # Home Assistant API Endpoint structure: /api/services/<domain>/<service>
    url = f"{HA_URL}/api/services/{domain}/{service}"
    
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    
    data = {"entity_id": entity_id}

    if MOCK_MODE:
        print("\n" + "="*50)
        print("🌐 MOCK HOME ASSISTANT TRIGGERED 🌐")
        print(f"📡 Target Device : {entity_id}")
        print(f"⚡  Action        : {action_type} (mapped to '{service}')")
        print("="*50 + "\n")
        return True

    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        if response.status_code == 200:
            print(f"✅ Successfully triggered Home Assistant: {entity_id} -> {service}")
            return True
        else:
            print(f"❌ Home Assistant error {response.status_code}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to reach Home Assistant at {HA_URL}: {e}")
        return False

def get_ha_entities(device_type_filter: str = None):
    """
    Fetches all entities from Home Assistant and formats them for the Sensee UI.
    """
    if MOCK_MODE:
        return [
            {"entity_id": "media_player.living_room_tv", "friendly_name": "Mock Living Room TV", "type": "Tv"},
            {"entity_id": "light.bedroom_lamp", "friendly_name": "Mock Bedroom Lamp", "type": "Light"},
            {"entity_id": "climate.downstairs_ac", "friendly_name": "Mock Living Room AC", "type": "Ac"},
            {"entity_id": "fan.kitchen_fan", "friendly_name": "Mock Kitchen Fan", "type": "Fan"},
        ]

    url = f"{HA_URL}/api/states"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            print(f"❌ HA Fetch Error {response.status_code}: {response.text}")
            return []

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
        
        return formatted_devices

    except Exception as e:
        print(f"❌ Exception fetching entities from Home Assistant: {e}")
        return []

def get_discovered_flows():
    """Fetches discovered devices from Home Assistant that haven't been added yet."""
    url, token = get_ha_config()
    api_url = f"{url}/api/config/config_entries/flow"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        response = requests.get(api_url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"❌ Error fetching discovered flows: {e}")
        return []

def start_pairing_flow(handler: str):
    """Starts a pairing process for a specific device type."""
    url, token = get_ha_config()
    api_url = f"{url}/api/config/config_entries/flow"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"handler": handler}

    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=5)
        return response.json()
    except Exception as e:
        print(f"❌ Error starting pairing flow: {e}")
        return {"error": str(e)}

def submit_pairing_step(flow_id: str, user_input: dict):
    """Submits data (like a PIN) to an active pairing flow."""
    url, token = get_ha_config()
    api_url = f"{url}/api/config/config_entries/flow/{flow_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        response = requests.post(api_url, headers=headers, json=user_input, timeout=5)
        return response.json()
    except Exception as e:
        print(f"❌ Error submitting pairing step: {e}")
        return {"error": str(e)}
