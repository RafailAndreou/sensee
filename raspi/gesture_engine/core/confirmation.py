class TouchConfirmation:
    def __init__(self, confirm_frames=2):
        self.confirm_frames = max(1, int(confirm_frames))
        self._state = {}

    def is_confirmed(self, state_key, is_touching):
        state = self._state.setdefault(state_key, {"streak": 0, "active": False})
        if is_touching:
            state["streak"] += 1
            if not state["active"] and state["streak"] >= self.confirm_frames:
                state["active"] = True
                return True
        else:
            state["streak"] = 0
            state["active"] = False
        return False