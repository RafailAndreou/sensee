# Sensee

Invisible Smart Gesture Controller — Laptop prototype

A minimal, local-first system that detects hand gestures using your laptop camera and exposes a small HTTP API to a Flutter mobile app which serves as the configuration UI.

## Table of contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Architecture](#architecture)
- [Features](#features)
- [Project structure](#project-structure)
- [Communication flow](#communication-flow)
- [Tech stack](#tech-stack)
- [Example configuration](#example-configuration)
- [Next steps](#next-steps)

## Overview

Sensee detects simple hand gestures (using MediaPipe + OpenCV) on a laptop and exposes:

- an MJPEG `/video` endpoint for a live camera feed
- configuration endpoints to accept gesture → action mappings from a Flutter app

The current repository focuses on the laptop/server prototype and the Flutter mobile UI.

## Prerequisites

- Python 3.10 or higher
- A webcam (for gesture detection)

## Installation

### Linux / Raspberry Pi

1. Navigate to the server directory:

   ```bash
   cd raspi
   ```

2. Create a virtual environment:

   ```bash
   python3 -m venv venv
   ```

3. Activate the environment:

   ```bash
   source venv/bin/activate
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Quickstart

1. Run the gesture server (from the `raspi/` or server folder):

   ```powershell
   python gesture.py
   ```

   The server will print the local URL (e.g. `http://192.168.1.42:8000`).

2. Open the Flutter app (`mobile/surface_controller`) on your phone/emulator and point it to the same IP.

3. Build an APK (optional — for distribution):

   ```powershell
   cd mobile\surface_controller
   flutter clean
   flutter pub get
   flutter build apk --release
   ```

   Output APK:

   `mobile/surface_controller/build/app/outputs/flutter-apk/app-release.apk`

   Notes:

   - Use `--split-per-abi` for smaller per-ABI APKs.
   - For Play Store, prefer `flutter build appbundle --release` and configure a proper signing keystore.

## Architecture

### Laptop (server)

- FastAPI backend
- OpenCV + MediaPipe for hand detection
- MJPEG endpoint for live frames

### Mobile (client)

- Flutter app that reads the MJPEG stream and posts configuration JSON to the server

## Features

- Gesture recognition (basic gestures implemented)
- MJPEG live stream (`/video`)
- Configuration endpoints for mapping gestures to actions

## Project structure

```
sensee/
├── raspi/                      # Python server + gesture detection
│   ├── gesture.py
│   └── server/                  # FastAPI app and helpers
└── mobile/                      # Flutter mobile configuration UI
    └── surface_controller/      # Flutter project
```

## Communication flow

```
Flutter App <---- HTTP (GET/POST) ----> FastAPI Server
       |                                     |
       |-- GET /video (MJPEG stream)         |-- Camera + MediaPipe + OpenCV
       |-- POST /configuration               |
```

## Tech stack

- Backend: Python + FastAPI
- Vision: OpenCV + MediaPipe
- Client: Flutter (Dart)

## Example configuration (POST JSON)

```json
{
  "brand": "Samsung",
  "action": "VolumeUp",
  "gesture": "ThumbIndex",
  "sound": "click.wav",
  "hand": "Right"
}
```

## Next steps

- Improve gesture set and add debounce
- Persist settings (JSON/SQLite)
- Integrate action layer (IR/Bluetooth)
- Configure release signing for Play Store

---

If you'd like, I can also:

- add a short developer-facing `mobile/README.md` with exact commands to build and attach the APK to a GitHub release
- configure Android release signing (generate keystore + Gradle config)
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
├── raspi/
│   ├── server         # FastAPI app with MJPEG + config endpoints
│   └── gesture.py
└── mobile/      # Flutter client (mobile configuration interface)



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
   python gesture
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

# Installation

## Run from clone(windows)

1. Clone the repo:

```
git clone https://github.com/your/repo.git
cd repo
```

2. Create & activate a virtual environment:

```
python -m venv venv
# PowerShell
.\venv\Scripts\Activate.ps1
# cmd.exe
venv\Scripts\activate
```

3. Install dependencies and run:

```
python -m pip install -r requirements.txt
python raspi\gesture.py
```

4. Change ip address

Manually change the ip address to the ones that's printed when you run the gesture.py from:

- mobile\surface_controller\android\app\src\main\res\xml\network_security_config.xml
- camera.dart
- server.dart

and then run
flutter clean
flutter pub get
flutter run
