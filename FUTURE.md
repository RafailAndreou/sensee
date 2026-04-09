# Sensee

**Invisible Smart Gesture Controller**

---

## 🧠 Overview

**Sensee** is a compact, screenless smart-home controller that recognizes **mid-air hand gestures** using a built-in camera or depth sensor. Instead of voice commands or touchscreens, Sensee enables **silent, touchless control** of home devices through intuitive gestures — ideal for privacy-conscious users, accessibility applications, and minimalists seeking seamless interaction.

---

## ✋ Core Concept

- **No screen. No projection. No voice.**
- Detects hand gestures (e.g., thumb-index pinch, palm stop, swipe).
- Maps each gesture to a **custom action**, such as:
  - Turning lights or AC on/off
  - Adjusting volume
  - Controlling music or TV

- Provides **haptic or audio feedback** to confirm recognition.
- Uses **MediaPipe** for hand-tracking and gesture detection.

---

## ⚙️ System Architecture

### 1. **Main Controller (SBC)**

- Runs **Linux (e.g., Rock Pi 4 / Libre Le Potato)**
- Executes gesture recognition using **MediaPipe + OpenCV + FastAPI**
- Streams live camera feed via **MJPEG** to the mobile app
- Hosts configuration portal (`FastAPI` server)

### 2. **Wireless Bridge (ESP32 Module)**

- Handles **IR signal transmission** and **Bluetooth actions**
- Communicates with the SBC over Wi-Fi or serial (USB)
- Sends IR codes (e.g., via `IRremoteESP8266` or custom protocol)

### 3. **Mobile Companion App (Flutter)**

- Connects to the SBC using HTTP (`GET`/`POST` requests)
- Displays live camera feed for gesture visualization
- Lets users **configure gesture-to-action mappings**
- Stores and sends configuration data to the SBC

---

## 🪛 Hardware Components (Prototype BOM)

| Component                     | Description                        | Approx. Cost (€) |
| ----------------------------- | ---------------------------------- | ---------------- |
| Rock Pi 4 B / Libre Le Potato | Main SBC (runs Python + MediaPipe) | 65               |
| Micro SD (16–32 GB)           | OS + software environment          | 6                |
| Power Supply (5 V 3 A)        | Official or USB-C                  | 8                |
| USB Camera (720p–1080p)       | Gesture input                      | 15–20            |
| ESP32 DevKit                  | Handles IR + buzzer                | 5–7              |
| IR LED (940 nm)               | Emits IR signals                   | 1                |
| Transistor + Resistors        | Drives LED safely                  | 1                |
| Piezo Buzzer (optional)       | Audio feedback                     | 1                |
| **Estimated Total:**          |                                    | **~100 €**       |

---

## 🧩 Software Stack

| Layer               | Technology                | Purpose                               |
| ------------------- | ------------------------- | ------------------------------------- |
| **Frontend (App)**  | Flutter                   | Configuration UI & live view          |
| **Backend (SBC)**   | Python + FastAPI          | MJPEG streaming & gesture recognition |
| **ML Framework**    | MediaPipe                 | Real-time hand tracking               |
| **Signal Layer**    | ESP32 (C++ / MicroPython) | IR or Bluetooth command transmission  |
| **Feedback System** | Buzzer / haptic driver    | Gesture confirmation                  |

---

## 🚀 Features (Current Status)

✅ **Implemented**

- Two accurate gestures (thumb–index, thumb–middle)
- Real-time MJPEG streaming server (FastAPI)
- Configuration endpoint (Flutter ↔ FastAPI)
- Stable gesture recognition at ~10 FPS

🧩 **In Progress / Planned**

- IR action execution via ESP32
- Gesture debounce logic (per-action fine-tuning)
- Additional gestures & improved detection stability
- Integration of haptic/audio feedback
- Cross-device SDK or closed API layer

💡 **Suggestions**

- **Important:** Reduce dashboard card flicker when adding/deleting configurations (currently visible after sync refresh). Updates should feel smooth with no visible jump/blink.
- Add a configuration revision system (`version` or `updated_at`) so clients can detect and apply only new changes.
- Add a live sync channel (WebSocket or Server-Sent Events) so all connected phones receive immediate dashboard updates.
- Add conflict handling for concurrent edits with strict last-write-wins (no warning and no lock).
- Add a backup/restore export for all configurations (JSON profile import/export) to simplify migration between devices.
- Add offline-first sync queue on mobile: store edits while offline and auto-push when the server reconnects.
- Add full state pull on app start so each phone loads the latest server dashboard cards before local cache updates.
- Add per-edit metadata (`device_id`, `updated_at`) to improve debugging and sync traceability across multiple phones.
- Add a lightweight diagnostics page showing active server URL, last successful sync time, and pending unsynced changes.

---

## 🎯 Target Users

