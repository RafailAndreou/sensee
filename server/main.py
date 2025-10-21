from fastapi import FastAPI
from pydantic import BaseModel
import socket
import uvicorn

app = FastAPI()

# ----------- MODEL -----------

class Configuration(BaseModel):
    brand: str
    action: str
    gesture: str
    sound: str
    hand: str

# ----------- GLOBAL CONFIG STORAGE -----------
current_config = {}

# ----------- ROUTES -----------

@app.get("/")
def root():
    return {"message": "Hello, World!"}

@app.post("/configuration")
def configure(settings: Configuration):
    global current_config
    current_config = settings.dict()
    print("\n✅ Received configuration:")
    for key, value in current_config.items():
        print(f"  {key}: {value}")

    # Example: you can use these values anywhere in your code
    # e.g. if current_config["gesture"] == "Thumb_Up": send_ir_signal()
    
    return {"status": "configured", "received": current_config}

@app.get("/configuration")
def get_configuration():
    return {"message": "Please use POST method to configure settings"}

@app.get("/current")
def get_current_config():
    return current_config


# ----------- HELPER FUNCTION -----------

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    s.close()
    return ip


# ----------- MAIN ENTRY POINT -----------

if __name__ == "__main__":
    ip = get_local_ip()
    print(f"\n🌐 Server running at http://{ip}:8000\n")
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000)
