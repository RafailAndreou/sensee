def normalize_name(value):
    return str(value).strip().lower().replace("_", " ").replace("+", " ")


def normalized_parts(value):
    normalized = normalize_name(value)
    return [part for part in normalized.replace("/", " ").split() if part]


def canonical_gesture_name(value):
    normalized = normalize_name(value)
    alias_map = {
        "closed fist": "fist",
        "open palm": "open palm",
        "thumb index": "thumb index",
        "index thumb": "thumb index",
        "thumb middle": "thumb middle",
        "middle thumb": "thumb middle",
    }
    return alias_map.get(normalized, normalized)


def gesture_matches(config_gesture, detected_gesture):
    config_normalized = canonical_gesture_name(config_gesture)
    detected_normalized = canonical_gesture_name(detected_gesture)

    if config_normalized == detected_normalized:
        return True

    config_parts = normalized_parts(config_gesture)
    detected_parts = normalized_parts(detected_gesture)

    if len(config_parts) > 1 and len(config_parts) == len(detected_parts):
        return sorted(config_parts) == sorted(detected_parts)

    return False


def find_matched_config(active_configs, gesture_name, detected_hand="Unknown"):
    for config_item in active_configs:
        config_hand = str(config_item.get("hand", "")).strip().lower()

        hand_match = False
        if "both" in config_hand or not config_hand:
            hand_match = True
        elif "right" in config_hand and "right" in detected_hand.lower():
            hand_match = True
        elif "left" in config_hand and "left" in detected_hand.lower():
            hand_match = True

        if gesture_matches(config_item["gesture"], gesture_name) and hand_match:
            return config_item

    return None
