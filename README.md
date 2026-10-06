# Sensee

Gesture-powered control for your space.

Sensee is a local engine that watches your camera and executes gesture-driven actions in real time. Configure mappings through a built-in web dashboard — no app install required — or use the optional mobile app.

The goal is a plug-and-play experience: power the device, open the dashboard in your browser, map gestures to actions, and control your environment naturally.

## Demo Showcase

https://github.com/user-attachments/assets/64bbf61c-e38d-4bf4-9064-bd26c9c91c62

## The Experience

Think of Sensee like this:

1. You plug in your Sensee device (PC or Raspberry Pi).
2. You open `sensee.local:8000` in your browser (or the auto-opened dashboard).
3. You add a mapping — choose a target (e.g. TV), a gesture (e.g. Open Palm), and an action (e.g. Volume Up).
4. The camera sees your gesture and the action runs.

The web dashboard handles setup and configuration, while the engine handles real-time detection and execution.

## The Loop

### 1. Configure

The web dashboard (served by the engine itself) is the control center for:

- Adding gesture-to-action mappings
- Editing and deleting mappings
- Pairing with Home Assistant devices
- Adjusting gesture and camera settings

An optional Flutter mobile app is also available for users who prefer a native experience with automatic network discovery.

### 2. Detect

The engine continuously processes camera frames and recognizes hand gestures in real time.

### 3. Execute

When a mapping is matched, Sensee routes the action to the right target:

- Smart Home / Home Assistant actions
- IR-style device actions (future implementation, not ready yet)
- PC actions

## Product Vision

The product is designed as a consumer flow:

- Plug in your Sensee device (Raspberry Pi or PC)
- Open the web dashboard or phone app
- Configure gestures in a guided UI
- Start controlling devices instantly

The long-term direction is a seamless hardware + software experience where setup feels as simple as onboarding a smart speaker.

## Setup For Non Developers

1. Download the latest Windows zip from the [Releases page](https://github.com/RafailAndreou/sensee/releases)
2. Extract the zip
3. Run the executable (`sensee.exe`)
4. The web dashboard will auto-open in your browser, or navigate to `http://sensee.local:8000`
   Enter the **pairing key** printed in the Sensee engine window. Each browser or mobile app must pair before it can view the camera or change settings. In the mobile app, tap **Pair** on the dashboard banner and enter the same key.
5. Open Settings and put your Home Assistant URL and token (Home Assistant URL is `http://localhost:8123` by default)
   **If you don't know how to setup Home Assistant check [raspi/docker/dockertutorial.md](raspi/docker/dockertutorial.md) or https://www.home-assistant.io/docs/**

### Optional: Mobile App

You can also download the latest Android APK from the [Releases page](https://github.com/RafailAndreou/sensee/releases) for a native experience with automatic device discovery. The app and the engine must be on the same network (no internet access required).

## Technical Setup (Developer Section)

This section keeps the implementation details separate from the user experience narrative.

### Prerequisites

- Python 3.10+
- Webcam
- Flutter SDK (optional, only if building the mobile app)

### Run the Engine (Python)

```powershell
cd raspi
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python gesture.py
```

Running `gesture.py` starts the FastAPI server and opens the web UI in your browser (`/web`) on the first available port from `8000-8004`.

For operation without the local camera window, set `SENSEE_PREVIEW=0` before
starting the engine. Recognition continues, and paired clients can still open
the video stream. Stream JPEGs are encoded only while a client is watching,
at a maximum of 15 frames per second, independently of recognition.

Camera changes saved through the dashboard or API reopen capture automatically.
Settings are cached in memory; restart the engine after editing JSON files
directly. Dashboard and API saves invalidate the cache automatically.

Touch confirmations use distinct, fresh recognition results. Losing tracking
resets confirmations and interrupts wake holds. Confirmed touch transitions and
device commands use bounded queues that preserve order; continuous inputs keep
the latest state. All camera commands expire 100 ms after their original
inference timestamp, including confirmed touches and commands waiting for a
device worker. Queuing never resets their age. An action overlay indicates accepted dispatch, rather than
confirmation that a physical device has responded.

Voice capture keeps about one second of pending audio. If transcription falls
behind and speech is interrupted by overflow, the engine waits for a pause
before collecting a new utterance. Disabling voice or changing its settings
cancels pending transcription output.

### Run the Surface Controller App (Flutter, Optional)

```powershell
cd mobile/surface_controller
flutter pub get
flutter run
```

### Home Assistant Connect

Create a `ha_config.json` file in the server folder with the following format (check [raspi/docker/dockertutorial.md](raspi/docker/dockertutorial.md) for more details on how to setup your Home Assistant):

```json
{
  "url": "http://localhost:8123",
  "token": "YOUR_LONG_LIVED_ACCESS_TOKEN"
}
```

The engine adds `http://` when the scheme is omitted. Leaving the token field blank in the dashboard or app preserves the saved token.

The pairing key is stored in `raspi/server/access_config.json` during development, or beside the Windows executable. To revoke all paired clients, stop Sensee, delete both `access_config.json` and its `.bak` file, and restart; enter the new key on each client. Keep these files private. Authentication protects access, but plain HTTP does not encrypt traffic; use Sensee on your trusted local network or put it behind HTTPS.

Settings are written atomically and the previous valid save is kept in a `.bak` file. The engine falls back to that backup if the main JSON file is damaged. `SENSEE_DATA_DIR` can override the settings directory.

### Optional: Home Assistant Container

```powershell
cd docker
docker compose up -d
```

## Repository Layout

```text
sensee/
├── mobile/surface_controller/   # Flutter configuration app (optional)
├── raspi/                       # Python engine + server + web dashboard
└── docker/                      # Home Assistant container setup
```

## Roadmap

- Expand plug-and-play onboarding flow
- Improve gesture robustness and personalization
- Broaden action coverage across smart and local devices
- Continue evolving IR-first and smart-home-first control paths

## Tech Stack

- Web Dashboard: Vanilla JS, CSS, HTML
- Mobile App (optional): Flutter (Dart)
- Engine & API: Python, FastAPI
- Vision: MediaPipe, OpenCV
- Smart Home Integration: Home Assistant

# Community Testing

This section is to list the hardware people have successfully run it on. If you run it on your Raspberry Pi or another SBC, please share the exact hardware so I can update this section.

# Contribute

### Getting Started

1. Fork the repo and clone it locally:
   ```powershell
   git clone https://github.com/YOUR_USERNAME/sensee.git
   cd sensee
   ```
2. Follow the **Technical Setup** section above to get the engine running
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
pip install -r requirements-test.txt
python -m unittest discover -s tests -p "test_*.py"
```

**App (Flutter, optional):**

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
