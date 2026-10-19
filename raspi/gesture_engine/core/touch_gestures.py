"""Touch gesture detection and helpers (Thumb+Index, Thumb+Middle)."""

from __future__ import annotations

from gesture_engine.core.matching import normalize_name
from gesture_engine.geometry import touching

TOUCH_XY_THRESHOLD = 0.05
TOUCH_Z_THRESHOLD = 0.02
TOUCH_CONFIRM_FRAMES = 2
TOUCH_RELEASE_MARGIN = 1.2
CONFIRMATION_ACTION_KEYWORDS = (
    "turn on",
    "turn off",
    "open",
    "close",
    "toggle",
    "brightness",
    "fan speed",
    "temperature",
    "activate",
)


def action_requires_confirmation(action_name: str) -> bool:
    normalized_action = normalize_name(action_name)
    if "volume" in normalized_action:
        return False
    return any(keyword in normalized_action for keyword in CONFIRMATION_ACTION_KEYWORDS)


def detect_touch_gestures(hand_landmarks, calibration=None, aspect=1.0, *, release=False) -> list[tuple[str, bool]]:
    """Return [(gesture_name, is_touching), ...] for thumb-finger contacts.

    Priority chain: Pinky > Ring > Middle > Index. Each higher-priority touch
    suppresses lower-priority ones to prevent co-firing as the thumb sweeps.
    """
    landmarks = getattr(hand_landmarks, "landmark", hand_landmarks)
    margin = TOUCH_RELEASE_MARGIN if release else 1
    found = False
    result = []
    for name, index in (("Thumb+Pinky", 20), ("Thumb+Ring", 16),
                        ("Thumb+Middle", 12), ("Thumb+Index", 8)):
        if calibration and calibration.get('enabled'):
            from gesture_engine.calibration import contact_distance
            xy, z = contact_distance(landmarks, index, aspect)
            active = xy <= calibration['contactRatio']*margin and z <= calibration['depthRatio']*margin
        else:
            active = touching(landmarks[4], landmarks[index], threshold=TOUCH_XY_THRESHOLD*margin,
                              z_threshold=TOUCH_Z_THRESHOLD*margin)
        result.append((name, active and (release or not found)))
        found = found or active
    return result


def snapshot_to_multi_hand_landmarks(snapshot):
    from mediapipe.framework.formats import landmark_pb2

    if not snapshot or not snapshot.hand_landmarks:
        return None

    multi_hand_landmarks = []
    for hand in snapshot.hand_landmarks:
        proto = landmark_pb2.NormalizedLandmarkList()  # type: ignore
        proto.landmark.extend(
            [landmark_pb2.NormalizedLandmark(x=l.x, y=l.y, z=l.z) for l in hand]  # type: ignore
        )
        multi_hand_landmarks.append(proto)

    return multi_hand_landmarks if multi_hand_landmarks else None


def clear_touch_releases(hand_landmarks):
    """Separate definite releases from small contact-threshold fluctuations."""
    landmarks = getattr(hand_landmarks, "landmark", hand_landmarks)
    return [name for name, index in (("Thumb+Pinky", 20), ("Thumb+Ring", 16),
                                     ("Thumb+Middle", 12), ("Thumb+Index", 8))
            if not touching(landmarks[4], landmarks[index],
                            threshold=TOUCH_XY_THRESHOLD * TOUCH_RELEASE_MARGIN,
                            z_threshold=TOUCH_Z_THRESHOLD * TOUCH_RELEASE_MARGIN)]


def resolve_detected_hand(snapshot, hand_idx: int) -> str:
    if (
        snapshot
        and snapshot.handedness
        and hand_idx < len(snapshot.handedness)
        and snapshot.handedness[hand_idx]
    ):
        return snapshot.handedness[hand_idx][0].category_name
    return "Unknown"
