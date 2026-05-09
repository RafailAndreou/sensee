# Sensee Raspi — Codebase Flow Documentation

## Entry Points

### `gesture.py`
The sole entry point. Execution flow:
1. `start_fastapi_server_in_background()` — launches FastAPI on ports 8000–8004 in a daemon thread
2. `register_mdns_service()` — advertises `_sensee._tcp.local` on the network
3. `start_udp_discovery_service()` — listens on port 54321 for `SENSEE_DISCOVER` broadcasts
4. `open_camera_capture()` — opens local device 0 or network stream URL
5. `GestureApp.run()` — main loop: capture → MediaPipe → touch detection → gesture gate → queue

---

## Module/Component Map

```
raspi/
├── gesture.py                            # App bootstrap, main camera/detection loop
├── requirements.txt                      # Python dependencies
├── gesture_engine/
│   ├── __init__.py                       # Public API barrel export
│   ├── capture.py                        # Camera source selection (local/network)
│   ├── camera.py                         # Deprecated alias → geometry.py
│   ├── geometry.py                       # Screen metrics, touch detection, coord translation
│   ├── overlay.py                        # Visual action label overlay on video frame
│   ├── runtime.py                        # Central runtime: queues, events, threading wiring
│   ├── server_runner.py                  # FastAPI server launcher (background thread)
│   └── core/
│       ├── __init__.py
│       ├── actions.py                    # Gesture→action dispatch + cooldown enforcement
│       ├── confirmation.py               # Touch gesture debounce (N consecutive frames)
│       ├── matching.py                   # Gesture name normalization + config lookup
│       ├── movement.py                   # Wrist position monitor → left/right events
│       ├── wake_gate.py                  # Optional arm/disarm gate for gesture recognition
│       ├── workers.py                    # Background worker loop implementations
│       └── handlers/
│           ├── __init__.py
│           ├── action_queue.py           # Latest-only queue semantics helper
│           ├── ha_handler.py             # Smart device routing (volume fast-path vs queue)
│           ├── ir_handler.py             # IR device routing (serialized queue)
│           └── pc_handler.py             # PC action execution (browser/pyautogui)
└── server/
    ├── __init__.py                       # Barrel: send_msg, set_frame_from_bgr
    ├── main.py                           # FastAPI app: all REST routes + lifespan
    ├── startup.py                        # Uvicorn port-retry runner (8000–8004)
    ├── models.py                         # Pydantic request/response schemas
    ├── events.py                         # Event log debouncer (0.18s per event type)
    ├── file.py                           # JSON file persistence (config/HA/gesture/camera)
    ├── discovery.py                      # mDNS registration + UDP broadcast responder
    ├── streamer.py                       # FrameHub: thread-safe MJPEG frame publisher
    ├── timing.py                         # Debouncer utility class
    ├── config_validation.py              # Gesture mapping conflict detection
    ├── ha_client.py                      # Low-level HA HTTP client (requests)
    ├── ha_config.py                      # HA URL/token thread-safe cache
    ├── ha_entities.py                    # HA entity fetch + 2s TTL cache
    ├── ha_pairing.py                     # HA config-entry pairing flow wrappers
    ├── ha_services.py                    # Action text → HA service name mapper
    ├── ha_transport.py                   # HA action executor + TV wake fallback logic
    └── homeassistant.py                  # Facade: re-exports all HA helpers
```

---

## Data Flow

### Gesture Detection → Action Execution

```
[Camera Frame]
      ↓
[cv2.VideoCapture.read()]
      ↓
[BGR→RGB conversion → mp.Image]
      ↓
[MediaPipe GestureRecognizer.recognize_async()]  (async LIVE_STREAM mode)
      ↓
[GestureApp.gesture_callback()]  (MediaPipe callback thread)
   ├── Full gestures: from MediaPipe result (e.g., "Swipe Up", "Open Palm")
   └── Touch gestures: manual thumb-finger Euclidean distance check
            (Thumb+Index, Thumb+Middle via geometry.touching())
      ↓
[TouchConfirmation.is_confirmed()]  — requires N consecutive frames (debounce)
      ↓
[WakeGate.allows()]  — blocks until wake sequence held (if enabled)
      ↓
[GestureRuntime.enqueue_gesture()]
      ↓
[gesture_queue (latest-only deque)] + [gesture_event.set()]
      ↓
[process_gestures_loop() — worker thread]
   ├── Confidence check  (≥0.70; ≥0.60 for open palm/fist)
   ├── Staleness check   (drops if too old)
   └── runtime.take_action(gesture_name, handedness)
      ↓
[find_matched_config()]  — hand-aware, alias-normalized lookup in active_configs
      ↓
[execute_configured_action()]
   ├── Cooldown check (per device/action type)
   ├── overlay.draw_action_overlay()  — visual label on frame
   └── Route by connectionType:
       ├── "pc"     → execute_pc_action()  (direct webbrowser / pyautogui)
       ├── "smart"  → handle_smart_device_action()
       │               ├── volume → non-blocking put to volume_queue
       │               └── other  → queue_latest_action() to action_queue
       └── "ir"     → handle_ir_device_action() → action_queue
```

