"""Touch gesture detection and helpers (Thumb+Index, Thumb+Middle)."""

from __future__ import annotations

from mediapipe.framework.formats import landmark_pb2

from gesture_engine.core.matching import normalize_name
from gesture_engine.geometry import touching

TOUCH_XY_THRESHOLD = 0.05
TOUCH_Z_THRESHOLD = 0.02
TOUCH_CONFIRM_FRAMES = 2
CONFIRMATION_ACTION_KEYWORDS = (
    "turn on",
    "turn off",
    "open",
    "close",
    "toggle",
)


def action_requires_confirmation(action_name: str) -> bool:
    normalized_action = normalize_name(action_name)
    if "volume" in normalized_action:
        return False
    return any(keyword in normalized_action for keyword in CONFIRMATION_ACTION_KEYWORDS)


def detect_touch_gestures(hand_landmarks) -> list[tuple[str, bool]]:
    """Return [(gesture_name, is_touching), ...] for thumb-finger contacts.

    Order matters: Thumb+Middle is checked first; if active it suppresses
    Thumb+Index to avoid co-firing while the thumb crosses both fingers.
    """
    thumb = hand_landmarks.landmark[4]
    index = hand_landmarks.landmark[8]
    middle = hand_landmarks.landmark[12]

    middle_touching = touching(
        thumb,
        middle,
        threshold=TOUCH_XY_THRESHOLD,
        z_threshold=TOUCH_Z_THRESHOLD,
    )
    index_touching = (
        False
        if middle_touching
        else touching(
            thumb,
            index,
            threshold=TOUCH_XY_THRESHOLD,
            z_threshold=TOUCH_Z_THRESHOLD,
        )
    )
    return [
        ("Thumb+Middle", middle_touching),
        ("Thumb+Index", index_touching),
    ]


def snapshot_to_multi_hand_landmarks(snapshot):
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


def resolve_detected_hand(snapshot, hand_idx: int) -> str:
    if (
        snapshot
        and snapshot.handedness
        and hand_idx < len(snapshot.handedness)
        and snapshot.handedness[hand_idx]
    ):
        return snapshot.handedness[hand_idx][0].category_name
    return "Unknown"
