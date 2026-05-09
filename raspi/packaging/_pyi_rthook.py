# _pyi_rthook.py
# PyInstaller runtime hook – executed BEFORE gesture.py starts inside the EXE.
#
# Responsibilities:
#   1. Patch sys.path so "server.*" and "gesture_engine.*" imports work.
#   2. Provide a sys._MEIPASS-aware base-path helper used by gesture.py
#      to locate the bundled gesture_recognizer.task model.
#   3. Copy default configure.json / ha_config.json from the read-only
#      bundle to the writable EXE directory on first run, so the server
#      can persist user config there.

import sys
import os
import shutil

# ── 1. Ensure frozen bundle root is on sys.path ─────────────────────────────
_bundle_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
if _bundle_dir not in sys.path:
    sys.path.insert(0, _bundle_dir)

# ── 2. Locate the writable EXE directory ────────────────────────────────────
# When frozen, the EXE itself lives in the same folder as the _internal/ dir.
_exe_dir = os.path.dirname(sys.executable)

# ── 3. Copy default config files to the EXE directory on first run ──────────
_defaults_src = os.path.join(_bundle_dir, "server_defaults")
_config_names = ["configure.json", "ha_config.json"]

for _cfg in _config_names:
    _dest = os.path.join(_exe_dir, _cfg)
    if not os.path.exists(_dest):
        _src = os.path.join(_defaults_src, _cfg)
        if os.path.exists(_src):
            shutil.copy2(_src, _dest)

# ── 4. Set an env var so server/file.py can find the writable config dir ────
os.environ["SENSEE_DATA_DIR"] = _exe_dir