### Action Queue → HA Execution

```
[action_queue]                    [volume_queue]
      ↓                                 ↓
[process_action_queue_loop()]    [process_volume_loop()]
      ↓                                 ↓ (no throttle)
[trigger_ha_action(entity_id, action)]
      ↓
[parse_action_to_service()]  — "turn on" → "turn_on", "volume up" → "volume_up"
      ↓
[HAClient.post_service()]  → POST /api/services/{domain}/{service}
      ↓ (if media_player turn_on and device still off after 350ms)
[_try_tv_wake_fallback()]
   ├── script.sensee_tv_power_on  (HA script entity)
   ├── wake switch toggle
   └── Wake-on-LAN magic packet
```

### Configuration Sync Flow

```
[Mobile App POST /configuration]
      ↓
[validate_configuration_payload()]  — conflict check (duplicate gesture+hand)
      ↓
[file.save_configure_json()]  → configure.json
      ↓
[file.set_loaded_config()]  — in-memory cache updated
      ↓
[Active configs used by find_matched_config() on next gesture]
```

### MJPEG Streaming Flow

```
[gesture.py:run() — main thread]
      ↓ (every frame after processing)
[set_frame_from_bgr(bgr_frame)]
      ↓
[FrameHub.set_bgr_frame()]
   ├── BGR → JPEG encode (cv2.imencode)
   ├── Store in _frame buffer
   └── frame_event.set()  — notify waiting clients
      ↓
[GET /video — HTTP client requests stream]
      ↓
[FrameHub.mjpeg_generator()]
   ├── Waits on frame_event (1s keep-alive if no new frame)
   └── Yields MJPEG multipart chunks
```

### Server Discovery Flow

```
[Startup]
      ↓
[register_mdns_service()]
   → Registers "Sensee Server._sensee._tcp.local." with zeroconf
   → TXT record includes url=http://{local_ip}:{port}
      ↓
[start_udp_discovery_service()]
   → Listens on UDP port 54321
   → On "SENSEE_DISCOVER" token: responds with IP/port/path
```

---

## Thread Architecture

| Thread | Spawned In | Role |
|---|---|---|
| Main (gesture loop) | `gesture.py:run()` | Camera capture, MediaPipe, frame publish, touch detection |
| FastAPI Server | `server_runner.py` | REST API: config, video, HA integration |
| Gesture Worker | `workers.start_workers()` | Consumes `gesture_queue`, routes to action dispatch |
| Action Worker | `workers.start_workers()` | Consumes `action_queue`, serializes HA/IR calls |
| Volume Worker | `workers.start_workers()` | Consumes `volume_queue`, high-frequency HA calls |
| Hand Movement Monitor | `movement.py` | Wrist position tracking → "Hand moved left/right" |
| Browser Opener | `server_runner.py` | Polls `/ping`, opens dashboard tab on ready |
| UDP Discovery | `discovery.py` | Responds to `SENSEE_DISCOVER` broadcast tokens |

All worker threads are **daemon threads** — they terminate when the main process exits.

---

## Key Dependencies

```
┌──────────────────────────────────────────────────────────────┐
│                        gesture.py                            │
│                     (bootstrap + loop)                       │
└──────────────────────────┬───────────────────────────────────┘
                           │ imports
          ┌────────────────┼───────────────────┐
          ↓                ↓                   ↓
┌──────────────────┐ ┌───────────────┐ ┌─────────────────┐
│ gesture_engine/  │ │ server/       │ │ gesture_engine/ │
│ capture.py       │ │ (REST + HA)   │ │ core/           │
│ overlay.py       │ └───────┬───────┘ │ (logic)         │
│ runtime.py       │         │         └────────┬────────┘
│ server_runner.py │         │                  │
└──────────────────┘         │                  │
                             ↓                  ↓
                   ┌──────────────────────────────┐
                   │      server/file.py           │
                   │   (JSON persistence layer)    │
                   └──────────────┬───────────────┘
                                  │
                    ┌─────────────┴──────────────┐
                    ↓                            ↓
          ┌──────────────────┐       ┌────────────────────┐
          │  configure.json  │       │  ha_config.json    │
          │  gesture_settings│       │  camera_settings   │
          └──────────────────┘       └────────────────────┘
```

