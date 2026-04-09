# Sensee

Invisible Smart Gesture Controller - laptop prototype.

Sensee detects hand gestures using your camera (MediaPipe + OpenCV), streams video through FastAPI, and lets the Flutter mobile app configure gesture-to-action mappings.

## Overview

- Backend exposes:
  - `/video` MJPEG stream
  - `/configuration` API for gesture mappings
- Mobile app (`mobile/surface_controller`) connects to the backend over local network HTTP.

## Prerequisites

- Python 3.10+
- Webcam
- Flutter SDK (for mobile app)

## Installation (Backend)

1. Go to backend directory:

```bash
cd raspi
```

2. Create and activate virtual environment.

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Quickstart

1. Start backend:

```powershell
cd raspi
python gesture.py
```

2. Backend prints local URL (for example `http://192.168.1.42:8000`).

3. Open Flutter app in `mobile/surface_controller` and connect to same IP.

## Mobile App

```powershell
cd mobile\surface_controller
flutter clean
flutter pub get
flutter run
```

Release APK (optional):

```powershell
flutter build apk --release
```

## Architecture

### Backend (`raspi`)

- FastAPI endpoints
- OpenCV + MediaPipe gesture detection
- MJPEG frame streaming

### Mobile (`mobile/surface_controller`)

- Flutter UI for live feed + gesture configuration

## Project Structure

```text
sensee/
├── raspi/                      # Python backend + gesture runtime
│   ├── gesture.py
│   ├── gesture_engine/
│   └── server/
├── mobile/
│   └── surface_controller/     # Flutter app
├── FUTURE.md
└── MODULARIZATION_PLAN.md
```

## Tech Stack

- Backend: Python, FastAPI
- Vision: OpenCV, MediaPipe
- Mobile: Flutter (Dart)

## Example Configuration Payload

```json
{
  "brand": "Samsung",
  "action": "VolumeUp",
  "gesture": "ThumbIndex",
  "sound": "click.wav",
  "hand": "Right"
}
```

## Next Steps

- Expand gesture set and reliability
- Improve persistence model beyond JSON when needed
- Continue modularization (tracked in `FUTURE.md`)
