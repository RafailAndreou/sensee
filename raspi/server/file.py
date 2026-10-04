import json
import os
import sys
import copy
import tempfile
import threading

from gesture_engine.log import get_logger

logger = get_logger(__name__)
PERSISTENCE_LOCK = threading.RLock()


# When running as a PyInstaller EXE the bundle root is read-only.
# The runtime hook sets SENSEE_DATA_DIR to the writable folder next to the EXE.
# In normal dev mode we fall back to the directory that contains this file.
def _data_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.environ.get("SENSEE_DATA_DIR", os.path.dirname(sys.executable))
    return os.environ.get("SENSEE_DATA_DIR", os.path.dirname(os.path.abspath(__file__)))

HA_CONFIG_PATH = os.path.join(_data_dir(), "ha_config.json")
CONFIG_FILE_PATH = os.path.join(_data_dir(), "configure.json")
GESTURE_SETTINGS_PATH = os.path.join(_data_dir(), "gesture_settings.json")
CAMERA_SETTINGS_PATH = os.path.join(_data_dir(), "camera_settings.json")
IRONMAN_PARAMS_PATH = os.path.join(_data_dir(), "ironman_params.json")
VOICE_SETTINGS_PATH = os.path.join(_data_dir(), "voice_settings.json")
ACCESS_CONFIG_PATH = os.path.join(_data_dir(), "access_config.json")

def _atomic_write(path: str, content: str) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".sensee-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def _save_json(path: str, value) -> None:
    # Serialize before touching disk: invalid input cannot damage a saved file.
    content = json.dumps(value, indent=4, ensure_ascii=False, allow_nan=False)
    with PERSISTENCE_LOCK:
        try:
            with open(path, encoding="utf-8") as stream:
                previous = stream.read()
            if isinstance(json.loads(previous), type(value)):
                _atomic_write(path + ".bak", previous)
        except FileNotFoundError:
            pass
        except (json.JSONDecodeError, UnicodeError) as error:
            logger.warning("Keeping existing backup of damaged %s: %s", path, error)
        _atomic_write(path, content)
    logger.info("Settings saved to %s", path)


def _load_json(path: str, default):
    with PERSISTENCE_LOCK:
        for candidate in (path, path + ".bak"):
            try:
                with open(candidate, encoding="utf-8") as stream:
                    value = json.load(stream)
                if not isinstance(value, type(default)):
                    raise ValueError("Unexpected JSON structure")
                if candidate != path:
                    logger.warning("Recovered settings from %s", candidate)
                return value
            except FileNotFoundError:
                continue
            except (OSError, ValueError, UnicodeError) as error:
                logger.warning("Cannot load %s: %s", candidate, error)
        return copy.deepcopy(default)


def save_configure_json(configuration: list):
    _save_json(CONFIG_FILE_PATH, configuration)


def load_configure_json() -> list:
    return _load_json(CONFIG_FILE_PATH, [])


def save_ha_config(config: dict):
    _save_json(HA_CONFIG_PATH, config)

def load_ha_config() -> dict:
    try:
        return _load_json(HA_CONFIG_PATH, {"url": "", "token": ""})
    except Exception as e:
        logger.warning("Error loading HA config: %s", e)
        return {"url": "", "token": ""}

def save_gesture_settings(settings: dict) -> None:
    _save_json(GESTURE_SETTINGS_PATH, settings)


def load_gesture_settings() -> dict:
    defaults = {
        "wakeEnabled": False,
        "holdDurationSeconds": 2,
        "activeWindowSeconds": 5,
        "selectedGesture": "Open Hand",
    }
    try:
        return _load_json(GESTURE_SETTINGS_PATH, defaults)
    except Exception as e:
        logger.warning("Error loading gesture settings: %s", e)
        return defaults


def delete_gesture_settings() -> None:
    # Removing both files prevents recovery from re-enabling the wake gate.
    with PERSISTENCE_LOCK:
        for path in (GESTURE_SETTINGS_PATH, GESTURE_SETTINGS_PATH + ".bak"):
            try:
                os.remove(path)
            except FileNotFoundError:
                continue


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
        data = _load_json(IRONMAN_PARAMS_PATH, {})
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
    _save_json(IRONMAN_PARAMS_PATH, params)


_VOICE_DEFAULTS: dict = {
    "enabled": False,
    "model": "tiny",
    "language": "en",
}


def load_voice_settings() -> dict:
    try:
        data = _load_json(VOICE_SETTINGS_PATH, {})
        return {**_VOICE_DEFAULTS, **data}
    except Exception as e:
        logger.warning("Error loading voice settings: %s", e)
        return dict(_VOICE_DEFAULTS)


def save_voice_settings(settings: dict) -> None:
    _save_json(VOICE_SETTINGS_PATH, settings)


def save_camera_settings(settings: dict) -> None:
    _save_json(CAMERA_SETTINGS_PATH, settings)


def load_camera_settings() -> dict:
    try:
        return _load_json(CAMERA_SETTINGS_PATH, {"useNetwork": False, "streamUrl": ""})
    except Exception as e:
        logger.warning("Error loading camera settings: %s", e)
        return {"useNetwork": False, "streamUrl": ""}
