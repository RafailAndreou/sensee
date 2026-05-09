from collections import defaultdict

from gesture_engine.log import get_logger
from server.timing import Debouncer

logger = get_logger(__name__)

_event_debouncers = defaultdict(lambda: Debouncer(0.18))


def send_msg(event: str):
    """Called by gesture loop; this can later route to IR/BLE/etc."""
    if not _event_debouncers[event].can_trigger():
        return
    logger.info("gesture: %s", event)