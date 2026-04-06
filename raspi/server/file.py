import json
import os
import copy

HA_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "ha_config.json")
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "configure.json")

def save_configure_json(configuration: dict):
    with open(CONFIG_FILE_PATH, "w+") as f:
        f.write(json.dumps(configuration))
        print(f"✅ Configuration saved to {CONFIG_FILE_PATH}")
       
def load_configure_json() -> list:
    try:
        with open(CONFIG_FILE_PATH, "r") as f:
            content = f.read()
            configuration = json.loads(content)
            print(f"✅ Configuration loaded from {CONFIG_FILE_PATH}")
            return configuration
    except FileNotFoundError:
        print("⚠️  Configuration file not found, returning empty configuration.")
        return []

def save_ha_config(config: dict):
    with open(HA_CONFIG_PATH, "w+") as f:
        json.dump(config, f, indent=4)
        print(f"✅ HA Configuration saved to {HA_CONFIG_PATH}")

def load_ha_config() -> dict:
    try:
        if not os.path.exists(HA_CONFIG_PATH):
            return {"url": "", "token": ""}
        with open(HA_CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading HA config: {e}")
        return {"url": "", "token": ""}

loaded_config = load_configure_json()

def _is_valid_config_item(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    if str(item.get("id", "")).strip() in ("", "-1"):
        return False
    if not str(item.get("gesture", "")).strip():
        return False
    if not str(item.get("action", "")).strip():
        return False
    return True

def get_active_configs() -> list:
    return [item for item in loaded_config if _is_valid_config_item(item)]
    
if __name__ == "__main__":
    test_dictionary = {
        "setting1": True,
        "setting2": "value",
        "setting3": 42
    }
    loaded_config = load_configure_json()
    print(type(loaded_config))
    for i in loaded_config:
        if i["gesture"]=="Thumb+Index":
            print(i["action"])
            