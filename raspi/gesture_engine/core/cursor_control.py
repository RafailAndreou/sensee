import time
import threading
from queue import Queue, Empty, Full

import pyautogui

from gesture_engine.log import get_logger
from gesture_engine.core.matching import normalize_name
from gesture_engine.core.handlers.pc_handler import execute_pc_action
from server.models import IronmanParams

logger = get_logger(__name__)

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

_PARAMS_CACHE_TTL = 0.5  # seconds between disk reads
_DIRECTIONAL_SCROLL_BOOST = 3  # Integer speed multiplier for scroll_up/scroll_down.
_ACTION_COOLDOWN_SECONDS = 1.5  # Per-action cooldown for one-shot ironman gestures.


class CursorController:
    """Daemon thread that translates normalized hand positions into smooth cursor movement.

    Velocity-scaling algorithm (ported from Man-Melds-With-Machine):
      - GAIN  : scales raw normalized delta to pixel delta (higher = faster)
      - DAMP  : divides delta when below SENSITIVITY threshold (jitter suppression)
      - SENSITIVITY : dead-zone size in scaled pixels below which damping applies
      - STEPS : number of intermediate moves per frame (smoothness)
      - DELAY : sleep between each interpolation step (seconds)
    """

    def __init__(self, load_params_fn, *, start_thread=True):
        self._load_params_fn = load_params_fn
        self._params_cache: dict = {}
        self._params_cache_ts: float = 0.0
        self._params_lock = threading.Lock()
        self._reverse_map: dict[str, str] = {}  # gesture_name → action_key, rebuilt with params

        self._action_cooldowns: dict[str, float] = {}
        self._action_lock = threading.Lock()

        self.cursor_queue: Queue = Queue(maxsize=2)
        self._stop = threading.Event()
        self._tracking_generation = 0
        self._residual_x = self._residual_y = 0.0

        self._thread = threading.Thread(target=self._run, daemon=True, name="CursorController")
        if start_thread:
            self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1)

    def reset_tracking(self):
        self._tracking_generation += 1
        self._enqueue_latest((0.0, 0.0, "reset"))

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
                try:
                    self._params_cache = IronmanParams.model_validate(self._load_params_fn()).model_dump()
                except (ValueError, TypeError) as error:
                    logger.warning("Invalid cursor settings; disabling cursor control: %s", error)
                    self._params_cache = IronmanParams().model_dump()
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

    def fire_action(self, action_key: str) -> None:
        """Execute a one-shot PC action with per-action cooldown."""
        now = time.monotonic()
        with self._action_lock:
            if now - self._action_cooldowns.get(action_key, 0) < _ACTION_COOLDOWN_SECONDS:
                return
            self._action_cooldowns[action_key] = now
        execute_pc_action(action_key.replace("_", " "))

    def _run(self) -> None:
        prev_x: float | None = None
        prev_y: float | None = None
        prev_mode: str | None = None
        scroll_accum: float = 0.0
        last_scroll_tick: float = 0.0

        while not self._stop.is_set():
            try:
                x, y, mode = self.cursor_queue.get(timeout=0.15)
            except Empty:
                # Gap in position feed — reset position so next entry starts without a jump.
                # For scroll, keep the accumulator alive across brief recognition gaps
                # (MediaPipe may skip frames on slow hardware); for cursor, full reset.
                prev_x = prev_y = None
                self._residual_x = self._residual_y = 0.0
                if prev_mode != "scroll":
                    prev_mode = None
                    scroll_accum = 0.0
                    last_scroll_tick = 0.0
                continue
            except Exception as e:
                logger.error("CursorController queue error: %s", e)
                continue

            try:
                params = self.get_params()
                if mode == "reset" or not params.get("enabled", False):
                    prev_x = prev_y = prev_mode = None
                    self._residual_x = self._residual_y = 0.0
                    scroll_accum = last_scroll_tick = 0.0
                    continue
                if prev_mode != mode:
                    prev_x, prev_y, prev_mode = x, y, mode
                    self._residual_x = self._residual_y = 0.0
                    scroll_accum = last_scroll_tick = 0.0
                    continue
                if prev_x is None:
                    prev_x, prev_y = x, y
                    continue
                if mode == "scroll":
                    scroll_accum = self._do_scroll(y, prev_y, params, scroll_accum)
                elif mode in ("scroll_up", "scroll_down"):
                    last_scroll_tick = self._do_directional_scroll(mode, params, last_scroll_tick)
                else:
                    self._do_cursor(x, y, prev_x, prev_y, params)
                prev_x, prev_y = x, y
            except Exception:
                logger.exception("Cursor processing failed; resetting tracking")
                prev_x = prev_y = prev_mode = None
                self._residual_x = self._residual_y = 0.0

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

        dx += self._residual_x
        dy += self._residual_y
        total_x, total_y = int(dx), int(dy)
        self._residual_x, self._residual_y = dx - total_x, dy - total_y
        if total_x == total_y == 0:
            return
        steps = min(steps, max(abs(total_x), abs(total_y)))
        generation = self._tracking_generation
        sent_x = sent_y = 0
        # Preserve total integer displacement; retain fractional residual across observations.
        for step in range(1, steps + 1):
            if self._stop.is_set() or generation != self._tracking_generation:
                return
            target_x, target_y = round(total_x * step / steps), round(total_y * step / steps)
            try:
                pyautogui.moveRel(target_x - sent_x, target_y - sent_y, _pause=False)
            except Exception as e:
                logger.warning("Cursor move error: %s", e)
                break
            sent_x, sent_y = target_x, target_y
            # Bound interpolation latency to 20 ms, even for large UI slider values.
            if step < steps and self._stop.wait(min(delay, 0.02 / steps)):
                return

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
