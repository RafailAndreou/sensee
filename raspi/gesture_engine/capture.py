import cv2

from gesture_engine.log import get_logger

logger = get_logger(__name__)


def open_camera_capture(camera_cfg: dict) -> tuple[cv2.VideoCapture, str]:
    """Open a VideoCapture from camera config.

    Returns:
        (cap, source_label) — label is used in error messages.
    """
    use_network = camera_cfg.get("useNetwork", False)
    stream_url = camera_cfg.get("streamUrl", "").strip()
    if use_network and stream_url:
        logger.info("Opening network camera: %s", stream_url)
        return cv2.VideoCapture(stream_url), stream_url
    return cv2.VideoCapture(0), "device 0"
