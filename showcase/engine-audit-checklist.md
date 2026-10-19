# Engine audit follow-up checklist

This follow-up applies to `alt`, starting at
`02b267363ac95f13c29cacc10b312c5af67ece3f`.

## Completed behavior

- [x] Bind camera URL and capture properties to one revision/epoch snapshot.
  Discard handles opened across a change and frames read across a change;
  neither old frames nor queued commands receive a fresh timestamp or epoch.
- [x] Keep Home Assistant network I/O outside the observation/settings lock.
  Recheck original command freshness, epoch and test mode after session
  preparation, immediately before HTTP handoff. Recheck delayed TV wake work.
- [x] Normalize legacy wake/mapping aliases to the same browser, Flutter and
  server labels. Invalidate the wake cache and active window immediately on
  configuration changes.
- [x] Clear calibration contact/open samples and completed results on every epoch
  change, in every phase. A new contact sample is required before open sampling.
- [x] Require two consecutive observations and limit held brightness, fan speed,
  temperature and scene/script activation mappings to one transition. Apply
  confirmation and cooldown to both native poses and contact gestures; uncertain
  observations do not rearm a held gesture.
- [x] Record rejection reasons for confidence, missing mapping/source, queue
  capacity, superseded work, stale/mismatched commands, wake gate, cooldown,
  invalid targets/actions, dispatch cancellation and HTTP errors. Keep recent
  decisions bounded to 64 entries. Coalesced volume requests have a separate
  diagnostic decision.
- [x] Protect Flutter camera/wake drafts from delayed local/server loads; reject
  ETag adoption from obsolete loads. Keep failed saves and later edits in forms.
  Browser renders reject obsolete loads. Debounced browser saves capture their
  payload before navigation. Flutter Ironman saves retain their loaded revision
  rather than silently rebasing with a GET immediately before saving.
- [x] Add regressions reproducing camera-open/read races, blocking HA transport,
  cancellation during session preparation, wake-cache delay, calibration phase
  mixing, missing confirmation/held limiting, rejection diagnostics, legacy
  aliases, late settings loads, conflicts and pending saves.

## Validation and remaining limits

The Python suite includes the actual pinned MediaPipe library and repository
model, exercising IMAGE and LIVE_STREAM graphs on a blank image. This checks
native model loading and callback integration; it does **not** validate real-hand
recognition accuracy. UI/gesture regressions use synthetic landmarks and mocked
network/hardware boundaries. Full suite totals are recorded in the commit's
completion report; CI also checks the pushed revision.

- An HTTP request already handed to `requests` cannot reliably be retracted.
  Epoch changes prevent pending/follow-up dispatch, but cannot guarantee that
  Home Assistant has not already received an in-flight request.
- Capture properties remain driver/backend requests. A stalled physical camera
  or decoder may delay reconnection; stale results cannot authorize output.
- Calibration remains **one thumb/index measurement applied to all fingers**.
  Per-finger calibration is not implemented or claimed.
- Unsaved drafts stay in the running form; closing a client can discard them.
  Review/reload is still required after a revision conflict.

## Hardware checks pending

- [ ] USB/RTSP camera source switching, disconnection and reconnect latency on a
  Raspberry Pi, including driver-negotiated dimensions/FPS and credential-safe
  backend output.
- [ ] Real hands: recognition confidence, handedness, wake hold timing, contact
  separation and held-gesture stability across users, lighting and camera ratios.
- [ ] Independent per-finger calibration implementation and validation, if wanted.
- [ ] Live Home Assistant lights/fans/climate/scenes/scripts, temperature units,
  advertised capabilities and the in-flight-request boundary under network delay.
- [ ] Real desktop cursor/keyboard/clipboard and microphone/voice output, including
  switching test mode during active output.
- [ ] Physical Android/iOS discovery, background/resume polling and settings UI
  behavior on devices.
