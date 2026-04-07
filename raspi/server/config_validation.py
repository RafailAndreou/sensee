def _normalize_config_value(value: str) -> str:
    return str(value).strip().lower()


def _normalize_hand_value(value: str) -> str:
    normalized = _normalize_config_value(value)
    if "both" in normalized:
        return "both hands"
    if "left" in normalized:
        return "left hand"
    if "right" in normalized:
        return "right hand"
    return normalized


def _find_duplicate_gesture_hand(configs: list[dict]):
    seen: dict[tuple[str, str], dict] = {}
    for config in configs:
        gesture = _normalize_config_value(config.get("gesture", ""))
        hand = _normalize_config_value(config.get("hand", ""))
        key = (gesture, hand)

        if key in seen:
            return seen[key], config

        seen[key] = config

    return None, None


def _find_invalid_hand_combination(configs: list[dict]):
    gesture_to_hands: dict[str, set[str]] = {}
    for config in configs:
        gesture = _normalize_config_value(config.get("gesture", ""))
        hand = _normalize_hand_value(config.get("hand", ""))
        if not gesture or not hand:
            continue

        hands = gesture_to_hands.setdefault(gesture, set())
        hands.add(hand)

    for gesture, hands in gesture_to_hands.items():
        if "both hands" in hands and ("left hand" in hands or "right hand" in hands):
            return gesture, hands

    return None, None


def validate_configuration_payload(configs: list[dict]) -> str | None:
    first, second = _find_duplicate_gesture_hand(configs)
    if first and second:
        gesture = second.get("gesture", "")
        hand = second.get("hand", "")
        return f"Duplicate gesture+hand mapping is not allowed: {gesture} / {hand}"

    invalid_gesture, invalid_hands = _find_invalid_hand_combination(configs)
    if invalid_gesture and invalid_hands:
        return (
            "Invalid hand combination for gesture "
            f"'{invalid_gesture}': Both Hands cannot coexist with Left/Right Hand mappings"
        )

    return None
