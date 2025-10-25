Perfect — here’s a version of the `README.md` focused **only on your current setup** (the **laptop FastAPI server + Flutter mobile app** version), leaving out Raspberry Pi and hardware plans for now.

---

# Sensee

**Invisible Smart Gesture Controller — Laptop Prototype**

---

## 🧠 Overview

**Sensee** is a gesture-based control system that lets you interact with devices using **hand gestures in mid-air**, with **no screen, no voice, and no touch**.

The current version runs entirely on a **laptop** and connects to a **Flutter mobile app** over HTTP. It detects gestures in real time using your webcam and displays live camera feed + configuration options on the app.

---

## ⚙️ Architecture

### 🖥️ **Laptop (Server)**

- Runs **FastAPI** backend
- Uses **OpenCV + MediaPipe** for real-time gesture detection
- Streams live video frames via **MJPEG** endpoint
- Provides configuration endpoints for the Flutter app
- Runs in a separate **thread** to avoid blocking the main gesture loop

### 📱 **Mobile App (Client)**

- Built with **Flutter**
- Connects to the FastAPI server using **HTTP requests**
- Fetches live camera feed from MJPEG stream (`/video`)
- Sends gesture configuration data via `POST` requests
- Displays intuitive UI for:

  - Selecting brand/device
  - Mapping gestures to actions
  - Choosing feedback type (sound/haptic)

---

## 🧩 Current Features

### ✅ **Implemented**

- **Gesture Recognition (Python + MediaPipe)**

  - Gestures available:

  - Thumb + Index touching
  - Thumb + Middle finger touching
  - Moving hand to the right
  - Moving hand to the left
  - Closing Fist
  - Opening Open Palm

  - Detection is consistent and stable at ~30+ FPS depending on hardware

- **FastAPI Server**

  - `/video` → MJPEG live stream endpoint
  - `/configuration` → Receives JSON configs from the app
  - Handles concurrent frame updates safely via threaded `FrameHub` class

- **Flutter App**

  - Live camera view via MJPEG
  - Configuration UI for mapping gestures
  - Sends configuration data to the backend via POST requests

---

## 🧱 Project Structure

```
sensee/
├── gesture.py          # Handles camera input + MediaPipe gesture detection
├── server/
│   ├── main.py         # FastAPI app with MJPEG + config endpoints
│   └── __init__.py
└── flutter_app/        # Flutter client (mobile configuration interface)
```

---

## 📡 Communication Flow

```
        +------------------+
        |   Flutter App    |
        |------------------|
        |  Live camera UI  |
        |  Gesture mapping |
        +---------+--------+
                  |
          HTTP (GET/POST)
                  |
        +---------v--------+
        |    FastAPI App   |
        |------------------|
        |  /video (MJPEG)  |
        |  /configuration  |
        +---------+--------+
                  |
             Camera + MediaPipe
```

---

## 🧰 Tech Stack

| Layer     | Framework / Library | Purpose                                      |
| --------- | ------------------- | -------------------------------------------- |
| Backend   | Python + FastAPI    | Server, endpoints, MJPEG stream              |
| Vision    | OpenCV + MediaPipe  | Hand tracking & gesture detection            |
| Frontend  | Flutter (Dart)      | Mobile UI, configuration portal              |
| Threading | Python `threading`  | Runs FastAPI + gesture detection in parallel |

---

## 🚀 How It Works

1. **Start the server**

   ```bash
   python gesture.py
   ```

   - This automatically launches the FastAPI app on your local IP (e.g., `http://192.168.1.x:8000`).
   - The terminal prints the access URL for your phone.

2. **Open the Flutter app**

   - Enter the same local IP in the app’s settings.
   - View the live camera stream.
   - Configure gestures → actions (e.g., “Thumb + Index → Volume Up”).

3. **Perform the gesture**

   - Sensee detects it using your laptop camera.
   - Prints or logs the detected gesture (actions are stubbed for now).

---

## 🧠 Example Configuration (POST JSON)

```json
{
  "brand": "Samsung",
  "action": "VolumeUp",
  "gesture": "ThumbIndex",
  "sound": "click.wav",
  "hand": "Right"
}
```

---

## 🧭 Philosophy

> “Invisible control for visible comfort.”

Sensee aims to make interaction **natural and quiet**, replacing voice assistants or screens with intuitive motion — combining **AI hand tracking**, **local computation**, and **minimalist design**.

---

## 📈 Next Steps

- Add debounce and per-action gesture handling
- Extend gesture library (more hand combinations)
- Integrate IR or Bluetooth action layer later
- Add persistent settings storage (JSON or SQLite)
- Improve latency and FPS stability
