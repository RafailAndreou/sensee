import webbrowser
import pyautogui


def open_url(url):
    webbrowser.open(url)
    
def close_app():
    print("Closing application...")
    exit()
    
def window_right():
    pyautogui.hotkey('win', 'right')
    
def window_left():
    pyautogui.hotkey('win', 'left')

if __name__ == "__main__":
    open_url("https://music.youtube.com/")
    close_app()
    
