# Sensee

Gesture-powered control for your space.

Sensee is a two-part ecosystem:

- A mobile app where you configure what each gesture should do.
- A local engine device (laptop or Raspberry Pi) that watches your camera and executes those actions in real time.

The goal is a plug-and-play experience: power the device, open the app, map gestures to actions, and control your environment naturally.

## Demo Showcase

Watch the project showcase video:

![Showcase Demo](showcase/showcase.mp4)

## The Experience

Think of Sensee like this:

1. You open the app and add a mapping.
2. You choose a target device (for example TV), a gesture (for example Open Palm), and an action (for example Volume Up).
3. The app syncs that mapping to your Sensee engine device.
4. The camera sees your gesture and the action runs.

You are not juggling two separate products. The app handles setup and control rules, while the engine handles real-time detection and execution.

## The Sensee Loop

### 1. Configure

The Flutter app (Surface Controller) is the control center for:

- Adding gesture-to-action mappings
- Editing and deleting mappings
- Syncing configurations to the engine
- Pairing with Home Assistant devices

### 2. Discover and Connect

The app finds the engine over the local network using automatic discovery (mDNS and UDP fallback), so setup feels lightweight.

### 3. Detect

The engine continuously processes camera frames and recognizes hand gestures in real time.

### 4. Execute

When a mapping is matched, Sensee routes the action to the right target:

- Smart Home / Home Assistant actions
- IR-style device actions
- PC actions

## Product Vision

Sensee is designed as a consumer flow:

- Plug in your Sensee device
- Open the phone app
- Configure gestures in a guided UI
- Start controlling devices instantly

The long-term direction is a seamless hardware + software experience where setup feels as simple as onboarding a smart speaker.

## Technical Setup (Developer Section)

This section keeps the implementation details separate from the user experience narrative.

### Prerequisites

- Python 3.10+
- Webcam
- Flutter SDK

### Run the Sensee Engine (Python)

```powershell
cd raspi
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python gesture.py
```

### Run the Surface Controller App (Flutter)

```powershell
cd mobile/surface_controller
flutter pub get
flutter run
```

### Optional: Home Assistant Container

```powershell
cd docker
docker compose up -d
```

## Repository Layout

```text
sensee/
├── mobile/surface_controller/   # Flutter configuration app
├── raspi/                       # Python engine + server
└── docker/                      # Home Assistant container setup
```

## Roadmap

- Expand plug-and-play onboarding flow
- Improve gesture robustness and personalization
- Broaden action coverage across smart and local devices
- Continue evolving IR-first and smart-home-first control paths

## Tech Stack

- Mobile App: Flutter (Dart)
- Engine & API: Python, FastAPI
- Vision: MediaPipe, OpenCV
- Smart Home Integration: Home Assistant
