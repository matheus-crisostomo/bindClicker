"""
Global constants for BindClicker application.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Application Info
# ---------------------------------------------------------------------------
APP_NAME = "BindClicker"
APP_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Paths  (resolved relative to the project root)
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    # Running as a compiled executable
    BASE_DIR = os.path.dirname(sys.executable)
    # PyInstaller extracts bundled data files (like assets) into sys._MEIPASS
    BUNDLE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BUNDLE_DIR = BASE_DIR

DATA_DIR = os.path.join(BASE_DIR, "data")
SCRIPTS_DIR = os.path.join(DATA_DIR, "scripts")
HISTORY_DIR = os.path.join(DATA_DIR, "history")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

ASSETS_DIR = os.path.join(BUNDLE_DIR, "assets")
APP_ICON = os.path.join(ASSETS_DIR, "icon.ico")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

# ---------------------------------------------------------------------------
# Default Hotkeys  (pynput Key names)
# ---------------------------------------------------------------------------
DEFAULT_HOTKEY_TOGGLE_RECORD = "f6"
DEFAULT_HOTKEY_EXECUTE = "f7"
DEFAULT_HOTKEY_EMERGENCY_STOP = "f8"

# ---------------------------------------------------------------------------
# Player Limits
# ---------------------------------------------------------------------------
SPEED_MIN = 0.25
SPEED_MAX = 4.0
SPEED_DEFAULT = 1.0

REPEAT_INFINITE = 0          # 0 means infinite
REPEAT_DEFAULT = 1

RANDOM_DELAY_MIN = 0         # ms
RANDOM_DELAY_MAX = 2000      # ms
RANDOM_DELAY_DEFAULT = 0     # ms (no random delay by default)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE = os.path.join(LOGS_DIR, "bindclicker.log")
LOG_MAX_BYTES = 5 * 1024 * 1024   # 5 MB
LOG_BACKUP_COUNT = 3
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ---------------------------------------------------------------------------
# Script file version (for import/export compatibility)
# ---------------------------------------------------------------------------
SCRIPT_FORMAT_VERSION = "1.0"
