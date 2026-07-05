"""
Recorder – captures mouse clicks and keyboard events.

Uses pynput listeners running in background threads.
Only records click events (press + release) and key events.
Mouse movement is NOT recorded per user preference.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, List, Optional

from pynput import keyboard, mouse

from core.models import Action
from utils.logger import get_logger

logger = get_logger("core.recorder")


class Recorder:
    """Records mouse clicks and keyboard events into a list of Actions."""

    def __init__(self, on_action_recorded: Optional[Callable[[Action], None]] = None):
        self._actions: List[Action] = []
        self._recording = False
        self._lock = threading.Lock()
        self._last_time: float = 0.0
        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._on_action_recorded = on_action_recorded

        # Keys to ignore during recording (hotkeys themselves)
        self._ignored_keys: set[str] = set()

    # -- Public API ----------------------------------------------------------

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def actions(self) -> List[Action]:
        with self._lock:
            return list(self._actions)

    @property
    def action_count(self) -> int:
        with self._lock:
            return len(self._actions)

    def set_ignored_keys(self, keys: set[str]) -> None:
        """Set keys that should not be recorded (e.g. hotkey keys)."""
        self._ignored_keys = {k.lower() for k in keys}

    def start(self) -> None:
        """Begin recording mouse clicks and keyboard events."""
        if self._recording:
            logger.warning("Recorder already active – ignoring start()")
            return

        with self._lock:
            self._actions.clear()
        self._last_time = time.perf_counter()
        self._recording = True

        self._mouse_listener = mouse.Listener(on_click=self._on_click)
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._mouse_listener.start()
        self._keyboard_listener.start()

        logger.info("Recording started")

    def stop(self) -> List[Action]:
        """Stop recording and return the captured actions."""
        if not self._recording:
            logger.warning("Recorder not active – ignoring stop()")
            return []

        self._recording = False

        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

        actions = self.actions
        logger.info("Recording stopped – %d actions captured", len(actions))
        return actions

    def clear(self) -> None:
        """Discard all recorded actions."""
        with self._lock:
            self._actions.clear()
        logger.debug("Recorded actions cleared")

    # -- Internal callbacks --------------------------------------------------

    def _elapsed_ms(self) -> float:
        """Return ms since last recorded action and reset the timer."""
        now = time.perf_counter()
        elapsed = (now - self._last_time) * 1000.0
        self._last_time = now
        return round(elapsed, 2)

    def _append(self, action: Action) -> None:
        with self._lock:
            self._actions.append(action)
        if self._on_action_recorded:
            try:
                self._on_action_recorded(action)
            except Exception:
                logger.exception("Error in on_action_recorded callback")
        logger.debug("Recorded: %s", action)

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if not self._recording:
            return

        btn_name = button.name  # "left", "right", "middle"
        delay = self._elapsed_ms()

        action = Action(
            action_type="click",
            button=btn_name,
            x=int(x),
            y=int(y),
            delay_before=delay if pressed else 0,
            delay_after=0 if pressed else delay,
            pressed=pressed,
        )
        self._append(action)

    def _key_name(self, key) -> str:
        """Extract a readable name from a pynput key object."""
        if hasattr(key, "char") and key.char is not None:
            return key.char
        if hasattr(key, "name"):
            return key.name
        return str(key)

    def _on_key_press(self, key) -> None:
        if not self._recording:
            return

        name = self._key_name(key)
        if name.lower() in self._ignored_keys:
            return

        delay = self._elapsed_ms()
        action = Action(
            action_type="key_press",
            button=name,
            delay_before=delay,
            pressed=True,
        )
        self._append(action)

    def _on_key_release(self, key) -> None:
        if not self._recording:
            return

        name = self._key_name(key)
        if name.lower() in self._ignored_keys:
            return

        delay = self._elapsed_ms()
        action = Action(
            action_type="key_release",
            button=name,
            delay_after=delay,
            pressed=False,
        )
        self._append(action)
