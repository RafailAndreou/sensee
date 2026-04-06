import threading
import time
import cv2
import numpy as np

class FrameHub:
    """Thread-safe place to publish latest JPEG for MJPEG streaming."""
    def __init__(self):
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._latest_jpeg: bytes | None = None

    def set_bgr_frame(self, bgr: np.ndarray, jpeg_quality: int = 80):
        ok, jpg = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])
        if not ok:
            return
        with self._lock:
            self._latest_jpeg = jpg.tobytes()
            self._event.set()

    def mjpeg_generator(self):
        boundary = b"--frame"
        # Yield a frame whenever a new one arrives; send a keepalive if idle.
        while True:
            # Wait at most 1s for a new frame to avoid proxy timeouts.
            self._event.wait(timeout=1.0)
            with self._lock:
                frame_bytes = self._latest_jpeg
                self._event.clear()

            if frame_bytes is None:
                # Keep-alive empty JPEG if nothing yet
                time.sleep(0.05)
                continue

            headers = (
                boundary + b"\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(frame_bytes)).encode() + b"\r\n\r\n"
            )
            yield headers + frame_bytes + b"\r\n"

frame_hub = FrameHub()

def set_frame_from_bgr(frame_bgr):
    """Public function the capture loop can call."""
    frame_hub.set_bgr_frame(frame_bgr)
