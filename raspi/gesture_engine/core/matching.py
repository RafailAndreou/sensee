from functools import lru_cache


_GESTURE_ALIAS_MAP = {
    "closed fist": "fist",
    "open palm": "open palm",
    "thumb index": "thumb index",
    "index thumb": "thumb index",
    "thumb middle": "thumb middle",
    "middle thumb": "thumb middle",
    "thumb ring": "thumb ring",
    "ring thumb": "thumb ring",
    "thumb pinky": "thumb pinky",
    "pinky thumb": "thumb pinky",
}


def normalize_name(value):
    return str(value).strip().lower().replace("_", " ").replace("+", " ")


@lru_cache(maxsize=128)
def _normalized_parts_tuple(normalized: str):
    return tuple(part for part in normalized.replace("/", " ").split() if part)


def normalized_parts(value):
    normalized = normalize_name(value)
    return list(_normalized_parts_tuple(normalized))


@lru_cache(maxsize=128)
def _canonical_from_normalized(normalized: str):
    return _GESTURE_ALIAS_MAP.get(normalized, normalized)


def canonical_gesture_name(value):
    normalized = normalize_name(value)
    return _canonical_from_normalized(normalized)


def gesture_matches(
    config_gesture,
    detected_gesture,
    detected_normalized=None,
    detected_parts=None,
    detected_parts_sorted=None,
):
    config_normalized = canonical_gesture_name(config_gesture)
    if detected_normalized is None:
        detected_normalized = canonical_gesture_name(detected_gesture)

    if config_normalized == detected_normalized:
        return True

    config_parts = normalized_parts(config_gesture)
    if detected_parts is None:
        detected_parts = normalized_parts(detected_gesture)

    if len(config_parts) > 1 and len(config_parts) == len(detected_parts):
        if detected_parts_sorted is None:
            detected_parts_sorted = tuple(sorted(detected_parts))
        return tuple(sorted(config_parts)) == detected_parts_sorted

    return False


def find_matched_config(active_configs, gesture_name, detected_hand="Unknown"):
    detected_hand_lower = str(detected_hand).strip().lower()
    detected_normalized = canonical_gesture_name(gesture_name)
    detected_parts = normalized_parts(gesture_name)
    detected_parts_sorted = tuple(sorted(detected_parts)) if len(detected_parts) > 1 else None

    for config_item in active_configs:
        config_hand = str(config_item.get("hand", "")).strip().lower()

        hand_match = False
        if "both" in config_hand or not config_hand:
            hand_match = True
        elif "right" in config_hand and "right" in detected_hand_lower:
            hand_match = True
        elif "left" in config_hand and "left" in detected_hand_lower:
            hand_match = True

        if hand_match and gesture_matches(
            config_item["gesture"],
            gesture_name,
            detected_normalized=detected_normalized,
            detected_parts=detected_parts,
            detected_parts_sorted=detected_parts_sorted,
        ):
            return config_item

    return None
