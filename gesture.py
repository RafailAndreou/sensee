
import cv2
import mediapipe as mp
import pyautogui
import server
import threading
import time
from server import main

ip = main.get_local_ip()
print(f"\n🌐 Access the configuration portal at: http://{ip}:8000\n")
uvicorn_process = threading.Thread(target=lambda: main.uvicorn.run("server.main:app", host="0.0.0.0", port=8000))
uvicorn_process.start()

screen_w, screen_h = pyautogui.size()
mouse_x, mouse_y = pyautogui.position()

print(screen_h, screen_w)

MIRROR_PREVIEW = True

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

def position_check():
    pass

def touching(finger1, finger2):
    threshold = 0.05  # Define a threshold for "touching"
    if finger1 and finger2:
        dist = ((finger1.x - finger2.x) ** 2 + (finger1.y - finger2.y) ** 2) ** 0.5
        return dist < threshold  # Adjust threshold as needed
    return False



def translate_coords(x, y):
    new_x = screen_w - round(x * screen_w)
    new_y = round(y * screen_h)
    return new_x, new_y


with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.3
) as hands:

    while cap.isOpened():
        ret, frame = cap.read()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        if not ret:
            continue

        if cv2.waitKey(1) & 0xFF == ord('q') or cv2.waitKey(1) & 0xFF == ord('Q'):
            break
        try: 
            index_x,index_y = results.multi_hand_landmarks[0].landmark[8].x,results.multi_hand_landmarks[0].landmark[8].y
            mouse_x, mouse_y = translate_coords(index_x, index_y)
            pyautogui.moveTo(mouse_x, mouse_y,_pause=False)
        except:
            pass
        try:
            thumb = results.multi_hand_landmarks[0].landmark[4]
            middle = results.multi_hand_landmarks[0].landmark[12]
            if touching(thumb, middle):
                send_thread = threading.Thread(target=server.send_msg, args=("up",))
                send_thread.start()
                time.sleep(0.2)  # debounce delay
                
        except:
            pass
        
        try:
            thumb = results.multi_hand_landmarks[0].landmark[4]
            index = results.multi_hand_landmarks[0].landmark[8]
            if touching(thumb, index):
                send_thread = threading.Thread(target=server.send_msg, args=("down",))
                send_thread.start()
                time.sleep(0.2)  # debounce delay
                
        except:
            pass
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )
        if MIRROR_PREVIEW:
            frame = cv2.flip(frame, 1)
        cv2.imshow('MediaPipe Hands', frame)
         
cap.release()
cv2.destroyAllWindows()
