"""
Settings dialog – modal window for editing hotkey bindings.

Each hotkey has a "Press any key…" capture button.
When clicked, it starts listening for the next physical key press
and assigns it as the new hotkey.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional

import customtkinter as ctk

from core.hotkey_manager import HotkeyManager
from ui import theme as T


# Friendly labels for each action
_ACTION_LABELS = {
    HotkeyManager.ACTION_TOGGLE_RECORD: "Toggle Recording",
    HotkeyManager.ACTION_EXECUTE: "Execute Bind",
    HotkeyManager.ACTION_EMERGENCY_STOP: "Emergency Stop",
}


class SettingsDialog(ctk.CTkToplevel):
    """Modal dialog for configuring hotkey bindings."""

    def __init__(
        self,
        master,
        hotkey_manager: HotkeyManager,
        on_close: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self._hk = hotkey_manager
        self._on_close = on_close
        self._capture_buttons: Dict[str, ctk.CTkButton] = {}
        self._currently_capturing: Optional[str] = None

        # -- Window setup --
        self.title("Hotkey Settings")
        self.geometry("420x320")
        self.resizable(False, False)
        self.configure(fg_color=T.BG_DARK)
        self.transient(master)
        self.grab_set()

        # Centre on parent
        self.update_idletasks()
        pw = master.winfo_width()
        ph = master.winfo_height()
        px = master.winfo_x()
        py = master.winfo_y()
        w, h = 420, 320
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # -- Title --
        ctk.CTkLabel(
            self, text="⚙  Hotkey Configuration",
            font=(T.FONT_FAMILY, T.FONT_SIZE_XL, "bold"),
            text_color=T.TEXT_PRIMARY,
        ).pack(pady=(T.PADDING_LG, T.PADDING))

        ctk.CTkLabel(
            self,
            text="Click the button then press any key to assign it.",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SM),
            text_color=T.TEXT_MUTED,
        ).pack(pady=(0, T.PADDING))

        # -- Hotkey rows --
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=T.PADDING_LG)

        bindings = self._hk.bindings
        for i, (action, key_name) in enumerate(bindings.items()):
            label_text = _ACTION_LABELS.get(action, action)

            row = ctk.CTkFrame(container, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS_SM)
            row.pack(fill="x", pady=4)
            row.columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row, text=label_text,
                font=(T.FONT_FAMILY, T.FONT_SIZE_MD),
                text_color=T.TEXT_PRIMARY,
                anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=T.PADDING, pady=T.PADDING_SM)

            btn = ctk.CTkButton(
                row,
                text=key_name.upper(),
                width=120, height=32,
                font=(T.FONT_FAMILY, T.FONT_SIZE_MD, "bold"),
                fg_color=T.ACCENT_PRIMARY,
                hover_color=T.BTN_DEFAULT_HOVER,
                corner_radius=T.CORNER_RADIUS_SM,
                command=lambda a=action: self._start_capture(a),
            )
            btn.grid(row=0, column=1, sticky="e", padx=T.PADDING, pady=T.PADDING_SM)
            self._capture_buttons[action] = btn

        # -- Close button --
        ctk.CTkButton(
            self, text="Done", width=120, height=36,
            font=(T.FONT_FAMILY, T.FONT_SIZE_MD, "bold"),
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.BTN_DEFAULT_HOVER,
            corner_radius=T.CORNER_RADIUS,
            command=self._close,
        ).pack(pady=T.PADDING_LG)

        self.protocol("WM_DELETE_WINDOW", self._close)

    # -----------------------------------------------------------------------
    # Key Capture
    # -----------------------------------------------------------------------

    def _start_capture(self, action: str) -> None:
        """Put one button into 'listening' mode."""
        # Cancel previous capture if any
        if self._currently_capturing:
            self._reset_button(self._currently_capturing)

        self._currently_capturing = action
        btn = self._capture_buttons[action]
        btn.configure(
            text="Press any key…",
            fg_color=T.STATUS_RECORDING,
            hover_color=T.STATUS_RECORDING,
        )

        # Tell the HotkeyManager to capture the next key
        self._hk.capture_next_key(action, callback=self._on_key_captured)

    def _on_key_captured(self, key_name: str) -> None:
        """Called from the HotkeyManager when a key is captured."""
        action = self._currently_capturing
        if not action:
            return
        self._currently_capturing = None

        # Update button text on the UI thread
        self.after(0, lambda: self._update_button(action, key_name))

    def _update_button(self, action: str, key_name: str) -> None:
        btn = self._capture_buttons.get(action)
        if btn:
            btn.configure(
                text=key_name.upper(),
                fg_color=T.ACCENT_PRIMARY,
                hover_color=T.BTN_DEFAULT_HOVER,
            )

    def _reset_button(self, action: str) -> None:
        btn = self._capture_buttons.get(action)
        key = self._hk.get_binding(action)
        if btn:
            btn.configure(
                text=key.upper(),
                fg_color=T.ACCENT_PRIMARY,
                hover_color=T.BTN_DEFAULT_HOVER,
            )
        self._hk.cancel_capture()

    def _close(self) -> None:
        if self._currently_capturing:
            self._hk.cancel_capture()
        self.grab_release()
        self.destroy()
        if self._on_close:
            self._on_close()
