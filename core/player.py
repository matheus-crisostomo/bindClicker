"""
Player – replays a Script by simulating mouse clicks and key events.

Runs in a background thread so the UI remains responsive.
Supports speed multiplier, repeat count, random delay jitter,
and an emergency stop flag.
"""

from __future__ import annotations

import random
import threading
import time
from datetime import datetime
from typing import Callable, Optional

from pynput import keyboard as kb_ctrl
from pynput import mouse as ms_ctrl
from pynput.mouse import Button as MouseButton

from core.models import Action, ExecutionRecord, Script
from utils.logger import get_logger

logger = get_logger("core.player")

_BUTTON_MAP = {
    "left": MouseButton.left,
    "right": MouseButton.right,
    "middle": MouseButton.middle,
}


class Player:
    """Replays a Script with configurable speed, repeats and jitter."""

    def __init__(
        self,
        on_progress: Optional[Callable[[int, int, int, int], None]] = None,
        on_finished: Optional[Callable[[ExecutionRecord], None]] = None,
    ):
        """
        Args:
            on_progress: callback(current_repeat, total_repeats, current_action, total_actions)
            on_finished: callback(execution_record)
        """
        self._mouse = ms_ctrl.Controller()
        self._keyboard = kb_ctrl.Controller()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._on_progress = on_progress
        self._on_finished = on_finished

    # -- Public API ----------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, script: Script) -> None:
        """Begin playback of *script* in a background thread."""
        if self._running:
            logger.warning("Player already running – ignoring start()")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, args=(script,), daemon=True
        )
        self._thread.start()
        logger.info("Playback started: '%s'", script.name)

    def stop(self) -> None:
        """Request an immediate stop (emergency stop)."""
        if not self._running:
            return
        self._stop_event.set()
        logger.info("Playback stop requested")

    def wait(self, timeout: float | None = None) -> None:
        """Block until playback finishes."""
        if self._thread:
            self._thread.join(timeout=timeout)

    # -- Internal playback loop ---------------------------------------------

    def _run(self, script: Script) -> None:
        self._running = True
        record = ExecutionRecord(script_name=script.name)
        start_time = time.perf_counter()
        total_actions_executed = 0
        repeat_count = script.repeat_count  # 0 = infinite
        total_repeats = repeat_count if repeat_count > 0 else -1

        try:
            iteration = 0
            while True:
                if self._stop_event.is_set():
                    break

                iteration += 1
                if repeat_count > 0 and iteration > repeat_count:
                    break

                for idx, action in enumerate(script.actions):
                    if self._stop_event.is_set():
                        break

                    # Report progress
                    if self._on_progress:
                        try:
                            self._on_progress(
                                iteration, total_repeats,
                                idx + 1, len(script.actions),
                            )
                        except Exception:
                            pass

                    self._execute_action(action, script)
                    total_actions_executed += 1

            record.status = "stopped" if self._stop_event.is_set() else "completed"

        except Exception as exc:
            logger.exception("Playback error: %s", exc)
            record.status = "error"

        finally:
            elapsed = (time.perf_counter() - start_time) * 1000.0
            record.ended_at = datetime.now().isoformat()
            record.duration_ms = round(elapsed, 2)
            record.actions_executed = total_actions_executed
            self._running = False

            logger.info(
                "Playback finished: status=%s, actions=%d, duration=%.0f ms",
                record.status, total_actions_executed, elapsed,
            )

            if self._on_finished:
                try:
                    self._on_finished(record)
                except Exception:
                    logger.exception("Error in on_finished callback")

    def _execute_action(self, action: Action, script: Script) -> None:
        speed = script.speed_multiplier
        jitter = script.random_delay_ms

        # --- delay BEFORE ---
        if action.delay_before > 0:
            self._sleep(action.delay_before, speed, jitter)

        # --- execute the action ---
        if action.action_type == "click":
            self._do_click(action)
        elif action.action_type == "key_press":
            self._do_key_press(action)
        elif action.action_type == "key_release":
            self._do_key_release(action)

        # --- delay AFTER ---
        if action.delay_after > 0:
            self._sleep(action.delay_after, speed, jitter)

    def _sleep(self, ms: float, speed: float, jitter_ms: int) -> None:
        """Sleep for *ms* adjusted by speed and jitter, interruptible."""
        delay = ms / speed
        if jitter_ms > 0:
            delay += random.uniform(-jitter_ms, jitter_ms)
        delay = max(0, delay)

        # Sleep in small increments so we can respond to stop quickly
        end = time.perf_counter() + delay / 1000.0
        while time.perf_counter() < end:
            if self._stop_event.is_set():
                return
            remaining = end - time.perf_counter()
            time.sleep(min(0.01, remaining))  # 10 ms increments

    # -- Action executors ---------------------------------------------------

    def _do_click(self, action: Action) -> None:
        button = _BUTTON_MAP.get(action.button or "left", MouseButton.left)
        if action.x is not None and action.y is not None:
            self._mouse.position = (action.x, action.y)
        if action.pressed:
            self._mouse.press(button)
        else:
            self._mouse.release(button)
        logger.debug("Click %s %s at (%s, %s)",
                      action.button, "down" if action.pressed else "up",
                      action.x, action.y)

    def _do_key_press(self, action: Action) -> None:
        key = self._resolve_key(action.button)
        if key:
            self._keyboard.press(key)
            logger.debug("Key press: %s", action.button)

    def _do_key_release(self, action: Action) -> None:
        key = self._resolve_key(action.button)
        if key:
            self._keyboard.release(key)
            logger.debug("Key release: %s", action.button)

    def _resolve_key(self, name: str | None):
        """Convert a key name string back to a pynput Key or KeyCode."""
        if not name:
            return None
        # Try special keys first (shift, ctrl, etc.)
        try:
            return kb_ctrl.Key[name]
        except (KeyError, ValueError):
            pass
        # Single character
        if len(name) == 1:
            return kb_ctrl.KeyCode.from_char(name)
        return None
