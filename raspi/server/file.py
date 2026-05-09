import json
import os
import sys

from gesture_engine.log import get_logger

logger = get_logger(__name__)


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
CAMERA_SETTINGS_PATH = os.path.join(_data_dir(), "camera_settings.json")

def save_configure_json(configuration: list):
    with open(CONFIG_FILE_PATH, "w+") as f:
        json.dump(configuration, f)
        logger.info("Configuration saved to %s", CONFIG_FILE_PATH)

def load_configure_json() -> list:
    try:
        with open(CONFIG_FILE_PATH, "r") as f:
            content = f.read()
            configuration = json.loads(content)
            logger.info("Configuration loaded from %s", CONFIG_FILE_PATH)
            return configuration
    except FileNotFoundError:
        logger.warning("Configuration file not found, returning empty configuration.")
        return []

def save_ha_config(config: dict):
    with open(HA_CONFIG_PATH, "w+") as f:
        json.dump(config, f, indent=4)
        logger.info("HA configuration saved to %s", HA_CONFIG_PATH)

def load_ha_config() -> dict:
    try:
        if not os.path.exists(HA_CONFIG_PATH):
            return {"url": "", "token": ""}
        with open(HA_CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Error loading HA config: %s", e)
        return {"url": "", "token": ""}

def save_gesture_settings(settings: dict) -> None:
    with open(GESTURE_SETTINGS_PATH, "w+") as f:
        json.dump(settings, f, indent=4)
        logger.info("Gesture settings saved to %s", GESTURE_SETTINGS_PATH)


def load_gesture_settings() -> dict:
    defaults = {
        "wakeEnabled": False,
        "holdDurationSeconds": 2,
        "activeWindowSeconds": 5,
        "selectedGesture": "Open Hand",
    }
    try:
        if not os.path.exists(GESTURE_SETTINGS_PATH):
            return defaults
        with open(GESTURE_SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Error loading gesture settings: %s", e)
        return defaults


def delete_gesture_settings() -> None:
    try:
        if os.path.exists(GESTURE_SETTINGS_PATH):
            os.remove(GESTURE_SETTINGS_PATH)
            logger.info("Gesture settings deleted from %s", GESTURE_SETTINGS_PATH)
    except Exception as e:
        logger.warning("Error deleting gesture settings: %s", e)


def save_camera_settings(settings: dict) -> None:
    with open(CAMERA_SETTINGS_PATH, "w+") as f:
        json.dump(settings, f, indent=4)
        logger.info("Camera settings saved to %s", CAMERA_SETTINGS_PATH)


def load_camera_settings() -> dict:
    try:
        if not os.path.exists(CAMERA_SETTINGS_PATH):
            return {"useNetwork": False, "streamUrl": ""}
        with open(CAMERA_SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Error loading camera settings: %s", e)
        return {"useNetwork": False, "streamUrl": ""}