- **Smart-home enthusiasts** seeking silent and natural control
- **Privacy-conscious users** avoiding microphones and cameras left active
- **Accessibility users** who prefer gesture input over touch or voice
- **Minimalists** desiring screenless interaction

---

## 💡 Future Vision

- Optional **tap/surface-zone mode** for mixed interaction
- Expand gesture library (custom training support)
- Launch on **Kickstarter** after final prototype validation
- Offer **closed-source SDK** for third-party integration
- Potential role as a **smart camera module** with secure local AI processing

---

## 📷 Prototype Example

- Runs locally on laptop SBC simulation (Python + FastAPI)
- Displays hand tracking using MediaPipe
- Streams camera feed to Flutter via MJPEG endpoint
- Receives gesture configuration from the mobile app

---

## 🧭 Philosophy

> “Invisible control for visible comfort.”
> Sensee merges **gesture AI**, **local privacy**, and **tactile minimalism** — creating a new way to interact with technology without screens or noise.

---

## Engineering Issues Backlog

This chapter tracks remaining architecture and organization work after the latest refactor pass.

### Completed In This Pass

- Removed duplicated FastAPI startup/port-retry logic by introducing shared startup logic in `raspi/server/startup.py` and using it from:
  - `raspi/server/main.py`
  - `raspi/gesture_engine/server_runner.py`
- Removed dead/unused `raspi/sensee_api.py`.
- Removed legacy `raspi/utils.py` after migrating debouncing to server-owned modules.
- Decoupled gesture runtime from `server.main` by introducing dedicated imports in `raspi/gesture.py`:
  - `server.events.send_msg`
  - `server.streamer.set_frame_from_bgr`
  - `server.discovery.get_local_ip`
- Added explicit config cache APIs in `raspi/server/file.py`:
  - `set_loaded_config(...)`
  - `reload_config_cache()`
- Split Home Assistant responsibilities (first phase):
  - `raspi/server/ha_services.py` for action/domain mapping
  - `raspi/server/ha_pairing.py` for pairing flow requests
  - kept `raspi/server/homeassistant.py` as orchestrator entrypoint
- Added dedicated Home Assistant HTTP client module:
  - `raspi/server/ha_client.py` for session and timeout policy
  - wired into `raspi/server/homeassistant.py`
- Tightened config store internals in `raspi/server/file.py`:
  - internal cache renamed to `_loaded_config`
  - added `get_loaded_config()` read API
  - kept `set_loaded_config(...)` and `reload_config_cache()`
- Split camera-related gesture utilities into focused modules while preserving compatibility imports:
  - `raspi/gesture_engine/core/confirmation.py`
  - `raspi/gesture_engine/core/movement.py`
  - `raspi/gesture_engine/geometry.py`
  - `raspi/gesture_engine/camera.py` now acts as a compatibility facade
- Improved server package boundary metadata in `raspi/server/__init__.py`.

### Remaining High Priority

1. Finish Home Assistant split by isolating config/cache ownership.

- `raspi/server/homeassistant.py` still owns HA config cache and entity cache state.
- Target next modules:
  - `raspi/server/ha_config.py` (load/cache/refresh of url+token)
  - optional `raspi/server/ha_entities_cache.py` (entity cache policy)

2. Complete config store encapsulation.

- `raspi/server/file.py` now has explicit cache APIs and private internals, but still uses module-global mutable state.
- Target: class-like store API (or module facade object) with controlled reads/writes and no module-level globals.

3. Introduce one clear composition root (`app.py` or equivalent).

- Startup responsibilities still span multiple files.
- Target: one launcher that wires gesture loop + API and keeps modules import-safe.

### Remaining Medium Priority

1. Further split `raspi/gesture_engine/camera.py` into smaller focused modules.

- Suggested boundaries:
  - touch confirmation logic
  - geometry/utilities
  - hand movement monitor
- Done in current refactor pass; keep facade for backward compatibility.

2. Move or retire legacy `raspi/utils.py`.

- Done: `raspi/utils.py` removed.

3. Move Home Assistant config/cache ownership into a dedicated module.

- Keep `homeassistant.py` as thin orchestration with explicit dependencies.

4. Improve package exports and module docs.

- `raspi/server/__init__.py` can expose stable public imports and remove outdated wording.

### Remaining Low Priority

1. README cleanup and deduplication.

- `README.md` contains repeated/generated draft sections and should be consolidated.

2. Workspace hygiene for artifact-like directories.

- Clarify status of `mobile/raspi/` (artifact workspace vs active source) and document or remove accordingly.

### Suggested Next Refactor Order

1. Final config store encapsulation (replace module-global state in `server/file.py`).
2. Single startup/composition module.
3. Docs and workspace hygiene.
4. Home Assistant config/cache extraction (`ha_config.py` + optional entity cache module) when testing is available.
