# Sensee Mobile App — Codebase Flow Documentation

## Entry Points

### `lib/main.dart`
The sole entry point. Execution flow:
1. `loadConfigurationsFromFile()` — loads saved gesture configs from local JSON
2. `initLocale()` — initializes language preference
3. Renders `MaterialApp` with `ServerConnectivityBanner` + `Dashboard` as home
4. Listens for theme/locale changes via `ValueListenableBuilder`
5. No named routes — uses `Navigator.push`/`Navigator.pop` throughout

---

## Module/Component Map

```
lib/
├── main.dart                          # App bootstrap, theme/locale init
├── globals/
│   ├── global.dart                    # ConnectionConfig model, legacy ValueNotifiers
│   ├── connectionslist.dart           # Connection CRUD, JSON persistence, sync trigger
│   ├── app_theme.dart                 # Light/dark theme ValueNotifier
│   ├── locale.dart                    # EN/EL translations, t() function
│   └── sizes.dart                     # Responsive sizing helpers
├── l10n/
│   └── strings.dart                   # Static translation map (en/el)
└── screens/
    ├── dashboard/
    │   ├── dashboard.dart             # Main grid of gesture-to-action cards
    │   └── widgets/
    │       ├── dashboardcard.dart     # Individual connection card
    │       ├── dashboardnavigation.dart  # Bottom nav bar
    │       └── server_connectivity_banner.dart  # Server status banner
    ├── actions/
    │   ├── actiondetails.dart        # Gesture/action/hand selection screen
    │   └── widgets/
    │       ├── actionbutton.dart     # Action selector button
    │       ├── gesturebutton.dart    # Gesture selector button
    │       └── actionselectorcard.dart  # Selection card widget
    ├── devicetype/
    │   ├── devicetype.dart           # Device type grid (TV/AC/Light/Fan/PC)
    │   ├── connection_method.dart    # Choose: Smart Home / Pair TV / Classic IR
    │   ├── smartdevice_list.dart     # HA device browser & picker
    │   └── widgets/
    │       └── devicetypebutton.dart  # Device type button
    ├── brandselection/
    │   └── brandselection.dart       # IR brand search & selection
    ├── settings/
    │   ├── settings.dart             # Settings menu
    │   └── widgets/
    │       ├── settingsbutton.dart
    │       └── theme_toggle_card.dart
    ├── gesturesettings/
    │   └── gesture_settings.dart     # Wake gesture, hold duration, active window
    ├── cameraSettings/
    │   └── camera_settings.dart      # RTSP/HTTP camera URL config
    └── setup/
        ├── ha_settings.dart         # HA URL + token configuration
        └── pairing_wizard.dart       # HA device discovery & pairing
└── server/
    ├── server.dart                   # Barrel export: re-exports all services
    ├── discovery_service.dart       # mDNS/UDP/port-scan server discovery
    ├── config_service.dart          # Configuration sync with backend
    ├── ha_service.dart              # Home Assistant API calls
    └── camera.dart                  # MJPEG WebView player
```

---

## Data Flow

### Configuration Sync Flow

```
[User Action on Screen]
        ↓
[ConnectionConfig ValueNotifier updated]
        ↓
[connectionslist.dart: saveToFile()]
        ↓
[configurations.json written via path_provider]
        ↓
[ServerConnectivityBanner: sendAllConfigurations()]
        ↓
[ConfigService.sendAllConfigurations()]
        ↓
[ServerClient.POST /configuration]
        ↓
[FastAPI Server] → saves to configure.json → reloads GestureRuntime
```

### Server Discovery Flow (Priority Order)

```
1. mDNS query for "_sensee._tcp.local"
        ↓ (fail)
2. UDP broadcast to port 54321 with token "SENSEE_DISCOVER"
        ↓ (fail)
3. Concurrent port scan:
   - sensee.local:8000-8004
   - 127.0.0.1:8000-8004
   - 10.0.2.2:8000-8004
        ↓
[ServerClient cached in _cachedClient]
```

### New Connection Flow

```
[Dashboard] → tap "+"
        ↓
[DeviceType screen] → select type (TV/AC/Light/Fan/PC)
        ↓
[ConnectionMethod screen] → choose path:
   ├── Smart Home (HA) → [SmartDeviceList] → select HA entity
   ├── Pair New TV → [PairingWizard] → OAuth/PIN flow
   └── Classic IR → [BrandSelection] → search & select brand
        ↓
[ActionDetails screen] → select:
   - Action (e.g., "Power", "Volume Up")
   - Gesture (e.g., "Swipe Right", "Pinch")
   - Hand (Left/Right)
        ↓
[saveNewConnection()] → validates no duplicate → saves
        ↓
[connectionslist.dart] → persists → triggers sync
```

---

## Key Dependencies

