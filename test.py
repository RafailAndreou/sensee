import cv2
import mediapipe as mp

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

with mp_hands.Hands(
    static_image_mode=False,      # Live video
    max_num_hands=2,              # You only need 1 hand for tapping
    min_detection_confidence=0.6,
    min_tracking_confidence=0.3) as hands:

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert BGR (OpenCV default) to RGB (MediaPipe expects this)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame
        results = hands.process(rgb)

        # Draw hand landmarks if detected
        if results.multi_hand_landmarks: # multi_hand_landmarks is a list of detected hands (each with 21 landmarks).
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS)

                # Example: get index fingertip coordinates (landmark 8)
                h, w, c = frame.shape
                x = int(hand_landmarks.landmark[8].x * w)
                y = int(hand_landmarks.landmark[8].y * h)
                z = hand_landmarks.landmark[8].z
                text = f"Z: {z:.2f}"
                cv2.putText(frame, text, (100,100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)
                # z is relative depth

                cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)
                cv2.putText(frame, "Index fingertip", (x+10, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
                
                x2 = int(hand_landmarks.landmark[4].x * w)
                y2 = int(hand_landmarks.landmark[4].y * h)
                if (abs(x - x2) < 20 and abs(y - y2) < 20):
                    cv2.putText(frame, "TAP!", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)
                   #draw when tapped is pressed
                    cv2.circle(frame, (x2, y2), 10, (0, 0, 255), -1) 

        cv2.imshow("MediaPipe Hands", frame)
        if cv2.waitKey(1) & 0xFF == ord('q') or cv2.waitKey(1) & 0xFF == ord('Q'):
            break

cap.release()
cv2.destroyAllWindows()

