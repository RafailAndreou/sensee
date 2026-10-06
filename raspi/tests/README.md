# Raspi tests

This folder uses `unittest`.

Install `pip install -r requirements-test.txt` for the focused test dependencies,
or install those alongside the engine requirements. API tests use temporary
settings and mocked discovery; they do not pair devices or contact Home Assistant.

Run the suite from the `raspi` directory:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

The suite covers inference freshness, contact priority, wake continuity,
confirmation delivery, per-target cooldowns, cursor precision, voice overflow
and cancellation, demand-driven preview encoding, settings cache invalidation,
port fallback, discovery payloads, and engine cleanup. Gesture agreement checks
cover changed gestures, tracking loss, bounded one-shot flicker tolerance, and
Home Assistant follow-ups. Camera and model operations
are simulated; these checks do not measure recognition accuracy or hardware
latency. PyAutoGUI needs a desktop session; on headless Linux run the suite under
Xvfb (for example, `xvfb-run -a python -m unittest discover -s tests`).

Test files should stay focused on one behavior area each, and shared test setup should go in `tests/__init__.py` instead of being duplicated in every file.
