import threading


def _check_hand_movement(wrist_queue, send_msg, movement_threshold=0.02):
    prev_pos = None
    while True:
        try:
            wrist = wrist_queue.get()
            
            if wrist is None:  # Sentinel value to gracefully exit the thread
                break

            current_pos = (wrist.x, wrist.y)

            if prev_pos is not None:
                # Positive x-delta means the wrist moved right in normalised coordinates.
                # Because the camera feed is mirrored for preview, this corresponds to
                # the user's hand moving to their left, so the event is labelled accordingly.
                if current_pos[0] - prev_pos[0] > movement_threshold:
                    send_msg("Hand moved left")
                elif current_pos[0] - prev_pos[0] < -movement_threshold:
                    send_msg("Hand moved right")

            prev_pos = current_pos
        except Exception as e:
            print(f"Error in hand movement monitor: {e}")


def start_hand_movement_monitor(wrist_queue, send_msg, movement_threshold=0.02):
    thread = threading.Thread(
        target=_check_hand_movement,
        args=(wrist_queue, send_msg, movement_threshold),
        daemon=True,
    )
    thread.start()
    return thread