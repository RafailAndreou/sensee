import threading
import time
import webbrowser
from queue import Empty

import pyautogui

from .matching import normalize_name, normalized_parts, find_matched_config


def device_key(value):
    parts = normalized_parts(value)
    if not parts:
        return ""
    return parts[0]


def action_key(action_name, device_name):
    return f"{normalize_name(device_name)}:{normalize_name(action_name)}"


def action_cooldown_seconds(runtime, action_name, device_name):
    action_normalized = normalize_name(action_name)
    if "volume" in action_normalized:
        return 0.0

    if device_key(device_name) == "pc":
        return runtime.action_cooldowns["pc"]

    for keyword in runtime.control_action_keywords:
        if keyword in action_normalized:
            return 1.5

    return runtime.action_cooldowns.get(device_key(device_name), 0.0)


def can_run_action(runtime, action_name, device_name):
    cooldown_seconds = action_cooldown_seconds(runtime, action_name, device_name)
    if cooldown_seconds <= 0:
        return True

    key = action_key(action_name, device_name)
    now = time.monotonic()

    with runtime.action_trigger_lock:
        last_trigger_time = runtime.action_trigger_times.get(key, 0)
        if now - last_trigger_time < cooldown_seconds:
            return False

        runtime.action_trigger_times[key] = now
        return True


def open_url(url):
    try:
        webbrowser.open_new_tab(url)
        return True
    except Exception as e:
        print(f"Failed to open URL {url}: {e}")
        return False


def execute_pc_action(action_name):
    action_normalized = normalize_name(action_name)

    if action_normalized == "open spotify":
        return open_url("https://open.spotify.com/")

    if action_normalized == "open youtube":
        return open_url("https://www.youtube.com/")

    if action_normalized == "open browser":
        return open_url("https://www.google.com/")

    if action_normalized == "close window":
        try:
            pyautogui.hotkey("alt", "f4")
            return True
        except Exception as e:
            print(f"Failed to close active window: {e}")
            return False

    print(f"Unsupported PC action: {action_name}")
    return False


def trigger_matched_config(runtime, matched_config, gesture_name, detected_hand="Unknown"):
    if matched_config is None:
        return

    action = str(matched_config.get("action", ""))
    device_name = str(matched_config.get("sound", ""))
    connection_type = str(matched_config.get("connectionType", "ir")).strip().lower()
    entity_id = str(matched_config.get("entityId", ""))
    is_volume = "volume" in normalize_name(action)

    if not can_run_action(runtime, action, device_name):
        return

    runtime.send_msg(f"{gesture_name} touch detected")
    print(f"Executing action: {device_name} {action}")

    if device_key(device_name) == "pc":
        execute_pc_action(action)
        return

    if connection_type == "smart":
        if is_volume:
            threading.Thread(
                target=runtime.trigger_ha_action,
                args=(entity_id, action),
                daemon=True,
            ).start()
            return

        try:
            if runtime.ha_action_queue.full():
                try:
                    runtime.ha_action_queue.get_nowait()
                except Empty:
                    pass
            runtime.ha_action_queue.put_nowait((entity_id, action))
        except Exception as e:
            print(f"Error queueing Home Assistant action: {e}")
        return


def take_action(runtime, gesture_name, detected_hand="Unknown"):
    active_configs = runtime.get_active_configs()
    matched_config = find_matched_config(active_configs, gesture_name, detected_hand)

    if matched_config is None:
        return

    trigger_matched_config(runtime, matched_config, gesture_name, detected_hand)
