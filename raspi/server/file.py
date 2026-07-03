import json
import os
import platform
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
IRONMAN_PARAMS_PATH = os.path.join(_data_dir(), "ironman_params.json")
VOICE_SETTINGS_PATH = os.path.join(_data_dir(), "voice_settings.json")


def _default_show_preview() -> bool:
    return platform.system().lower() == "windows"


def _default_camera_settings() -> dict:
    return {
        "useNetwork": False,
        "streamUrl": "",
        "cameraIndex": 0,
        "width": 640,
        "height": 480,
        "fps": 30,
        "showPreview": _default_show_preview(),
    }

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


_IRONMAN_DEFAULTS = {
    "enabled": False,
    "always_track": False,
    "gain": 5000,
    "damp": 50,
    "sensitivity": 3,
    "steps": 10,
    "delay": 0.001,
    "scroll": 10,
    "gesture_map": {
        "move_cursor": "Open Palm",
        "scroll_up": "Victory",
        "scroll_down": "",
        "left_click": "Thumb+Index",
        "right_click": "Thumb+Middle",
        "tab_forward": "Thumb+Ring",
        "tab_backward": "Thumb+Pinky",
        "new_tab": "ILoveYou",
        "task_view": "Closed Fist",
        "browser_forward": "Thumb Up",
        "browser_back": "Thumb Down",
        "browser_search": "Pointing Up",
        "screenshot": "",
        "close_tab": "",
    },
}


def _copy_ironman_defaults() -> dict:
    return {
        **_IRONMAN_DEFAULTS,
        "gesture_map": dict(_IRONMAN_DEFAULTS["gesture_map"]),
    }


def load_ironman_params() -> dict:
    try:
        if not os.path.exists(IRONMAN_PARAMS_PATH):
            return _copy_ironman_defaults()
        with open(IRONMAN_PARAMS_PATH, "r") as f:
            data = json.load(f)
            merged = _copy_ironman_defaults()
            merged.update(data)

            raw_map = data.get("gesture_map")
            if isinstance(raw_map, dict):
                gesture_map = {
                    **_IRONMAN_DEFAULTS["gesture_map"],
                    **raw_map,
                }
            else:
                gesture_map = dict(_IRONMAN_DEFAULTS["gesture_map"])

            legacy_scroll = gesture_map.pop("scroll", "")
            if legacy_scroll and not gesture_map.get("scroll_up"):
                gesture_map["scroll_up"] = legacy_scroll
            gesture_map.setdefault("scroll_down", "")

            merged["gesture_map"] = gesture_map
            return merged
    except Exception as e:
        logger.warning("Error loading Ironman params: %s", e)
        return _copy_ironman_defaults()


def save_ironman_params(params: dict) -> None:
    with open(IRONMAN_PARAMS_PATH, "w+") as f:
        json.dump(params, f, indent=4)
        logger.info("Ironman params saved to %s", IRONMAN_PARAMS_PATH)


_VOICE_DEFAULTS: dict = {
    "enabled": False,
    "model": "tiny",
    "language": "en",
}


def load_voice_settings() -> dict:
    try:
        if not os.path.exists(VOICE_SETTINGS_PATH):
            return dict(_VOICE_DEFAULTS)
        with open(VOICE_SETTINGS_PATH, "r") as f:
            data = json.load(f)
            return {**_VOICE_DEFAULTS, **data}
    except Exception as e:
        logger.warning("Error loading voice settings: %s", e)
        return dict(_VOICE_DEFAULTS)


def save_voice_settings(settings: dict) -> None:
    with open(VOICE_SETTINGS_PATH, "w+") as f:
        json.dump(settings, f, indent=4)
        logger.info("Voice settings saved to %s", VOICE_SETTINGS_PATH)


def save_camera_settings(settings: dict) -> None:
    with open(CAMERA_SETTINGS_PATH, "w+") as f:
        json.dump(settings, f, indent=4)
        logger.info("Camera settings saved to %s", CAMERA_SETTINGS_PATH)


def load_camera_settings() -> dict:
    defaults = _default_camera_settings()
    try:
        if not os.path.exists(CAMERA_SETTINGS_PATH):
            return defaults
        with open(CAMERA_SETTINGS_PATH, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return defaults
            return {**defaults, **data}
    except Exception as e:
        logger.warning("Error loading camera settings: %s", e)
        return defaults
