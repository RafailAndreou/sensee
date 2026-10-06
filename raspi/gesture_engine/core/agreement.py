"""Match queued camera commands to the current uninterrupted hand gesture."""
import threading
from dataclasses import dataclass

from .matching import canonical_gesture_name, canonical_hand_name


@dataclass(frozen=True)
class GestureSource:
    hand: str
    gesture: str
    generation: int
    one_shot: bool


@dataclass
class _HandState:
    gesture: str
    generation: int
    last_match_ms: int
    certain: bool = True


class GestureAgreement:
    def __init__(self, grace_ms=50):
        self.grace_ms = grace_ms
        self._lock = threading.Lock()
        self._states = {}
        self._generation = 0
        self._timestamp = -1

    def clear(self):
        with self._lock:
            self._states.clear()

    def observe(self, gestures_by_hand, timestamp_ms, released=()):
        """None means uncertain recognition; missing hands mean lost tracking.

        Explicit contact releases invalidate a touch even during the grace period.
        """
        observed = {canonical_hand_name(hand): canonical_gesture_name(name) if name else None
                    for hand, name in gestures_by_hand.items()}
        releases = {(canonical_hand_name(hand), canonical_gesture_name(name)) for hand, name in released}
        with self._lock:
            if timestamp_ms <= self._timestamp:
                return
            self._timestamp = timestamp_ms
            for hand in tuple(self._states):
                if hand not in observed:
                    del self._states[hand]
            for hand, gesture in observed.items():
                state = self._states.get(hand)
                if gesture:
                    if (state is None or state.gesture != gesture
                            or not state.certain and timestamp_ms - state.last_match_ms > self.grace_ms):
                        self._generation += 1
                        state = self._states[hand] = _HandState(gesture, self._generation, timestamp_ms)
                    state.last_match_ms, state.certain = timestamp_ms, True
                elif state is not None:
                    if ((hand, state.gesture) in releases
                            or timestamp_ms - state.last_match_ms > self.grace_ms):
                        del self._states[hand]
                    else:
                        state.certain = False

    def capture(self, gesture, hand, one_shot=False):
        hand, gesture = canonical_hand_name(hand), canonical_gesture_name(gesture)
        with self._lock:
            state = self._states.get(hand)
            if state is None or not state.certain or state.gesture != gesture:
                return None
            return GestureSource(hand, gesture, state.generation, one_shot)

    def matches(self, source, now_ms):
        with self._lock:
            state = self._states.get(source.hand)
            return (state is not None and state.generation == source.generation
                    and state.gesture == source.gesture
                    and (state.certain or source.one_shot
                         and now_ms - state.last_match_ms <= self.grace_ms))
