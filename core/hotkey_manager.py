"""
HotkeyManager – global hotkey listener with editable key bindings.

Hotkeys are persisted in data/settings.json so they survive restarts.
The UI can call `capture_next_key()` to enter "listening" mode;
the very next physical key press will be set as the new hotkey.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Callable, Dict, Optional

from pynput import keyboard

from utils.constants import (
    DEFAULT_HOTKEY_EMERGENCY_STOP,
    DEFAULT_HOTKEY_EXECUTE,
    DEFAULT_HOTKEY_TOGGLE_RECORD,
    SETTINGS_FILE,
)
from utils.logger import get_logger

logger = get_logger("core.hotkey_manager")


class HotkeyManager:
    """Manages global hotkeys with runtime re-binding and key capture."""

    # The three logical actions
    ACTION_TOGGLE_RECORD = "toggle_record"
    ACTION_EXECUTE = "execute"
    ACTION_EMERGENCY_STOP = "emergency_stop"

    def __init__(self) -> None:
        # action_name → key name string (e.g. "f6")
        self._bindings: Dict[str, str] = {
            self.ACTION_TOGGLE_RECORD: DEFAULT_HOTKEY_TOGGLE_RECORD,
            self.ACTION_EXECUTE: DEFAULT_HOTKEY_EXECUTE,
            self.ACTION_EMERGENCY_STOP: DEFAULT_HOTKEY_EMERGENCY_STOP,
        }

        # action_name → callable
        self._callbacks: Dict[str, Callable] = {}

        self._listener: Optional[keyboard.Listener] = None
        self._running = False

        # Key-capture state
        self._capture_action: Optional[str] = None
        self._capture_callback: Optional[Callable[[str], None]] = None
        self._capture_lock = threading.Lock()

        self._load_settings()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    @property
    def bindings(self) -> Dict[str, str]:
        """Return a copy of current hotkey bindings."""
        return dict(self._bindings)

    def get_binding(self, action: str) -> str:
        return self._bindings.get(action, "")

    def get_all_hotkey_keys(self) -> set[str]:
        """Return a set of all bound key names (for the recorder to ignore)."""
        return {v.lower() for v in self._bindings.values()}

    def set_callback(self, action: str, callback: Callable) -> None:
        """Register a callback for a hotkey action."""
        self._callbacks[action] = callback

    def set_binding(self, action: str, key_name: str) -> None:
        """Change the key bound to an action and persist."""
        old = self._bindings.get(action)
        self._bindings[action] = key_name.lower()
        self._save_settings()
        logger.info("Hotkey changed: %s  %s → %s", action, old, key_name)

    def start(self) -> None:
        """Start the global keyboard listener."""
        if self._running:
            return
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()
        self._running = True
        logger.info("HotkeyManager listening – bindings: %s", self._bindings)

    def stop(self) -> None:
        """Stop the global keyboard listener."""
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._running = False
        logger.info("HotkeyManager stopped")

    # -----------------------------------------------------------------------
    # Key Capture ("press any key" mode)
    # -----------------------------------------------------------------------

    def capture_next_key(
        self,
        action: str,
        callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Enter capture mode: the next key pressed will be assigned to *action*.

        Args:
            action:   The logical action to rebind.
            callback: Optional function called with the captured key name.
        """
        with self._capture_lock:
            self._capture_action = action
            self._capture_callback = callback
        logger.debug("Capture mode ON for action '%s'", action)

    def cancel_capture(self) -> None:
        """Cancel an ongoing key capture."""
        with self._capture_lock:
            self._capture_action = None
            self._capture_callback = None

    @property
    def is_capturing(self) -> bool:
        with self._capture_lock:
            return self._capture_action is not None

    # -----------------------------------------------------------------------
    # Internal
    # -----------------------------------------------------------------------

    def _key_name(self, key) -> str:
        """Extract a lowercase name from a pynput key."""
        if hasattr(key, "name"):
            return key.name.lower()
        if hasattr(key, "char") and key.char:
            return key.char.lower()
        return str(key).lower()

    def _on_press(self, key) -> None:
        name = self._key_name(key)

        # --- Capture mode takes priority ---
        with self._capture_lock:
            if self._capture_action is not None:
                action = self._capture_action
                cb = self._capture_callback
                self._capture_action = None
                self._capture_callback = None

        # Check if we were in capture mode (variable set inside lock)
                self.set_binding(action, name)
                if cb:
                    try:
                        cb(name)
                    except Exception:
                        logger.exception("Error in capture callback")
                return

        # --- Normal hotkey dispatch ---
        for action, bound_key in self._bindings.items():
            if name == bound_key:
                cb = self._callbacks.get(action)
                if cb:
                    try:
                        cb()
                    except Exception:
                        logger.exception("Error in hotkey callback '%s'", action)
                return

    # -----------------------------------------------------------------------
    # Persistence
    # -----------------------------------------------------------------------

    def _save_settings(self) -> None:
        settings = self._load_all_settings()
        settings["hotkeys"] = self._bindings
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        logger.debug("Settings saved to %s", SETTINGS_FILE)

    def _load_settings(self) -> None:
        settings = self._load_all_settings()
        saved = settings.get("hotkeys", {})
        for action in self._bindings:
            if action in saved:
                self._bindings[action] = saved[action]
        if saved:
            logger.info("Hotkey settings loaded: %s", self._bindings)

    @staticmethod
    def _load_all_settings() -> dict:
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}
