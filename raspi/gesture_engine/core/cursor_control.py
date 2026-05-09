import time
import threading
from queue import Queue, Empty

import pyautogui

from gesture_engine.log import get_logger

logger = get_logger(__name__)

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

_PARAMS_CACHE_TTL = 0.5  # seconds between disk reads


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

        self.cursor_queue: Queue = Queue(maxsize=2)

        self._thread = threading.Thread(target=self._run, daemon=True, name="CursorController")
        self._thread.start()

    def feed(self, x: float, y: float) -> None:
        """Push a normalized (0–1) landmark position. Drops oldest if full."""
        try:
            self.cursor_queue.put_nowait((x, y, "cursor"))
        except Exception:
            pass

    def feed_scroll(self, x: float, y: float) -> None:
        """Push a position for scroll mode."""
        try:
            self.cursor_queue.put_nowait((x, y, "scroll"))
        except Exception:
            pass

    def _get_params(self) -> dict:
        now = time.monotonic()
        with self._params_lock:
            if now - self._params_cache_ts > _PARAMS_CACHE_TTL:
                self._params_cache = self._load_params_fn()
                self._params_cache_ts = now
            return self._params_cache

    def _run(self) -> None:
        prev_x: float | None = None
        prev_y: float | None = None
        prev_mode: str | None = None
        scroll_accum: float = 0.0

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
                continue
            except Exception as e:
                logger.error("CursorController queue error: %s", e)
                continue

            params = self._get_params()
            if not params.get("enabled", False):
                prev_x, prev_y = x, y
                continue

            if prev_mode != mode:
                # Mode changed: full reset.
                prev_x, prev_y = x, y
                prev_mode = mode
                scroll_accum = 0.0
                continue

            if prev_x is None:
                # Re-entering after a gap: re-anchor position but keep scroll accum.
                prev_x, prev_y = x, y
                continue

            if mode == "scroll":
                scroll_accum = self._do_scroll(y, prev_y, params, scroll_accum)
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
