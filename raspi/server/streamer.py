"""Demand-driven latest-frame JPEG encoding, outside the capture thread."""
import asyncio
from contextlib import contextmanager
import threading
import time
import cv2
import numpy as np
from gesture_engine.log import get_logger

logger = get_logger(__name__)


class FrameHub:
    def __init__(self, max_fps=15):
        self._cond = threading.Condition()
        self._latest_jpeg = None
        self._frame_id = 0
        self._subscribers = 0
        self._pending = None
        self._last_submission = float("-inf")
        self._interval = 1.0 / max_fps
        self._stopped = False
        self._encoder = None

    def start(self):
        with self._cond:
            self._stopped = False

    def has_subscribers(self):
        with self._cond:
            return self._subscribers > 0 and not self._stopped

    def set_bgr_frame(self, bgr: np.ndarray, jpeg_quality=80):
        with self._cond:
            now = time.monotonic()
            if self._stopped or not self._subscribers or now - self._last_submission < self._interval:
                return False
            self._last_submission = now
            self._pending = (bgr.copy(), jpeg_quality)
            if self._encoder is None or not self._encoder.is_alive():
                self._encoder = threading.Thread(target=self._encode, daemon=True, name="PreviewEncoder")
                self._encoder.start()
            self._cond.notify_all()
        return True

    def _encode(self):
        while True:
            with self._cond:
                self._cond.wait_for(lambda: self._pending is not None or self._stopped)
                if self._stopped:
                    return
                frame, quality = self._pending
                self._pending = None
            try:
                ok, jpg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            except Exception:
                logger.exception("Preview encoding failed")
                continue
            if ok:
                data = jpg.tobytes()
                with self._cond:
                    if self._stopped or not self._subscribers:
                        continue
                    self._latest_jpeg = data
                    self._frame_id += 1
                    self._cond.notify_all()

    def close(self):
        with self._cond:
            self._stopped = True
            self._pending = None
            self._latest_jpeg = None
            self._cond.notify_all()
        if self._encoder is not None:
            self._encoder.join(timeout=2)

    @contextmanager
    def _subscription(self):
        with self._cond:
            self._subscribers += 1
            self._cond.notify_all()
        try:
            yield
        finally:
            with self._cond:
                self._subscribers -= 1
                if not self._subscribers:
                    self._pending = None
                    self._latest_jpeg = None
                self._cond.notify_all()

    def _wait_frame(self, last_seen):
        with self._cond:
            self._cond.wait_for(lambda: self._frame_id > last_seen or self._stopped, timeout=1)
            data = self._latest_jpeg if self._frame_id > last_seen else None
            return data, self._frame_id, self._stopped

    @staticmethod
    def _multipart(data):
        if data is None:
            return b""
        return (b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                + str(len(data)).encode() + b"\r\n\r\n" + data + b"\r\n")

    def mjpeg_generator(self):
        last_seen = 0
        with self._subscription():
            while True:
                data, last_seen, stopped = self._wait_frame(last_seen)
                if stopped:
                    return
                yield self._multipart(data)

    async def async_mjpeg_generator(self):
        """Release subscriptions on ASGI disconnect, including while idle."""
        last_seen = 0
        with self._subscription():
            while True:
                data, last_seen, stopped = await asyncio.to_thread(self._wait_frame, last_seen)
                if stopped:
                    return
                yield self._multipart(data)


frame_hub = FrameHub()


def set_frame_from_bgr(frame_bgr):
    return frame_hub.set_bgr_frame(frame_bgr)
