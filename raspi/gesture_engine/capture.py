"""A dedicated camera owner with one replaceable latest frame."""
import threading
import time
from urllib.parse import urlsplit
import cv2
from gesture_engine import control
from gesture_engine.log import get_logger
from server import file

logger = get_logger(__name__)


def safe_camera_label(url):
    try:
        parsed = urlsplit(url)
        return f'{parsed.scheme}://{parsed.hostname or "camera"}/[redacted]'
    except ValueError:
        return '[network camera]'


def open_camera_capture(camera_cfg):
    url = str(camera_cfg.get('streamUrl', '')).strip()
    network = camera_cfg.get('useNetwork', False) and url
    label = safe_camera_label(url) if network else 'device 0'
    logger.info('Opening camera: %s', label)
    if network:
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG, [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000,
                                                   cv2.CAP_PROP_READ_TIMEOUT_MSEC, 1000])
    else:
        cap = cv2.VideoCapture(0)
    settings = file.load_engine_settings()
    for key, prop in [('captureWidth', cv2.CAP_PROP_FRAME_WIDTH),
                      ('captureHeight', cv2.CAP_PROP_FRAME_HEIGHT), ('captureFps', cv2.CAP_PROP_FPS)]:
        cap.set(prop, settings[key])
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap, label


class CaptureWorker:
    def __init__(self, stop_event, opener=open_camera_capture):
        self.stop_event = stop_event
        self.opener = opener
        self.condition = threading.Condition()
        self.latest = None
        self.thread = threading.Thread(target=self._run, name='CameraCapture', daemon=True)

    def start(self):
        self.thread.start()
        return self

    def publish(self, frame, timestamp_ms, epoch):
        with self.condition:
            self.latest = (frame, timestamp_ms, epoch)
            self.condition.notify_all()

    def take(self, max_age_ms=100):
        with self.condition:
            self.condition.wait_for(lambda: self.latest is not None or self.stop_event.is_set(), timeout=0.1)
            item, self.latest = self.latest, None
        if item and (time.monotonic_ns() // 1_000_000 - item[1] > max_age_ms or item[2] != control.epoch):
            control.record('rejected', reason='stale_capture')
            return None
        return item

    def _run(self):
        cap = None
        revision = None
        last_published = float("-inf")
        try:
            while not self.stop_event.is_set():
                current = (file.settings_revision(file.CAMERA_SETTINGS_PATH),
                           file.settings_revision(file.ENGINE_SETTINGS_PATH))
                if cap is None or current != revision:
                    if cap is not None:
                        cap.release()
                    revision = current
                    last_published = float("-inf")
                    settings = file.load_engine_settings()
                    try:
                        cap, _ = self.opener(file.load_camera_settings())
                    except (cv2.error, OSError) as error:
                        # Native errors may embed the original URL; never log their text.
                        logger.warning('Camera open failed (%s); retrying.', type(error).__name__)
                        cap = None
                        control.invalidate('camera_disconnect')
                        control.metric(cameraConnected=False)
                        self.stop_event.wait(0.5)
                        continue
                epoch = control.epoch
                started = time.monotonic()
                try:
                    ok, frame = cap.read() if cap.isOpened() else (False, None)
                except (cv2.error, OSError):
                    ok, frame = False, None
                if not ok:
                    control.invalidate('camera_disconnect')
                    with self.condition:
                        self.latest = None
                    cap.release()
                    cap = None
                    control.metric(cameraConnected=False)
                    self.stop_event.wait(0.5)
                    continue
                timestamp = int(started * 1000)
                # Always drain the device/decoder. Sleeping here accumulates buffered
                # RTSP frames when the source ignores a requested lower capture FPS.
                if started - last_published >= 1 / settings['captureFps']:
                    last_published = started
                    control.metric(cameraConnected=True, captureLatencyMs=round((time.monotonic()-started)*1000, 2),
                                   actualCaptureWidth=frame.shape[1], actualCaptureHeight=frame.shape[0])
                    self.publish(frame, timestamp, epoch)
        finally:
            if cap is not None:
                cap.release()
            control.invalidate('camera_stopped')

    def close(self):
        self.stop_event.set()
        with self.condition:
            self.condition.notify_all()
        self.thread.join(timeout=3)
