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

- **Important:** Real-time multi-phone configuration sync: if Phone X creates configs A and B, Phone Y should instantly show A and B in its dashboard cards; if Phone Y adds C, both phones should show A, B, and C without manual refresh or re-save.
- **Must-have:** Prevent duplicate mapping of the same `gesture + hand` pair (recommended default). If a user tries to save a duplicate, block it and prompt them to edit the existing mapping. Optional advanced mode: allow one-to-many mappings and execute all actions for that pair.
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