### Module Responsibilities

| Module | Depends On | Purpose |
|---|---|---|
| `gesture.py` | `gesture_engine/`, `server/` | Bootstrap, camera loop, gesture detection |
| `gesture_engine/runtime.py` | `core/actions`, `core/workers` | Shared queues, events, threading wires |
| `gesture_engine/core/workers.py` | `runtime.py` | Worker loop bodies (gesture/action/volume) |
| `gesture_engine/core/actions.py` | `matching.py`, `handlers/*` | Dispatch: cooldown + route by device type |
| `gesture_engine/core/matching.py` | — | Alias normalization + hand-aware config lookup |
| `gesture_engine/core/wake_gate.py` | `server/file.py` | Arm/disarm gate; reloads settings every 1s |
| `gesture_engine/core/confirmation.py` | — | Per-(hand, gesture) consecutive-frame debounce |
| `gesture_engine/geometry.py` | — | Touch detection, coordinate translation |
| `gesture_engine/overlay.py` | — | Draw action label bar on OpenCV frame |
| `gesture_engine/capture.py` | `server/file.py` | Local vs network camera selection |
| `server/main.py` | all `server/*` | FastAPI routes: config, stream, HA |
| `server/file.py` | — | All JSON I/O; in-memory config cache |
| `server/ha_transport.py` | `ha_client`, `ha_config`, `ha_services` | Execute HA action + TV wake fallback |
| `server/ha_entities.py` | `ha_client`, `ha_config` | Fetch + cache HA entities (2s TTL) |
| `server/discovery.py` | — | mDNS registration + UDP broadcast responder |
| `server/streamer.py` | — | Thread-safe MJPEG frame hub |
| `server/config_validation.py` | — | Conflict detection in gesture mappings |

---

## API Reference

### REST Endpoints (`server/main.py`)

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Serve web dashboard (index.html or fallback) |
| `/ping` | GET | Health check — returns `{"status": "ok"}` |
| `/configuration` | POST | Validate + persist gesture-device mappings; reload runtime |
| `/configuration` | GET | Return current config from file |
| `/current` | GET | Return in-memory `AppState` config |
| `/smart-devices` | GET | List HA entities filtered by `?type=` |
| `/ha/config` | GET | Retrieve HA URL + masked token |
| `/ha/config` | POST | Save HA URL + token |
| `/ha/discovered` | GET | List discovered HA config-entry flows |
| `/ha/pair/start` | POST | Initiate HA pairing flow |
| `/ha/pair/submit` | POST | Submit pairing step input |
| `/video` | GET | MJPEG stream (multipart/x-mixed-replace) |
| `/event/{name}` | POST | Log named event to stdout (debounced) |
| `/gesture-settings` | GET/POST | Wake gesture config sync |
| `/camera-settings` | GET/POST | Camera URL / network mode sync |

---

## Persistence Layer

### Files (`server/file.py`)

| File | Content | Default Location |
|---|---|---|
| `configure.json` | Gesture-to-device mappings array | `SENSEE_DATA_DIR` or beside executable |
| `ha_config.json` | HA URL + token | Same directory |
| `gesture_settings.json` | Wake enabled, gesture, hold/window durations | Same directory |
| `camera_settings.json` | Camera URL + network flag | Same directory |

**In-memory cache**: `get_active_configs()` returns filtered list (items with id + gesture + action). Cache is updated on every POST `/configuration`.

**Environment fallbacks**:
- `SENSEE_HA_URL` — default HA base URL if `ha_config.json` absent
- `SENSEE_HA_TOKEN` — default HA token
- `SENSEE_DATA_DIR` — override data directory (used in PyInstaller builds)

---

## Config & Environment

### Cooldowns (`core/actions.py`)

| Action Type | Cooldown |
|---|---|
| Volume up/down | 0.0s (fire every frame) |
| turn on/off, open/close | 1.5s |
| Other HA/IR actions | ~1.5s (from `RuntimePolicy`) |

### Confidence Thresholds (`core/workers.py`)

| Gesture | Threshold |
|---|---|
| Open Palm, Closed Fist | 0.60 |
| All others | 0.70 |

### Discovery Constants (`server/discovery.py`)

