"""
PyInstaller build script for BindClicker.

Run:  py build.py
Produces:  dist/BindClicker/BindClicker.exe  (one-dir mode, faster startup)
"""

import subprocess
import sys

def main():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "BindClicker",
        "--icon", "assets/icon.ico",
        "--onefile",                     # single portable .exe
        "--windowed",                    # no console window
        "--noconfirm",                   # overwrite without asking
        "--clean",                       # clean cache before building
        # Include all subpackages
        "--hidden-import", "pynput.keyboard._win32",
        "--hidden-import", "pynput.mouse._win32",
        "--hidden-import", "pynput._util.win32",
        "--hidden-import", "customtkinter",
        # Collect customtkinter data files (themes, etc.)
        "--collect-data", "customtkinter",
        # Bundle custom assets
        "--add-data", "assets;assets",
        # Entry point
        "main.py",
    ]
    print("Building BindClicker...")
    print(" ".join(cmd))
    result = subprocess.run(cmd, cwd=".")
    if result.returncode == 0:
        print("\n[OK] Build successful!")
        print("Executable: dist/BindClicker/BindClicker.exe")
    else:
        print("\n[FAIL] Build failed!")
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
