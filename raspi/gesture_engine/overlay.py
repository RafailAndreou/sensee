import cv2

OVERLAY_DURATION_SECONDS = 1.5


def draw_action_overlay(frame, label: str) -> None:
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, h - 50), (w, h), (20, 20, 20), -1)
    cv2.putText(
        frame, label, (12, h - 16),
        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 230, 110), 2, cv2.LINE_AA,
    )
