import time
from typing import TYPE_CHECKING, Any, Mapping

from .handlers.ha_handler import handle_smart_device_action
from .handlers.ir_handler import handle_ir_device_action
from .handlers.pc_handler import execute_pc_action
from .matching import normalize_name, normalized_parts, find_matched_config

if TYPE_CHECKING:
    from gesture_engine.runtime import GestureRuntime

CONTROL_ACTION_COOLDOWN_SECONDS = 1.5


def _safe_str(value: Any) -> str:
    """Normalize arbitrary config values to strings for resilient action parsing.

    Args:
        value: Raw config field value.

    Returns:
        String representation safe for normalization/matching.
    """
    return str(value or "")


def get_device_family(value: str) -> str:
    """Extract the leading device family token for routing decisions.

    Args:
        value: User/device label from config.

    Returns:
        Lowercased normalized family key (for example `pc`, `tv`, `ac`).
    """
    parts = normalized_parts(value)
    if not parts:
        return ""
    return parts[0]


def build_action_cooldown_key(action_name: str, device_name: str) -> str:
    """Build a stable key for per-device/per-action cooldown tracking.

    Args:
        action_name: Action label.
        device_name: Device label.

    Returns:
        Normalized cooldown key.
    """
    return f"{normalize_name(device_name)}:{normalize_name(action_name)}"


def action_cooldown_seconds(
    runtime: "GestureRuntime",
    action_name: str,
    device_name: str,
) -> float:
    """Decide cooldown duration so held gestures do not spam actions.

    Args:
        runtime: Runtime carrying policy thresholds.
        action_name: Requested action string.
        device_name: Configured device name.

    Returns:
        Cooldown duration in seconds.
    """
    action_normalized = normalize_name(action_name)
    if "volume" in action_normalized:
        return 0.0

    device_family = get_device_family(device_name)
    if device_family == "pc":
        return runtime.policy.action_cooldowns["pc"]

    for keyword in runtime.policy.control_action_keywords:
        if keyword in action_normalized:
            return CONTROL_ACTION_COOLDOWN_SECONDS

    return runtime.policy.action_cooldowns.get(device_family, 0.0)


def should_execute_action(
    runtime: "GestureRuntime",
    action_name: str,
    device_name: str,
) -> bool:
    """Apply cooldown checks to prevent repeated action bursts.

    Args:
        runtime: Runtime with cooldown state.
        action_name: Requested action name.
        device_name: Target device name.

    Returns:
        `True` when action execution is allowed now.
    """
    cooldown_seconds = action_cooldown_seconds(runtime, action_name, device_name)
    if cooldown_seconds <= 0:
        return True

    key = build_action_cooldown_key(action_name, device_name)
    now = time.monotonic()

    with runtime.action_trigger_lock:
        last_trigger_time = runtime.action_trigger_times.get(key, 0)
        if now - last_trigger_time < cooldown_seconds:
            return False

        runtime.action_trigger_times[key] = now
        return True


def _extract_action_context(matched_config: Mapping[str, Any]) -> tuple[str, str, str, str, bool]:
    """Extract normalized action-routing fields from a matched config.

    Args:
        matched_config: Selected configuration mapping.

    Returns:
        Tuple `(action, device_name, connection_type, entity_id, is_volume)`.
    """
    action = _safe_str(matched_config.get("action", ""))
    device_name = _safe_str(matched_config.get("sound", ""))
    connection_type = _safe_str(matched_config.get("connectionType", "ir")).strip().lower()
    entity_id = _safe_str(matched_config.get("entityId", ""))
    is_volume = "volume" in normalize_name(action)
    return action, device_name, connection_type, entity_id, is_volume


def execute_configured_action(
    runtime: "GestureRuntime",
    matched_config: Mapping[str, Any],
    gesture_name: str,
) -> None:
    """Run a matched configuration through cooldown and routing checks.

    Args:
        runtime: Runtime owning queue/cooldown state.
        matched_config: Config matched to current gesture and hand.
        gesture_name: Gesture name used for logging and notifications.
    """
    action, device_name, connection_type, entity_id, is_volume = _extract_action_context(matched_config)

    if not should_execute_action(runtime, action, device_name):
        return

    runtime.send_msg(f"{gesture_name} touch detected")
    print(f"Executing action: {device_name} {action}")
    with runtime.overlay_lock:
        runtime.overlay_label = f"{device_name}  {action}" if device_name else action
        runtime.overlay_ts = time.monotonic()

    if get_device_family(device_name) == "pc":
        execute_pc_action(action)
        return

    if connection_type == "smart":
        try:
            handle_smart_device_action(runtime, entity_id, action, is_volume)
        except Exception as e:
            print(f"Error queueing Home Assistant action: {e}")
        return

    # Handle IR devices (volume and non-volume actions)
    try:
        handle_ir_device_action(runtime, entity_id, action)
    except Exception as e:
        print(f"Error queueing IR action: {e}")


def take_action(
    runtime: "GestureRuntime",
    gesture_name: str,
    detected_hand: str = "Unknown",
) -> None:
    """Resolve gesture-hand mapping and dispatch the configured action.

    Args:
        runtime: Runtime with active config access.
        gesture_name: Gesture name to resolve.
        detected_hand: Handedness associated with the detection.
    """
    active_configs = runtime.get_active_configs()
    matched_config = find_matched_config(active_configs, gesture_name, detected_hand)

    if matched_config is None:
        return

    execute_configured_action(runtime, matched_config, gesture_name)
