# Sensee

Gesture-powered control for your space.

Sensee is a two-part ecosystem:

- A mobile app where you configure what each gesture should do.
- A local engine device ( Pc or Raspberry Pi) that watches your camera and executes those actions in real time.

The goal is a plug-and-play experience: power the device, open the app, map gestures to actions, and control your environment naturally.

## Demo Showcase

https://github.com/user-attachments/assets/64bbf61c-e38d-4bf4-9064-bd26c9c91c62

## The Experience

Think of Sensee like this:

1. You open the app and add a mapping.
2. You choose a target device (for example TV), a gesture (for example Open Palm), and an action (for example Volume Up).
3. The app syncs that mapping to your device.
4. The camera sees your gesture and the action runs.

You are not juggling two separate products. The app handles setup and control rules, while the engine handles real-time detection and execution.

## The Loop

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
- IR-style device actions(future implementation, not ready yet)
- PC actions

## Product Vision

The product is designed as a consumer flow:

- Plug in your Sensee device(raspberry pi or pc)
- Open the phone app
- Configure gestures in a guided UI
- Start controlling devices instantly

The long-term direction is a seamless hardware + software experience where setup feels as simple as onboarding a smart speaker.

## Setup For Non Developers

1. Install the app on your phone from the release page [app-release.apk](https://github.com/RafailAndreou/sensee/releases/tag/v0.6.9v)
2. Install the zip on your windows from the release page [sensee-windows-x64.zip](https://github.com/RafailAndreou/sensee/releases/tag/v0.6.9v)
3. Extract the zip
4. Run the executable(sensee.exe)
5. Open the settings and put your home assistant url and token(homeassistant url is localhost:8123 as the default)
   **If you don't know how to setup homeassistant check raspi/docker/dockertutorial.md or https://www.home-assistant.io/docs/**

**Important: The app and the engine must be on the same network(no need for internet access tho)**

## Technical Setup (Developer Section)

This section keeps the implementation details separate from the user experience narrative.

### Prerequisites

- Python 3.10+
- Webcam
- Flutter SDK

### Run the Engine (Python)

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

### Home Assistant Connect

Create a ha_config.json file in the server folder with the following format(check raspi/docker/dockertutorial.md for more details on how to setup your homeassistant):

```json
{
  "host": "http://localhost:8123",
  "token": "YOUR_LONG_LIVED_ACCESS_TOKEN"
}
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

# Community Testing

This section is to list the hardware people have succesfully run it on so if you run it on your raspberry pi or another sbc please share the exact hardware so I can update this section.

# Contribute

### Getting Started

1. Fork the repo and clone it locally:
   ```powershell
   git clone https://github.com/YOUR_USERNAME/sensee.git
   cd sensee
   ```
2. Follow the **Technical Setup** section above to get both the engine and app running
3. Create a branch for your changes:
   ```powershell
   git checkout -b feature/your-feature-name
   # or: fix/issue-description, docs/update-readme, etc.
   ```

### Before Submitting

Run the tests to make sure nothing is broken:

**Engine (Python):**

```powershell
cd raspi
python -m unittest discover -s tests -p "test_*.py"
```

**App (Flutter):**

```powershell
cd mobile/surface_controller
flutter analyze
flutter test
```

### Submitting a Pull Request

1. One feature or fix per PR (keep changes focused and reviewable)
2. Write a clear PR title and description explaining **what** changed and **why**
3. For larger changes, open an issue first to discuss the approach
4. Make sure your code passes all tests and lint checks

**AI-assisted contributions:** Upload `guidelines.md` to your AI assistant before generating changes.
