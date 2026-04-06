import requests
import json
import os

# MOCK MODE: Set this to False when your Home Assistant is actually running!
MOCK_MODE = True

# We will load these from environment variables later
HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "YOUR_LONG_LIVED_ACCESS_TOKEN_HERE")

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
