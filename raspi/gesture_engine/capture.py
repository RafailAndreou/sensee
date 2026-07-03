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

    camera_index = int(camera_cfg.get("cameraIndex", 0))
    cap = cv2.VideoCapture(camera_index)

    width = int(camera_cfg.get("width", 0))
    height = int(camera_cfg.get("height", 0))
    fps = int(camera_cfg.get("fps", 0))
    if width > 0:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if height > 0:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    if fps > 0:
        cap.set(cv2.CAP_PROP_FPS, fps)

    logger.info(
        "Opening camera device %s (%sx%s @ %sfps)",
        camera_index,
        width or "default",
        height or "default",
        fps or "default",
    )
    return cap, f"device {camera_index}"
