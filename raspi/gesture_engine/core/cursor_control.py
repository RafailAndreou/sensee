import time
import threading
from queue import Queue, Empty, Full

import pyautogui

from gesture_engine.log import get_logger
from gesture_engine.core.matching import normalize_name

logger = get_logger(__name__)

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

_PARAMS_CACHE_TTL = 0.5  # seconds between disk reads
_DIRECTIONAL_SCROLL_BOOST = 3  # Integer speed multiplier for scroll_up/scroll_down.


class CursorController:
    """Daemon thread that translates normalized hand positions into smooth cursor movement.

    Velocity-scaling algorithm (ported from Man-Melds-With-Machine):
      - GAIN  : scales raw normalized delta to pixel delta (higher = faster)
      - DAMP  : divides delta when below SENSITIVITY threshold (jitter suppression)
      - SENSITIVITY : dead-zone size in scaled pixels below which damping applies
      - STEPS : number of intermediate moves per frame (smoothness)
      - DELAY : sleep between each interpolation step (seconds)
    """

    def __init__(self, load_params_fn):
        self._load_params_fn = load_params_fn
        self._params_cache: dict = {}
        self._params_cache_ts: float = 0.0
        self._params_lock = threading.Lock()
        self._reverse_map: dict[str, str] = {}  # gesture_name → action_key, rebuilt with params

        self.cursor_queue: Queue = Queue(maxsize=2)

        self._thread = threading.Thread(target=self._run, daemon=True, name="CursorController")
        self._thread.start()

    def feed(self, x: float, y: float) -> None:
        """Push a normalized (0–1) landmark position. Drops oldest if full."""
        self._enqueue_latest((x, y, "cursor"))

    def feed_scroll(self, x: float, y: float) -> None:
        """Legacy continuous scroll mode based on wrist movement."""
        self._enqueue_latest((x, y, "scroll"))

    def feed_scroll_up(self) -> None:
        """Push a request for directional scroll up mode."""
        self._enqueue_latest((0.0, 0.0, "scroll_up"))

    def feed_scroll_down(self) -> None:
        """Push a request for directional scroll down mode."""
        self._enqueue_latest((0.0, 0.0, "scroll_down"))

    def _enqueue_latest(self, item: tuple[float, float, str]) -> None:
        try:
            self.cursor_queue.put_nowait(item)
            return
        except Full:
            try:
                self.cursor_queue.get_nowait()
            except Empty:
                logger.debug("Cursor queue reported full but had no item to drop")
        try:
            self.cursor_queue.put_nowait(item)
        except Full:
            logger.debug("Cursor queue still full after dropping stale item")

    def get_params(self) -> dict:
        now = time.monotonic()
        with self._params_lock:
            if now - self._params_cache_ts > _PARAMS_CACHE_TTL:
                self._params_cache = self._load_params_fn()
                self._params_cache_ts = now
                gesture_map = self._params_cache.get("gesture_map", {})
                self._reverse_map = {
                    normalize_name(gname): action_key
                    for action_key, gname in gesture_map.items()
                    if gname
                }
            return self._params_cache

    def resolve_action(self, gesture_name: str) -> str | None:
        """Return the ironman action key for this gesture, or None if disabled/unmatched."""
        params = self.get_params()
        if not params.get("enabled", False):
            return None
        return self._reverse_map.get(normalize_name(gesture_name))

    def _run(self) -> None:
        prev_x: float | None = None
        prev_y: float | None = None
        prev_mode: str | None = None
        scroll_accum: float = 0.0
        last_scroll_tick: float = 0.0

        while True:
            try:
                x, y, mode = self.cursor_queue.get(timeout=0.15)
            except Empty:
                # Gap in position feed — reset position so next entry starts without a jump.
                # For scroll, keep the accumulator alive across brief recognition gaps
                # (MediaPipe may skip frames on slow hardware); for cursor, full reset.
                prev_x = prev_y = None
                if prev_mode != "scroll":
                    prev_mode = None
                    scroll_accum = 0.0
                    last_scroll_tick = 0.0
                continue
            except Exception as e:
                logger.error("CursorController queue error: %s", e)
                continue

            params = self.get_params()
            if not params.get("enabled", False):
                prev_x, prev_y = x, y
                continue

            if prev_mode != mode:
                # Mode changed: full reset.
                prev_x, prev_y = x, y
                prev_mode = mode
                scroll_accum = 0.0
                last_scroll_tick = 0.0
                continue

            if prev_x is None:
                # Re-entering after a gap: re-anchor position but keep scroll accum.
                prev_x, prev_y = x, y
                continue

            if mode == "scroll":
                scroll_accum = self._do_scroll(y, prev_y, params, scroll_accum)
            elif mode in ("scroll_up", "scroll_down"):
                last_scroll_tick = self._do_directional_scroll(
                    mode=mode,
                    params=params,
                    last_tick=last_scroll_tick,
                )
            else:
                self._do_cursor(x, y, prev_x, prev_y, params)

            prev_x, prev_y = x, y

    def _do_cursor(self, x, y, prev_x, prev_y, params):
        gain = params.get("gain", 5000)
        damp = max(params.get("damp", 50), 1)
        sensitivity = params.get("sensitivity", 3)
        steps = max(params.get("steps", 10), 1)
        delay = params.get("delay", 0.001)

        # Negate dx: landmarks are in un-mirrored camera space, so moving
        # your hand right decreases x. Flip it so cursor follows the preview.
        dx = -(x - prev_x) * gain
        dy = (y - prev_y) * gain

        if abs(dx) < sensitivity and abs(dy) < sensitivity:
            dx /= damp
            dy /= damp

        step_x = dx / steps
        step_y = dy / steps

        for _ in range(steps):
            try:
                pyautogui.moveRel(step_x, step_y, _pause=False)
            except Exception as e:
                logger.warning("Cursor move error: %s", e)
                break
            time.sleep(delay)

    def _do_scroll(self, y, prev_y, params, accum: float) -> float:
        scroll_speed = max(params.get("scroll", 10), 1)
        # Positive dy → hand moved up → scroll up.
        dy = (prev_y - y) * 1000
        accum += dy
        # Fire only when enough has accumulated — avoids int(small/speed)=0 every frame.
        if abs(accum) < scroll_speed:
            return accum
        clicks = int(accum / scroll_speed)
        if clicks == 0:
            return accum
        try:
            pyautogui.scroll(clicks, _pause=False)
        except Exception as e:
            logger.warning("Scroll error: %s", e)
        return accum - clicks * scroll_speed

    def _do_directional_scroll(self, mode: str, params: dict, last_tick: float) -> float:
        scroll_speed = max(min(params.get("scroll", 10), 50), 1)
        now = time.monotonic()
        boost = _DIRECTIONAL_SCROLL_BOOST

        # Higher slider value => much faster scrolling (both frequency and amount).
        speed_ratio = (scroll_speed - 1) / 49
        interval = max(0.001, (0.06 - (0.052 * speed_ratio)) / boost)  # 60..8 ms / boost
        if now - last_tick < interval:
            return last_tick

        clicks = max(1, int((4 + (24 * speed_ratio)) * boost))  # (4 .. 28) * boost

        direction = 1 if mode == "scroll_up" else -1
        try:
            pyautogui.scroll(direction * clicks, _pause=False)
        except Exception as e:
            logger.warning("Directional scroll error: %s", e)
        return now
