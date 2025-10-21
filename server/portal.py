from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import socket

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html><body style="font-family:sans-serif;text-align:center;">
    <h2>Gesture Controller Setup</h2>
    <form action="/provision" method="post">
      Wi-Fi SSID:<br><input name="ssid"><br><br>
      Password:<br><input name="password" type="password"><br><br>
      <button type="submit">Connect</button>
    </form>
    </body></html>
    """

@app.post("/provision")
def provision(ssid: str = Form(...), password: str = Form(...)):
    print(f"Received credentials: SSID={ssid}, PASSWORD={password}")
    return {"status": "ok", "msg": f"Trying to connect to {ssid}"}

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    s.close()
    return ip

if __name__ == "__main__":
    ip = get_local_ip()
    print(f"\n🌐 Connect your phone to the 'GestureController' Wi-Fi.")
    print(f"Then open: http://{ip}:8000\n")
    import uvicorn
    uvicorn.run("portal:app", host="0.0.0.0", port=8000, reload=False)
