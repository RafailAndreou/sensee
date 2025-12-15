class Debouncer:
    def __init__(self, interval_seconds):
        self.interval = interval_seconds
        self.last_trigger_time = 0

    def can_trigger(self):
        """Returns True if enough time has passed since the last trigger."""
        now = time.monotonic()
        if now - self.last_trigger_time > self.interval:
            self.last_trigger_time = now
            return True
        return False