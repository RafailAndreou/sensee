"""
build_exe.py  -  Run this to produce the Sensee Windows EXE.

Usage (inside the activated venv):
    python build_exe.py

The output will be in:
    dist/sensee/sensee.exe
"""

import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def ensure_pyinstaller():
    try:
        import PyInstaller  # noqa: F401
        print("[OK] PyInstaller already installed.")
    except ImportError:
        print("[...] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller installed.")


def build():
    ensure_pyinstaller()
    spec_path = os.path.join(HERE, "sensee.spec")
    print("\n[BUILD] Building EXE from: {}\n".format(spec_path))
    subprocess.check_call(
        [sys.executable, "-m", "PyInstaller", "--clean", spec_path],
        cwd=HERE,
    )
    exe_path = os.path.join(HERE, "dist", "sensee", "sensee.exe")
    print("\n[DONE] EXE is at:\n    {}\n".format(exe_path))


if __name__ == "__main__":
    build()
