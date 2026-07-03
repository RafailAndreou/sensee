# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

Sensee is a gesture-powered smart home controller. A Python engine on a Raspberry Pi (or Windows) runs MediaPipe gesture recognition and executes Home Assistant / IR / PC actions. A Flutter mobile app configures gesture-to-action mappings and pairs with the engine over the local network.

---

## Commands

### Python Engine (`raspi/`)

```powershell
cd raspi
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

python gesture.py                          # Run the engine
python -m unittest discover -s tests -p "test_*.py"  # Run all tests
python build_exe.py                        # Build Windows EXE via PyInstaller
```

### Flutter App (`mobile/surface_controller/`)

```powershell
cd mobile/surface_controller
flutter pub get
flutter run
flutter analyze   # Lint
flutter test      # Tests
```

### Home Assistant (Docker)

```powershell
cd docker
docker compose up -d   # Start HA on port 8123
```

---

## Architecture

### Three-Layer System

```
[Flutter App] ←→ (mDNS/UDP discovery + HTTP) ←→ [FastAPI Server] ←→ [Gesture Engine]
                                                        ↕
                                               [Home Assistant REST API]
```

**Mobile App** (`mobile/surface_controller/lib/`): Configuration UI. Discovers the engine via mDNS (`multicast_dns`) with UDP broadcast fallback. Syncs gesture mappings via `POST /configuration`. Screens live in `screens/`; network logic in `server/` (discovery, config, HA client).

**FastAPI Server** (`raspi/server/`): REST control plane + MJPEG video stream. Key routes: `POST /configuration` (save & reload gesture config), `GET /ping`, `GET /video`. Config is persisted to `configure.json` and read by the gesture engine at startup and on reload. HA credentials come from `ha_config.json` (not committed).

**Gesture Engine** (`raspi/gesture_engine/`): Real-time pipeline driven by three independent worker threads in `core/workers.py`:
- `process_gestures_loop` — wakes on `threading.Event`, pops from `deque(maxlen=1)`, matches gesture against config, routes to action.
- `process_action_queue_loop` — serializes Home Assistant calls; uses `Queue(maxsize=1)` with `put_nowait` + `queue.Full` to drop stale actions.
- `process_volume_loop` — dedicated high-frequency volume thread with its own queue and time-based debounce.

### Data Flow

1. **Config sync:** App → `POST /configuration` → `configure.json` → loaded into `GestureRuntime`
2. **Frame capture:** OpenCV → MediaPipe async callback → `GestureApp.gesture_callback()` → `deque(maxlen=1)` gesture buffer
3. **Gesture matching:** `gesture_event.set()` wakes worker → `matching.py` (`lru_cache` on normalization) → cooldown check → `take_action()`
4. **Action dispatch:** HA → `action_queue`; volume → `volume_queue`; PC → direct `pyautogui`/`webbrowser`
5. **Feedback:** Action label written to frame overlay → streamed via `/video` MJPEG endpoint

### Key Files

| File | Role |
|---|---|
| `raspi/gesture.py` | Entry point; owns camera loop and MediaPipe setup |
| `raspi/gesture_engine/runtime.py` | `GestureRuntime`: shared queues, cooldowns, overlay state |
| `raspi/gesture_engine/core/workers.py` | Three worker threads |
| `raspi/gesture_engine/core/matching.py` | Gesture normalization + config matching (cached) |
| `raspi/gesture_engine/core/actions.py` | Cooldown logic, action routing |
| `raspi/gesture_engine/core/wake_gate.py` | Enable/disable gesture filtering |
| `raspi/server/main.py` | FastAPI routes |
| `raspi/server/file.py` | `configure.json` read/write |
| `raspi/server/ha_transport.py` | HA REST calls + volume throttle |

---

## Code Guidelines (from `guideline.md`)

These are load-bearing rules — violations will be rejected in review.

**Threading:** Always use `threading.Event` or `threading.Condition` to signal between threads. No `while True: time.sleep(0.01)` polling.

**Queue backpressure:** Use `put_nowait()` and catch `queue.Full` to drop stale data. Never block the camera/producer thread on a full queue.

**Caching:** Use `functools.lru_cache` for repeated string normalization or high-frequency calculations inside tight loops.

**No object churn:** Do not instantiate objects inside the frame capture loop.

**Network concurrency (Dart):** Use `Future.any()` to race futures rather than sequential timeouts.

**Debounce:** High-frequency inputs (volume gestures) must be debounced with time locks before hitting external APIs.

**Anti-patterns to avoid:**
- Silent `except` blocks that swallow errors without logging
- `time.sleep()` inside worker loops (use blocking queue gets or event waits instead)
- Deep class hierarchies — prefer `dataclass` and stateless functions
