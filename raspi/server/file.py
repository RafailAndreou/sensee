import json
import os
import sys

# When running as a PyInstaller EXE the bundle root is read-only.
# The runtime hook sets SENSEE_DATA_DIR to the writable folder next to the EXE.
# In normal dev mode we fall back to the directory that contains this file.
def _data_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.environ.get("SENSEE_DATA_DIR", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

HA_CONFIG_PATH = os.path.join(_data_dir(), "ha_config.json")
CONFIG_FILE_PATH = os.path.join(_data_dir(), "configure.json")
GESTURE_SETTINGS_PATH = os.path.join(_data_dir(), "gesture_settings.json")

def save_configure_json(configuration: list):
    with open(CONFIG_FILE_PATH, "w+") as f:
        json.dump(configuration, f)
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

_loaded_config = load_configure_json()


def get_loaded_config() -> list:
    return list(_loaded_config)


def set_loaded_config(configuration: list):
    global _loaded_config
    _loaded_config = list(configuration) if isinstance(configuration, list) else []


def reload_config_cache() -> list:
    global _loaded_config
    _loaded_config = load_configure_json()
    return list(_loaded_config)

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
    return [item for item in _loaded_config if _is_valid_config_item(item)]


def save_gesture_settings(settings: dict) -> None:
    with open(GESTURE_SETTINGS_PATH, "w+") as f:
        json.dump(settings, f, indent=4)
        print(f"✅ Gesture settings saved to {GESTURE_SETTINGS_PATH}")


def load_gesture_settings() -> dict:
    try:
        if not os.path.exists(GESTURE_SETTINGS_PATH):
            return {
                "wakeEnabled": False,
                "holdDurationSeconds": 2,
                "activeWindowSeconds": 5,
                "selectedGesture": "Open Hand",
            }
        with open(GESTURE_SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading gesture settings: {e}")
        return {
            "wakeEnabled": False,
            "holdDurationSeconds": 2,
            "activeWindowSeconds": 5,
            "selectedGesture": "Open Hand",
        }


def delete_gesture_settings() -> None:
    try:
        if os.path.exists(GESTURE_SETTINGS_PATH):
            os.remove(GESTURE_SETTINGS_PATH)
            print(f"✅ Gesture settings deleted from {GESTURE_SETTINGS_PATH}")
    except Exception as e:
        print(f"⚠️ Error deleting gesture settings: {e}")