```
┌─────────────────────────────────────────────────────────┐
│                      main.dart                          │
│                   (bootstrap only)                      │
└─────────────────────┬───────────────────────────────────┘
                      │ imports
         ┌────────────┴────────────┐
         ↓                        ↓
┌─────────────────┐      ┌──────────────────┐
│  globals/       │      │  screens/        │
│  (state + util) │      │  (UI + actions)  │
└────────┬────────┘      └────────┬─────────┘
         │                        │
         └────────┬───────────────┘
                  │ imports
                  ↓
        ┌─────────────────┐
        │    server/     │
        │  (network I/O) │
        └────────┬────────┘
                 │ HTTP calls
                 ↓
      ┌──────────┴──────────┐
      ↓                     ↓
[FastAPI Server]    [Home Assistant API]
(gesture engine)    (smart home)
```

### Module Responsibilities

| Module | Depends On | Purpose |
|---|---|---|
| `globals/global.dart` | — | Core `ConnectionConfig` model |
| `globals/connectionslist.dart` | `global.dart`, `server/` | Connection persistence + sync orchestration |
| `globals/app_theme.dart` | — | Theme state management |
| `globals/locale.dart` | `l10n/strings.dart` | Localization |
| `screens/*/` | `globals/`, `server/` | UI + user actions → update state |
| `server/discovery_service.dart` | — | Server location via mDNS/UDP/port scan |
| `server/config_service.dart` | `discovery_service.dart` | Config JSON sync |
| `server/ha_service.dart` | `discovery_service.dart` | HA API calls |

---

## Request/Event Lifecycle

### Example: User creates a new TV Power gesture

```
Timeline:
─────────────────────────────────────────────────────────────────

T+0ms   [Dashboard] User taps "+" button
        → Navigator.push(DeviceTypeScreen)

T+2s    [DeviceType] User selects "TV"
        → Navigator.push(ConnectionMethodScreen)

T+3s    [ConnectionMethod] User selects "Classic IR"
        → Navigator.push(BrandSelectionScreen)

T+5s    [BrandSelection] User searches "Samsung" and selects
        → saveBrand("Samsung") → Navigator.pop() back to ActionDetails

T+6s    [ActionDetails] User selects:
        - Action: "Power"
        - Gesture: "Swipe Up"
        - Hand: "Right"
        → Tap "Save"

T+6.1ms [ActionDetails] validateNoDuplicate(): checks all connections
        → Pass, continue

T+6.2ms [ActionDetails] createConnectionConfig():
        - id = nextId()
        - connectionType = "ir"
        - brand = "Samsung"
        - action = "Power"
        - gesture = "Swipe Up"
        - hand = "Right"
        → addNewConnection(config)

T+6.3ms [connectionslist.dart] addNewConnection():
        - connections[id] = config
        - connectionsList.value.add(id)
        → saveToFile() → write configurations.json

T+6.4ms [connectionslist.dart] trigger server sync:
        → server.sendAllConfigurations()

T+6.5ms [config_service.dart] sendAllConfigurations():
        - server = await getServerClient()
        - body = JSON of all connections
        → POST server.configUri

T+6.6ms [FastAPI /configuration endpoint]:
        - Validate payload
        - Write configure.json
        - Signal GestureRuntime to reload
        - Return 200 OK

T+7ms    [Dashboard] rebuilds via ValueListenableBuilder
        → Shows new card for "Samsung TV → Swipe Up (Right)"
```

---

## External Integrations

### 1. FastAPI Server (`raspi/server/`)

**Purpose:** Configuration sync + MJPEG video stream

| Endpoint | Method | Direction | Purpose |
|---|---|---|---|
| `/configuration` | POST | App → Server | Sync gesture-to-action mappings |
| `/ping` | GET | App → Server | Server reachability check |
| `/video` | GET | App → Server | MJPEG stream (via WebView) |
| `/gesture-settings` | GET/POST | App → Server | Sync gesture settings |
| `/camera-settings` | GET/POST | App → Server | Sync camera settings |
| `/ha/config` | GET/POST | App → Server | HA credentials storage |
| `/smart-devices` | GET | App → Server | List HA entities |
| `/discover` | POST | App → Server | HA device pairing |

**Protocol:** HTTP over local network (WiFi)

---

### 2. Home Assistant REST API

**Purpose:** Smart home device control

| Operation | HA Endpoint | Triggered By |
|---|---|---|
| List entities | `GET /states` | SmartDeviceList screen |
| Call service | `POST /services/{domain}/{service}` | Gesture match → action dispatch |
| Config save | `POST /config` | HA Settings screen |

**Protocol:** HTTPS (or HTTP) to HA instance at configured URL

---

### 3. mDNS / UDP Discovery

**Purpose:** Locate server on local network without hardcoded IP

| Method | Protocol | Details |
|---|---|---|
| mDNS | Multicast DNS | Query `_sensee._tcp.local` TXT record for `url` |
| UDP Broadcast | Port 54321 | Send `SENSEE_DISCOVER` token, await `SENSEE_FOUND` response |
| Port Scan | TCP | Probe fallback hosts on ports 8000-8004 |

