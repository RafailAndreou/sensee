import time
from typing import TYPE_CHECKING, Any, Mapping

from gesture_engine.log import get_logger

from .handlers.ha_handler import handle_smart_device_action
from .handlers.ir_handler import handle_ir_device_action
from .handlers.pc_handler import execute_pc_action
from .matching import normalize_name, normalized_parts, find_matched_config

if TYPE_CHECKING:
    from gesture_engine.runtime import GestureRuntime

logger = get_logger(__name__)

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


def build_action_cooldown_key(action_name: str, device_name: str, target_id: str = "") -> str:
    """Build a stable key for per-device/per-action cooldown tracking.

    Args:
        action_name: Action label.
        device_name: Device label.

    Returns:
        Normalized cooldown key.
    """
    return f"{target_id or normalize_name(device_name)}:{normalize_name(action_name)}"


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
    target_id: str = "",
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

    key = build_action_cooldown_key(action_name, device_name, target_id)
    now = time.monotonic()

    with runtime.action_trigger_lock:
        last_trigger_time = runtime.action_trigger_times.get(key)
        if last_trigger_time is not None and now - last_trigger_time < cooldown_seconds:
            return False
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
    event_ts_ms=None,
    source=None,
) -> None:
    """Run a matched configuration through cooldown and routing checks.

    Args:
        runtime: Runtime owning queue/cooldown state.
        matched_config: Config matched to current gesture and hand.
        gesture_name: Gesture name used for logging and notifications.
    """
    action, device_name, connection_type, entity_id, is_volume = _extract_action_context(matched_config)

    target_id = entity_id or str(matched_config.get("id", device_name))
    if event_ts_ms is not None and not runtime.command_is_fresh(event_ts_ms, source):
        return
    if not should_execute_action(runtime, action, device_name, target_id):
        return

    try:
        if get_device_family(device_name) == "pc":
            if source is not None and not runtime.command_is_fresh(event_ts_ms, source):
                return
            accepted = execute_pc_action(action)
        elif connection_type == "smart":
            accepted = handle_smart_device_action(runtime, entity_id, action, is_volume,
                                                  event_ts_ms=event_ts_ms, source=source)
        else:
            accepted = handle_ir_device_action(runtime, entity_id, action, event_ts_ms=event_ts_ms, source=source)
    except Exception as e:
        logger.error("Error dispatching action: %s", e)
        return
    if not accepted:
        return

    now = time.monotonic()
    key = build_action_cooldown_key(action, device_name, target_id)
    with runtime.action_trigger_lock:
        runtime.action_trigger_times[key] = now  # Cooldown begins on accepted dispatch.
    if is_volume:
        logger.debug("Queued volume action: %s %s", device_name, action)
    else:
        logger.info("Dispatched action: %s %s", device_name, action)
    # Feedback is sampled separately from action delivery.
    if now - runtime.last_action_feedback.get(key, float("-inf")) >= 0.25:
        runtime.last_action_feedback[key] = now
        runtime.send_msg(f"{gesture_name} touch detected")
        with runtime.overlay_lock:
            runtime.overlay_label = f"{device_name}  {action}" if device_name else action
            runtime.overlay_ts = now


def take_action(
    runtime: "GestureRuntime",
    gesture_name: str,
    detected_hand: str = "Unknown",
    event_ts_ms=None,
    source=None,
) -> None:
    """Resolve gesture-hand mapping and dispatch the configured action.

    Args:
        runtime: Runtime with active config access.
        gesture_name: Gesture name to resolve.
        detected_hand: Handedness associated with the detection.
    """
    if runtime.find_config is not None:
        matched_config = runtime.find_config(gesture_name, detected_hand)
    else:
        matched_config = find_matched_config(runtime.get_active_configs(), gesture_name, detected_hand)

    if matched_config is None:
        return

    execute_configured_action(runtime, matched_config, gesture_name, event_ts_ms=event_ts_ms, source=source)
