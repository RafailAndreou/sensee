"""
build_exe.py  -  Run this to produce the Sensee Windows EXE.

Usage (inside the activated venv):
    python build_exe.py

The output will be in:
    dist/sensee-x64/sensee-x64.exe
A zip archive will also be created in:
    dist/sensee-x64.zip
"""

import subprocess
import sys
import os
import zipfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def ensure_pyinstaller():
    try:
        import PyInstaller  # noqa: F401
        print("[OK] PyInstaller already installed.")
    except ImportError:
        print("[...] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller installed.")


def zip_build():
    build_dir = os.path.join(HERE, "dist", "sensee-x64")
    zip_path = os.path.join(HERE, "dist", "sensee-x64.zip")
    print("\n[ZIP] Creating: {}\n".format(zip_path))
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(build_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.join(HERE, "dist"))
                zf.write(file_path, arcname)
    print("[DONE] Zip created at:\n    {}\n".format(zip_path))


def build():
    ensure_pyinstaller()
    spec_path = os.path.join(HERE, "sensee.spec")
    print("\n[BUILD] Building EXE from: {}\n".format(spec_path))
    subprocess.check_call(
        [sys.executable, "-m", "PyInstaller", "--clean", "-y", spec_path],
        cwd=HERE,
    )
    exe_path = os.path.join(HERE, "dist", "sensee-x64", "sensee-x64.exe")
    print("\n[DONE] EXE is at:\n    {}\n".format(exe_path))
    zip_build()


if __name__ == "__main__":
    build()
