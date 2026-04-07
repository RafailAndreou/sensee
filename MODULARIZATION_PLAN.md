# Sensee Modularization Plan (main.py + gesture.py)

## Goals

- Reduce file size and mixed responsibilities in `raspi/server/main.py` and `raspi/gesture.py`.
- Keep runtime behavior unchanged.
- Keep public API/function names stable where possible.
- Make future features easier to add and test.

## Scope

- Modularize server-side models/validation from `main.py`.
- Modularize gesture matching/action execution/workers from `gesture.py`.
- Keep app entrypoints unchanged:
  - FastAPI app still in `raspi/server/main.py`
  - Camera loop still in `raspi/gesture.py`

## Target Structure

### Server (`raspi/server`)

1. `models.py`

- `Configuration`
- `HAConfigRequest`
- `HAPairStartRequest`
- `HAPairSubmitRequest`

2. `config_validation.py`

- `_normalize_config_value`
- `_normalize_hand_value`
- `_find_duplicate_gesture_hand`
- `_find_invalid_hand_combination`
- `validate_configuration_payload(configs)` -> returns error detail or `None`

3. `main.py`

- Keeps FastAPI routes and lifecycle hooks.
- Imports models and validation helpers.
- Keeps route behavior and response shapes the same.

### Gesture Runtime (`raspi`)

1. `gesture_runtime.py`

- Contains gesture/action logic now mixed in `gesture.py`:
  - normalization + canonical gesture matching
  - hand-aware config lookup
  - cooldown handling
  - action dispatch (PC/smart queue)
  - worker loops (`process_gestures`, `process_homeassistant_actions`)
- Exposes a runtime class with internal queues.

2. `gesture.py`

- Keeps camera capture loop, MediaPipe callback, and frame publishing.
- Instantiates and starts runtime workers.
- Delegates action/matching/queue processing to `gesture_runtime.py`.

## Implementation Steps

1. Extract server models into `raspi/server/models.py` and import from `main.py`.
2. Extract configuration validation into `raspi/server/config_validation.py` and call it from POST `/configuration`.
3. Create `raspi/gesture_runtime.py` and move pure gesture/action logic into class-based runtime.
4. Update `raspi/gesture.py` to use `GestureRuntime` while preserving existing behavior.
5. Run diagnostics (`get_errors`) on touched files.

## Non-Goals (for this pass)

- No behavior changes to endpoints.
- No protocol changes between Flutter and backend.
- No large UI refactor.

## Validation Checklist

- No new static errors in touched files.
- `main.py` still exposes same routes.
- Gesture detection still logs detections and triggers actions.
- Home Assistant action queue still runs in background.