```python
UDP_PORT        = 54321
DISCOVER_TOKEN  = "SENSEE_DISCOVER"
DISCOVER_RESP   = "SENSEE_FOUND"
MDNS_SERVICE    = "_sensee._tcp.local."
SERVER_PORTS    = [8000, 8001, 8002, 8003, 8004]  # tried in order
```

### Volume Throttle (`server/ha_transport.py`)

```python
SENSEE_VOLUME_INTERVAL = 50  # ms minimum between volume HA calls (env override)
```

### Wake Gate Defaults (`core/wake_gate.py`)

```python
holdDurationSeconds  = 1.0   # how long to hold wake gesture
activeWindowSeconds  = 5.0   # window after wake before re-arming
```

### TV Wake Fallback Env Vars (`server/ha_transport.py`)

```python
SENSEE_TV_WAKE_SCRIPT = "script.sensee_tv_power_on"  # HA script entity
SENSEE_TV_WAKE_SWITCH = ""                            # toggle switch entity
SENSEE_TV_WAKE_MAC    = ""                            # WOL MAC address
SENSEE_DEBUG_HA_TIMING = False                        # log HA response times
```

---

## Request/Event Lifecycle

### Example: Gesture "Swipe Up" → TV Volume Up

```
Timeline:
─────────────────────────────────────────────────────────────────

T+0ms    [Camera frame captured]
         → cv2.VideoCapture.read() → BGR frame
         → BGR→RGB → mp.Image

T+1ms    [MediaPipe recognize_async()]
         → Async callback scheduled

T+3ms    [gesture_callback() fires]
         → result.gestures[0][0].category_name = "Pointing_Up"
         → confidence = 0.88

T+3.1ms  [TouchConfirmation] — not a touch gesture, skip

T+3.2ms  [WakeGate.allows("Pointing_Up")]
         → wake mode disabled → allow

T+3.3ms  [GestureRuntime.enqueue_gesture("Pointing_Up", "Right")]
         → gesture_queue[0] = ("Pointing_Up", "Right", timestamp, conf)
         → gesture_event.set()

T+3.4ms  [process_gestures_loop() wakes]
         → pop_latest_gesture()
         → confidence 0.88 ≥ 0.70 ✓
         → staleness check ✓
         → runtime.take_action("Pointing_Up", "Right")

T+3.5ms  [find_matched_config(active_configs, "Pointing_Up", "Right")]
         → canonical: "pointing up"
         → match: {id:3, gesture:"pointing up", action:"volume up",
                   connectionType:"smart", entityId:"media_player.living_room_tv",
                   hand:"right"}

T+3.6ms  [execute_configured_action()]
         → cooldown check: volume → 0.0s → allow
         → overlay: "Volume Up" label queued for 1.5s
         → handle_smart_device_action("volume up", "media_player.living_room_tv", ...)

T+3.7ms  [handle_smart_device_action()]
         → action is volume → non-blocking put to volume_queue

T+3.8ms  [process_volume_loop() wakes]
         → trigger_ha_action("media_player.living_room_tv", "volume up")
         → parse_action_to_service("volume up") → service="volume_up"
         → domain = "media_player"
         → HAClient.post_service("media_player", "volume_up",
                                  {"entity_id": "media_player.living_room_tv"})

T+5ms    [Home Assistant API]
         → POST /api/services/media_player/volume_up  → 200 OK
         → TV volume increases
```

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                          RASPI PROCESS                               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                      gesture.py (main)                       │    │
│  │  Camera → MediaPipe → Touch Detection → WakeGate → Queue     │    │
│  └───────────────────────────┬──────────────────────────────────┘    │
│                              │                                       │
│         ┌────────────────────┼───────────────────┐                  │
│         ↓                    ↓                   ↓                  │
│  ┌─────────────┐    ┌──────────────────┐  ┌────────────────┐        │
│  │ gesture_    │    │ gesture_engine/  │  │ server/        │        │
│  │ engine/     │    │ core/            │  │ FastAPI app    │        │
│  │ runtime.py  │◄──►│ workers.py       │  │                │        │
│  │ (queues)    │    │ actions.py       │  │ /configuration │        │
│  └──────┬──────┘    │ matching.py      │  │ /video         │        │
│         │           │ wake_gate.py     │  │ /ha/*          │        │
│         │           └──────────────────┘  └───────┬────────┘        │
│         │                                         │                 │
│         │           ┌──────────────────┐          │                 │
│         └──────────►│ handlers/        │          │                 │
│                     │ ha_handler       │          ▼                 │
│                     │ ir_handler       │  ┌────────────────┐        │
│                     │ pc_handler       │  │ server/file.py │        │
│                     └────────┬─────────┘  │ (persistence)  │        │
│                              │            └───────┬────────┘        │
│                              ↓                    │                 │
│                     ┌────────────────┐            ↓                 │
│                     │ server/        │  ┌──────────────────────┐    │
│                     │ ha_transport   │  │   JSON files         │    │
│                     │ ha_client      │  │   configure.json     │    │
│                     │ ha_entities    │  │   ha_config.json     │    │
│                     └────────┬───────┘  │   gesture_settings   │    │
│                              │          │   camera_settings    │    │
└──────────────────────────────┼──────────┴──────────────────────┘    │
                               │                                       
          ┌────────────────────┴──────────────┐                        
          ↓                                   ↓                        
┌──────────────────────┐           ┌──────────────────────┐            
│  Home Assistant API  │           │   Mobile App         │            
│  /api/services/...   │           │   POST /configuration│            
│  /api/states/...     │           │   GET  /video        │            
└──────────────────────┘           └──────────────────────┘            
```

---

## File Responsibilities Detail

| File | Responsibility |
|---|---|
| `gesture.py` | Entry point: camera loop, MediaPipe orchestration, touch detection, frame publishing |
| `gesture_engine/runtime.py` | Shared state hub: `gesture_queue`, `action_queue`, `volume_queue`, events, worker spawning |
| `gesture_engine/core/workers.py` | Three worker loops: gesture consumer, action serializer, volume fast-path |
| `gesture_engine/core/actions.py` | Cooldown gating + routing by `connectionType` (smart/ir/pc) |
| `gesture_engine/core/matching.py` | Alias normalization, canonical names, hand-aware config lookup |
| `gesture_engine/core/wake_gate.py` | Arm/disarm state machine; loads settings from file with 1s throttle |
| `gesture_engine/core/confirmation.py` | Per-(hand, gesture) streak counter; requires N consecutive frames |
| `gesture_engine/core/handlers/ha_handler.py` | Volume → `volume_queue` (drop-if-busy); other → `action_queue` |
| `gesture_engine/core/handlers/ir_handler.py` | All IR → `action_queue` for serial execution |
| `gesture_engine/core/handlers/pc_handler.py` | Direct execution: `webbrowser.open_new_tab()` / `pyautogui.hotkey()` |
| `gesture_engine/geometry.py` | `touching()` euclidean check, `translate_coords()` mirror+scale, `get_screen_metrics()` |
| `gesture_engine/overlay.py` | Semi-transparent label bar drawn on OpenCV frame for 1.5s |
| `gesture_engine/capture.py` | Selects camera source: network stream URL or local device 0 |
| `gesture_engine/server_runner.py` | Starts uvicorn in daemon thread; polls `/ping` to open dashboard |
| `server/main.py` | All FastAPI routes; `AppState` in-memory mirror; lifespan for mDNS |
| `server/file.py` | All JSON reads/writes; active config cache; `SENSEE_DATA_DIR` resolution |
| `server/ha_transport.py` | `trigger_ha_action()`: volume throttle, post service, TV wake fallback |
| `server/ha_client.py` | `requests.Session` wrapper for HA REST API (0.8s/2.2s timeouts) |
| `server/ha_entities.py` | Fetch all HA states, map domains to device types, cache 2s TTL |
| `server/ha_services.py` | Text action → HA service name (e.g., "volume up" → "volume_up") |
| `server/ha_config.py` | Thread-safe URL/token cache; env var fallback |
| `server/ha_pairing.py` | Thin wrappers for HA config-entry flow API (start/submit/list) |
| `server/homeassistant.py` | Single-import facade re-exporting all HA helpers |
| `server/discovery.py` | Zeroconf mDNS registration + UDP socket listener on port 54321 |
| `server/streamer.py` | `FrameHub`: thread-safe JPEG buffer with `frame_event` for waiting consumers |
| `server/config_validation.py` | Rejects duplicate gesture+hand; rejects "both" mixed with "left"/"right" |
| `server/events.py` | `send_msg()` with 0.18s debounce per event type to prevent log spam |
| `server/models.py` | Pydantic schemas: `Configuration`, `GestureSettings`, `CameraSettings`, `HAConfigRequest` |
| `server/startup.py` | `run_uvicorn_with_port_retry()`: tries ports 8000→8004 on bind failure |
| `server/timing.py` | `Debouncer` class: returns True if elapsed ≥ interval since last trigger |