**Storage:** Discovered URL cached in `ServerClient._cachedClient`

---

### 4. Local Persistence

| Data | Storage | Location |
|---|---|---|
| Gesture configs | JSON file | `configurations.json` via `path_provider` |
| App theme | Key-value | SharedPreferences `app_theme` |
| App locale | Key-value | SharedPreferences `app_locale` |
| Gesture settings | Key-value | SharedPreferences keys |
| Camera settings | Key-value | SharedPreferences keys |

---

## Config & Environment

### Discovery Constants (`server/discovery_service.dart:8-14`)

```dart
const _DISCOVERY_PORT = 54321;
const _DISCOVERY_TOKEN = "SENSEE_DISCOVER";
const _DISCOVERY_RESPONSE = "SENSEE_FOUND";
const _FALLBACK_HOSTS = ["sensee.local", "127.0.0.1", "10.0.2.2"];
const _FALLBACK_PORTS = [8000, 8001, 8002, 8003, 8004];
```

### Sync Intervals

| Operation | Interval | Location |
|---|---|---|
| Server connectivity check | 2 seconds | `dashboard.dart` (`Timer.periodic`) |
| Configuration sync | On every change | `connectionslist.dart` (post-save) |

### State Management Pattern

Uses `ValueNotifier` + `ValueListenableBuilder` — a custom reactive pattern (not BLoC/Riverpod/Provider despite `provider` being in pubspec.yaml):

```dart
// Example: Theme
ValueNotifier<String> appTheme = ValueNotifier("light");
ValueListenableBuilder<String>(
  valueListenable: appTheme,
  builder: (_, theme, __) => MaterialApp(theme: theme == "dark" ? darkTheme : lightTheme)
)
```

### Environment Variables

None at app level — all config comes from:
- User input (HA URL/token, camera URL, gesture settings)
- Auto-discovery (server location)
- Local persistence (SharedPreferences, JSON file)

---

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                         MOBILE APP                                  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                        screens/                              │  │
│  │  ┌────────┐ ┌────────────┐ ┌──────────┐ ┌──────────┐        │  │
│  │  │Dashboard│ │ActionDetails│ │Settings │ │Camera    │        │  │
│  │  └────┬───┘ └──────┬─────┘ └────┬────┘ └────┬─────┘        │  │
│  │       │            │           │           │               │  │
│  │       └────────────┼───────────┼───────────┘               │  │
│  │                    ↓           ↓                           │  │
│  │  ┌──────────────────────────────────────────────────────┐   │  │
│  │  │                    globals/                          │   │  │
│  │  │  connectionslist.dart  │  global.dart  │  app_theme  │   │  │
│  │  └────────────────────────────┬───────────────────────┘   │  │
│  │                               ↓                             │  │
│  │  ┌──────────────────────────────────────────────────────┐   │  │
│  │  │                     server/                           │   │  │
│  │  │  discovery_service │ config_service │ ha_service     │   │  │
│  │  └────────────────────────────┬───────────────────────┘   │  │
│  └───────────────────────────────┼────────────────────────────┘  │
│                                  │                                 │
│                    ┌─────────────┴─────────────┐                  │
│                    ↓                           ↓                  │
│         ┌──────────────────┐      ┌────────────────────┐           │
│         │  FastAPI Server  │      │  Home Assistant    │           │
│         │ (raspi/server/)  │      │  REST API         │           │
│         └────────┬─────────┘      └────────────────────┘           │
│                  ↓                                                │
│         ┌──────────────────┐                                      │
│         │  Gesture Engine  │                                      │
│         │ (raspi/gesture_)  │                                      │
│         └──────────────────┘                                      │
└────────────────────────────────────────────────────────────────────┘
```

---

## File Responsibilities Detail

| File | Responsibility |
|---|---|
| `main.dart` | Bootstrap, render MaterialApp with reactive theme/locale |
| `globals/connectionslist.dart` | Central hub: manages all connections, persistence, sync trigger |
| `globals/global.dart` | `ConnectionConfig` model — holds id, type, entity, brand, action, gesture, sound, hand, isSynced |
| `server/discovery_service.dart` | Locate server via mDNS → UDP → port scan. Caches `ServerClient` |
| `server/config_service.dart` | Serialize connections to JSON, POST to `/configuration`, sync settings |
| `server/ha_service.dart` | Direct HA API calls: list states, call services, get config |
| `server/camera.dart` | `VideoPage` — WebView loading MJPEG stream from `/video` endpoint |
| `screens/dashboard/dashboard.dart` | Main grid UI, periodic connectivity check, navigation hub |
| `screens/actions/actiondetails.dart` | Create/edit gesture mappings: action + gesture + hand selection |
| `screens/devicetype/smartdevice_list.dart` | Fetch HA entities, filter by domain, let user select |
| `screens/setup/pairing_wizard.dart` | HA device discovery flow with OAuth + PIN entry |