from collections import defaultdict

from server.timing import Debouncer


_event_debouncers = defaultdict(lambda: Debouncer(0.18))


def send_msg(event: str):
    """Called by gesture loop; this can later route to IR/BLE/etc."""
    if not _event_debouncers[event].can_trigger():
        return
    print(f"[gesture] {event}")